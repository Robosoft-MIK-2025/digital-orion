#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$PROJECT_ROOT"

usage() {
  cat <<EOF
Usage: doron <command> [args]

Commands:
  build               Build Docker image
  up                  Start container (terminal)
  shell               Enter container shell
  record [sec]        Record all ROS2 topics for N seconds
  ulog-latest [path]  Convert latest QGC .ulg to CSV (runs/<ts>/)
  run-zip-latest      Zip latest runs/<ts> (falls back to tar.gz)
  metrics             Compute metrics for last run (placeholder)
  docs                Build Sphinx docs
  open-docs           Open docs in browser (Linux)
  stop                Stop container
  clean               Clean build artifacts
EOF
}

latest_run_dir() {
  local latest
  latest=$(find "$PROJECT_ROOT/runs" -maxdepth 1 -mindepth 1 -type d -printf '%T@\t%p\n' 2>/dev/null | sort -nr | awk 'NR==1{print $2}')
  [[ -n "${latest:-}" ]] && { echo "$latest"; return 0; }
  return 1
}

# Resolve latest QGC log (.ulg). Argument may be a file or directory.
resolve_latest_ulog() {
  local input="${1:-}"
  if [[ -n "$input" && -f "$input" && "$input" == *.ulg ]]; then
    echo "$input"; return 0
  fi
  if [[ -n "$input" && -d "$input" ]]; then
    local latest
    latest=$(find "$input" -type f -name '*.ulg' -printf '%T@\t%p\n' 2>/dev/null | sort -nr | awk 'NR==1{print $2}')
    [[ -n "${latest:-}" ]] && { echo "$latest"; return 0; }
  fi
  if [[ -n "${QGC_LOGS_DIR:-}" ]]; then
    if [[ -f "${QGC_LOGS_DIR}" && "${QGC_LOGS_DIR}" == *.ulg ]]; then
      echo "${QGC_LOGS_DIR}"; return 0
    fi
    if [[ -d "${QGC_LOGS_DIR}" ]]; then
      local latest
      latest=$(find "${QGC_LOGS_DIR}" -type f -name '*.ulg' -printf '%T@\t%p\n' 2>/dev/null | sort -nr | awk 'NR==1{print $2}')
      [[ -n "${latest:-}" ]] && { echo "$latest"; return 0; }
    fi
  fi
  local candidates=(
    "$PROJECT_ROOT/qgc_logs"
    "$HOME/qgc_logs"
    "$HOME/QGroundControl/Logs"
    "$HOME/ros2_ws/runs"
  )
  local latest
  for d in "${candidates[@]}"; do
    if [[ -d "$d" ]]; then
      latest=$(find "$d" -type f -name '*.ulg' -printf '%T@\t%p\n' 2>/dev/null | sort -nr | awk 'NR==1{print $2}')
      if [[ -n "${latest:-}" ]]; then
        echo "$latest"; return 0
      fi
    fi
  done
  if command -v wslpath >/dev/null 2>&1; then
    latest=$(find /mnt/c/Users -path '*/QGroundControl/Logs/*' -name '*.ulg' -type f -printf '%T@\t%p\n' 2>/dev/null | sort -nr | awk 'NR==1{print $2}')
    if [[ -n "${latest:-}" ]]; then
      echo "$latest"; return 0
    fi
    latest=$(find /mnt/c/Users -path '*/OneDrive*/Documents/QGroundControl/Logs/*' -name '*.ulg' -type f -printf '%T@\t%p\n' 2>/dev/null | sort -nr | awk 'NR==1{print $2}')
    if [[ -n "${latest:-}" ]]; then
      echo "$latest"; return 0
    fi
  fi
  return 1
}

cmd=${1:-help}
shift || true

case "$cmd" in
  build)
    docker build -t digital-oreon:humble -f docker/Dockerfile .
    ;;
  up)
    (cd docker && docker compose up -d terminal)
    ;;
  shell)
    (cd docker && docker compose exec terminal bash)
    ;;
  record)
    secs=${1:-30}
    (cd docker && docker compose exec -T terminal bash -lc 'source /opt/ros/humble/setup.bash && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export RMW_CYCLONEDDS_USE_SHM=0 && ros2 bag record -a -o runs/sample & pid=$!; sleep '"$secs"'; kill -INT $pid; wait $pid || true')
    echo "Recorded for ${secs}s into runs/sample"
    ;;
  ulog-latest)
    pref=${1:-}
    latest_ulog=$(resolve_latest_ulog "$pref" || true)
    if [[ -z "${latest_ulog:-}" ]]; then
      echo "No .ulg found. Provide a file/dir or set QGC_LOGS_DIR.\nExamples:\n  ./scripts/doron.sh ulog-latest ~/QGroundControl/Logs\n  ./scripts/doron.sh ulog-latest /mnt/c/Users/<you>/Documents/QGroundControl/Logs\n  ./scripts/doron.sh ulog-latest /path/to/log.ulg" >&2
      exit 1
    fi
    ts=$(date +%Y%m%d_%H%M%S)
    outdir="$PROJECT_ROOT/runs/$ts"
    mkdir -p "$outdir"
    echo "Converting: $latest_ulog -> $outdir"
    python3 scripts/ulog_to_ml_csv.py "$latest_ulog" --out "$outdir"
    echo "Done. Output: $outdir"
    ;;
  run-zip-latest)
    d=$(latest_run_dir || true)
    if [[ -z "${d:-}" ]]; then
      echo "No runs found in runs/." >&2; exit 1
    fi
    if command -v zip >/dev/null 2>&1; then
      zipfile="${d}.zip"
      (cd "$(dirname "$d")" && zip -r "$(basename "$zipfile")" "$(basename "$d")" >/dev/null)
      echo "Created: $zipfile"
    elif command -v tar >/dev/null 2>&1; then
      tarfile="${d}.tar.gz"
      (cd "$(dirname "$d")" && tar -czf "$(basename "$tarfile")" "$(basename "$d")")
      echo "Created: $tarfile"
    else
      echo "Neither zip nor tar found. Install zip: sudo apt-get install -y zip" >&2
      exit 1
    fi
    ;;
  metrics)
    (cd docker && docker compose exec -T terminal bash -lc '~/ros2_ws/../scripts/compute_metrics.py || true')
    ;;
  docs)
    python3 -m venv .venv && source .venv/bin/activate && \
      pip install -r docs/requirements-docs.txt && \
      sphinx-build -b html docs docs/_build/html
    ;;
  open-docs)
    xdg-open docs/_build/html/index.html || true
    ;;
  stop)
    (cd docker && docker compose down || true)
    ;;
  clean)
    rm -rf docs/_build || true
    ;;
  *)
    usage
    ;;
esac


