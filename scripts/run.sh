#!/bin/sh
set -eu
task_skill_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -n "${PALETTE_PYTHON:-}" ]; then
    task_python="$PALETTE_PYTHON"
elif [ -x "$task_skill_dir/.venv/bin/python" ]; then
    task_python="$task_skill_dir/.venv/bin/python"
else
    task_python=$(command -v python3 || true)
fi
if [ -z "$task_python" ]; then
    echo "Python 3.10+ is missing; install Python or set PALETTE_PYTHON." >&2
    exit 2
fi
exec "$task_python" "$task_skill_dir/scripts/palette.py" "$@"
