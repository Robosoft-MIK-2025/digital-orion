#!/usr/bin/env python3
import argparse
import glob
import math
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

try:
    import pandas as pd
except Exception as e:
    print("pandas is required. Install inside container: pip3 install pandas", file=sys.stderr)
    raise

# Optional: pyulog for direct dataset introspection
try:
    from pyulog import ULog  # type: ignore
except Exception:
    ULog = None


def quat_to_euler(w: float, x: float, y: float, z: float):
    # roll (x-axis rotation)
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)
    # pitch (y-axis rotation)
    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch = math.asin(t2)
    # yaw (z-axis rotation)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)
    return roll, pitch, yaw


def run_ulog2csv(ulog_path: str, out_dir: str):
    """Run ulog2csv to extract per-topic CSVs into out_dir/csv_raw."""
    raw_dir = os.path.join(out_dir, "csv_raw")
    os.makedirs(raw_dir, exist_ok=True)
    try:
        subprocess.run(["ulog2csv", ulog_path, "-o", raw_dir], check=True)
    except FileNotFoundError:
        print("ulog2csv not found. Install pyulog: pip3 install pyulog", file=sys.stderr)
        raise
    return raw_dir


def run_ulog2csv_for_topics(ulog_path: str, out_dir: str, topics: list[str]):
    """Run ulog2csv exporting only specific topics into out_dir/csv_raw."""
    raw_dir = os.path.join(out_dir, "csv_raw")
    os.makedirs(raw_dir, exist_ok=True)
    try:
        cmd = ["ulog2csv", ulog_path, "-o", raw_dir]
        for t in topics:
            cmd.extend(["-m", t])
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("ulog2csv not found. Install pyulog: pip3 install pyulog", file=sys.stderr)
        raise
    return raw_dir


def list_datasets_in_ulog(ulog_path: str) -> list[str]:
    if ULog is None:
        return []
    try:
        u = ULog(ulog_path, None, disable_str_exceptions=True)
        return sorted(set(d.name for d in u.data_list))
    except Exception:
        return []


def load_dataset_df(ulog_path: str, name_prefixes: list[str]) -> Optional[pd.DataFrame]:
    """Return a pandas DataFrame for the first matching dataset name prefix."""
    if ULog is None:
        return None
    try:
        u = ULog(ulog_path, None, disable_str_exceptions=True)
        # pick first dataset that equals or startswith prefix + '_'
        def match(ds_name: str) -> bool:
            return any(ds_name == p or ds_name.startswith(p + "_") for p in name_prefixes)
        ds = next((d for d in u.data_list if match(d.name)), None)
        if ds is None:
            return None
        # Convert to DataFrame
        data_dict = {k: v for k, v in ds.data.items()}
        try:
            df = pd.DataFrame(data_dict)
        except Exception:
            # Fallback: align by length of the longest array
            max_len = max(len(v) for v in data_dict.values()) if data_dict else 0
            padded = {}
            for k, v in data_dict.items():
                if len(v) == max_len:
                    padded[k] = v
            df = pd.DataFrame(padded)
        # Normalize timestamp column name
        if "timestamp" not in df.columns:
            if "time" in df.columns:
                df.rename(columns={"time": "timestamp"}, inplace=True)
        return df
    except Exception:
        return None


def pick_one(glob_pat: str) -> Optional[str]:
    files = sorted(glob.glob(glob_pat, recursive=True))
    return files[0] if files else None

def pick_first_of(patterns) -> Optional[str]:
    for pat in patterns:
        p = pick_one(pat)
        if p:
            return p
    return None


def main():
    ap = argparse.ArgumentParser(description="Convert PX4 .ulg to ML-friendly CSV")
    ap.add_argument("ulog", help="Path to input .ulg file")
    ap.add_argument("--out", default=os.path.expanduser("~/ros2_ws/runs"), help="Output directory root")
    ap.add_argument("--vlp", default=None, help="Override path to local position CSV (e.g., estimator_local_position_*.csv)")
    ap.add_argument("--att", default=None, help="Override path to attitude CSV (e.g., estimator_attitude_*.csv)")
    args = ap.parse_args()

    ulog_path = os.path.abspath(args.ulog)
    run_root = os.path.join(os.path.abspath(args.out), os.path.splitext(os.path.basename(ulog_path))[0])
    os.makedirs(run_root, exist_ok=True)

    # 1) Extract per-topic CSVs unless overrides provided
    raw_dir = os.path.join(run_root, "csv_raw")
    if not (args.vlp and args.att):
        raw_dir = run_ulog2csv(ulog_path, run_root)

    # 2) Load key topics
    vlp_path = args.vlp or pick_first_of([
        os.path.join(raw_dir, "vehicle_local_position*.csv"),
        os.path.join(raw_dir, "vehicle_local_position_*0*.csv"),
        os.path.join(raw_dir, "estimator_local_position*.csv"),
        os.path.join(raw_dir, "estimator_local_position_*0*.csv"),
    ])
    att_path = args.att or pick_first_of([
        os.path.join(raw_dir, "vehicle_attitude*.csv"),
        os.path.join(raw_dir, "vehicle_attitude_*0*.csv"),
        os.path.join(raw_dir, "estimator_attitude*.csv"),
        os.path.join(raw_dir, "estimator_attitude_*0*.csv"),
    ])
    # Keep a dedicated odometry candidate for robust fallback
    odom_path = pick_first_of([
        os.path.join(raw_dir, "vehicle_odometry*.csv"),
    ])
    mr_path = pick_first_of([
        os.path.join(raw_dir, "mission_result*.csv"),
        os.path.join(raw_dir, "navigator_status*.csv"),
    ])

    # Fallback: search recursively under output root if not found
    if not vlp_path:
        vlp_path = pick_first_of([
            os.path.join(run_root, "**/vehicle_local_position*.csv"),
            os.path.join(run_root, "**/vehicle_local_position_*0*.csv"),
            os.path.join(run_root, "**/estimator_local_position*.csv"),
            os.path.join(run_root, "**/estimator_local_position_*0*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/vehicle_local_position*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/vehicle_local_position_*0*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/estimator_local_position*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/estimator_local_position_*0*.csv"),
            os.path.join(os.path.abspath(args.out), "**/vehicle_local_position*.csv"),
            os.path.join(os.path.abspath(args.out), "**/vehicle_local_position_*0*.csv"),
            os.path.join(os.path.abspath(args.out), "**/estimator_local_position*.csv"),
            os.path.join(os.path.abspath(args.out), "**/estimator_local_position_*0*.csv"),
        ])
    if not att_path:
        att_path = pick_first_of([
            os.path.join(run_root, "**/vehicle_attitude*.csv"),
            os.path.join(run_root, "**/vehicle_attitude_*0*.csv"),
            os.path.join(run_root, "**/estimator_attitude*.csv"),
            os.path.join(run_root, "**/estimator_attitude_*0*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/vehicle_attitude*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/vehicle_attitude_*0*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/estimator_attitude*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/estimator_attitude_*0*.csv"),
            os.path.join(os.path.abspath(args.out), "**/vehicle_attitude*.csv"),
            os.path.join(os.path.abspath(args.out), "**/vehicle_attitude_*0*.csv"),
            os.path.join(os.path.abspath(args.out), "**/estimator_attitude*.csv"),
            os.path.join(os.path.abspath(args.out), "**/estimator_attitude_*0*.csv"),
        ])
    if not odom_path:
        odom_path = pick_first_of([
            os.path.join(run_root, "**/vehicle_odometry*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/vehicle_odometry*.csv"),
            os.path.join(os.path.abspath(args.out), "**/vehicle_odometry*.csv"),
        ])
    if not mr_path:
        mr_path = pick_first_of([
            os.path.join(run_root, "**/mission_result*.csv"),
            os.path.join(run_root, "**/navigator_status*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/mission_result*.csv"),
            os.path.join(os.path.dirname(ulog_path), "**/navigator_status*.csv"),
            os.path.join(os.path.abspath(args.out), "**/mission_result*.csv"),
            os.path.join(os.path.abspath(args.out), "**/navigator_status*.csv"),
        ])

    # If dedicated topics are missing but odometry exists, use odometry for both
    if (not vlp_path or not att_path) and odom_path:
        vlp_path = vlp_path or odom_path
        att_path = att_path or odom_path
    if not vlp_path or not att_path:
        # One more attempt: inspect ULog to see if alternative names exist and re-export specifically
        dataset_names = list_datasets_in_ulog(ulog_path)
        desired_candidates = [
            ["vehicle_local_position", "estimator_local_position", "vehicle_odometry"],
            ["vehicle_attitude", "estimator_attitude", "vehicle_odometry"],
        ]
        selected: list[str] = []
        for group in desired_candidates:
            picked = next((n for n in group if any(n == ds or ds.startswith(n + "_") for ds in dataset_names)), None)
            if picked:
                selected.append(picked)
        if selected:
            raw_dir = run_ulog2csv_for_topics(ulog_path, run_root, selected)
            # Re-search after targeted export
            vlp_path = vlp_path or pick_first_of([
                os.path.join(raw_dir, "vehicle_local_position*.csv"),
                os.path.join(raw_dir, "vehicle_local_position_*0*.csv"),
                os.path.join(raw_dir, "estimator_local_position*.csv"),
                os.path.join(raw_dir, "estimator_local_position_*0*.csv"),
                os.path.join(raw_dir, "vehicle_odometry*.csv"),
            ])
            att_path = att_path or pick_first_of([
                os.path.join(raw_dir, "vehicle_attitude*.csv"),
                os.path.join(raw_dir, "vehicle_attitude_*0*.csv"),
                os.path.join(raw_dir, "estimator_attitude*.csv"),
                os.path.join(raw_dir, "estimator_attitude_*0*.csv"),
                os.path.join(raw_dir, "vehicle_odometry*.csv"),
            ])
        if not vlp_path or not att_path:
            # Print a brief diagnostic to help user, then continue to direct ULog read fallback
            print("Required topics not found. Tried local position (vehicle_local_position/estimator_local_position), attitude (vehicle_attitude/estimator_attitude), and fallback vehicle_odometry.", file=sys.stderr)
            if dataset_names:
                print("Datasets inside ULog:", ", ".join(dataset_names), file=sys.stderr)
            print(f"Looked under: {run_root} and {os.path.dirname(ulog_path)}", file=sys.stderr)

    if vlp_path:
        vlp = pd.read_csv(vlp_path)
    else:
        vlp = load_dataset_df(ulog_path, ["vehicle_local_position", "estimator_local_position", "vehicle_odometry"])
        if vlp is None:
            print("Could not load local position from ULog directly.", file=sys.stderr)
            sys.exit(2)
    if att_path:
        att = pd.read_csv(att_path)
    else:
        att = load_dataset_df(ulog_path, ["vehicle_attitude", "estimator_attitude", "vehicle_odometry"])
        if att is None:
            print("Could not load attitude from ULog directly.", file=sys.stderr)
            sys.exit(2)
    # Normalize timestamp name
    for df in (vlp, att):
        if "timestamp" not in df.columns and "time" in df.columns:
            df.rename(columns={"time": "timestamp"}, inplace=True)

    # Normalize local position columns to x, y, z and velocities to vx, vy, vz
    if "x" not in vlp.columns and all(k in vlp.columns for k in ["position[0]", "position[1]", "position[2]"]):
        vlp.rename(columns={
            "position[0]": "x",
            "position[1]": "y",
            "position[2]": "z",
        }, inplace=True)
    if "vx" not in vlp.columns and all(k in vlp.columns for k in ["velocity[0]", "velocity[1]", "velocity[2]"]):
        vlp.rename(columns={
            "velocity[0]": "vx",
            "velocity[1]": "vy",
            "velocity[2]": "vz",
        }, inplace=True)

    # 3) Compute Euler angles from attitude quaternion
    # Expect columns: q[0], q[1], q[2], q[3]
    if set(["q[0]", "q[1]", "q[2]", "q[3]"]).issubset(att.columns):
        eulers = att[["q[0]", "q[1]", "q[2]", "q[3]"]].apply(
            lambda row: quat_to_euler(row["q[0]"], row["q[1]"], row["q[2]"], row["q[3]"]), axis=1
        )
        att["roll"], att["pitch"], att["yaw"] = zip(*eulers)
    else:
        att["roll"] = att.get("roll", 0.0)
        att["pitch"] = att.get("pitch", 0.0)
        att["yaw"] = att.get("yaw", 0.0)

    # 4) Align by nearest timestamp (tolerance 20 ms)
    att_idx = att.set_index("timestamp").sort_index()
    vlp = vlp.sort_values("timestamp")
    merged = vlp.join(att_idx[["roll", "pitch", "yaw"]], on="timestamp", how="left")

    # 5) Optionally add mission_result (waypoint progress)
    if mr_path:
        mr = pd.read_csv(mr_path)
        if "timestamp" in mr.columns and "seq_current" in mr.columns:
            mr_idx = mr.set_index("timestamp").sort_index()[["seq_current", "seq_total", "mission_finished"]]
            merged = merged.join(mr_idx, on="timestamp", how="left")

    # 6) Select useful columns
    cols = []
    for c in ("timestamp", "x", "y", "z", "vx", "vy", "vz", "roll", "pitch", "yaw", "seq_current", "seq_total", "mission_finished"):
        if c in merged.columns:
            cols.append(c)
    ml = merged[cols].copy()

    # 7) Save ML-friendly CSV
    out_csv = os.path.join(run_root, "flight_data.csv")
    ml.to_csv(out_csv, index=False)
    print(f"Saved: {out_csv}")
    print(f"Raw per-topic CSVs: {raw_dir}")
    
    # Display CSV contents preview
    print("\n" + "="*50)
    print("CSV CONTENTS PREVIEW")
    print("="*50)
    print(f"Shape: {ml.shape}")
    print(f"Columns: {list(ml.columns)}")
    print(f"Data types:\n{ml.dtypes}")
    print(f"\nFirst 5 rows:")
    print(ml.head().to_string())
    print(f"\nLast 5 rows:")
    print(ml.tail().to_string())
    print(f"\nBasic statistics:")
    print(ml.describe().to_string())
    print("="*50)


if __name__ == "__main__":
    main()


