#!/usr/bin/env python3
import os
import json
import glob
import argparse

try:
    import pandas as pd
except Exception:
    pd = None


def load_parquet_or_csv(path: str):
    if pd is None:
        import csv
        rows = []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                rows.append({k: float(v) if isinstance(v, str) and v.replace('.','',1).isdigit() else v for k, v in row.items()})
        return rows
    return pd.read_parquet(path)


def compute(run_dir: str) -> dict:
    out: dict = {"run_dir": run_dir}

    # deviation stats (needs pose + setpoint parquet)
    pose_p = os.path.join(run_dir, "local_pose.parquet")
    setp_p = os.path.join(run_dir, "setpoint_local.parquet")
    if os.path.exists(pose_p) and os.path.exists(setp_p) and pd is not None:
        pose = pd.read_parquet(pose_p)
        setp = pd.read_parquet(setp_p)
        # align by nearest timestamp (simple)
        pose = pose.sort_values("t_ns")
        setp = setp.sort_values("t_ns")
        setp_idx = setp.set_index("t_ns")
        # reindex setpoints at pose times by nearest
        nearest = setp_idx.reindex(pose["t_ns"], method="nearest", tolerance=5_000_000)  # 5 ms
        merged = pose.join(nearest, rsuffix="_sp")
        dx = merged["x"] - merged["x_sp"]
        dy = merged["y"] - merged["y_sp"]
        dz = merged["z"] - merged["z_sp"]
        dev = (dx * dx + dy * dy + dz * dz) ** 0.5
        out["deviation_m_mean"] = float(dev.mean())
        out["deviation_m_p95"] = float(dev.quantile(0.95))
        out["deviation_m_max"] = float(dev.max())

    # state timeline (armed time proportion)
    state_p = os.path.join(run_dir, "mavros_state.parquet")
    if os.path.exists(state_p) and pd is not None:
        st = pd.read_parquet(state_p).sort_values("t_ns")
        st["dt_s"] = (st["t_ns"].shift(-1) - st["t_ns"]) / 1e9
        total = float(st["dt_s"].fillna(0).sum())
        armed_time = float(st.loc[st["armed"] == True, "dt_s"].fillna(0).sum())
        out["armed_time_s"] = armed_time
        out["run_time_s"] = total
        out["armed_ratio"] = armed_time / total if total > 0 else 0.0

    # events count
    ev_p = os.path.join(run_dir, "events.jsonl")
    if os.path.exists(ev_p):
        counts = {}
        with open(ev_p) as f:
            for line in f:
                try:
                    ev = json.loads(line)
                    counts[ev.get("event","unknown")] = counts.get(ev.get("event","unknown"), 0) + 1
                except Exception:
                    pass
        out["events"] = counts

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_root", nargs="?", default=os.path.expanduser("~/ros2_ws/runs"))
    args = ap.parse_args()

    run_dirs = sorted([d for d in glob.glob(os.path.join(args.runs_root, "*")) if os.path.isdir(d)])
    results = [compute(d) for d in run_dirs[-5:]]  # last 5 runs
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()


