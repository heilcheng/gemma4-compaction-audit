#!/bin/bash
# Wait for each arm's modal run to exit, then relaunch it once so the resumable
# runner redoes any errored tasks. Usage: scripts/finish_seed.sh <seed> <cap> <arm>...
set -u
cd "$(dirname "$0")/.."
SEED=$1; CAP=$2; shift 2
for ARM in "$@"; do
  (
    OUT=runs/main_s${SEED}_${ARM}.jsonl
    while pgrep -f "modal run modal/run.py.*--arms ${ARM} --seed ${SEED} --cap ${CAP} " >/dev/null; do sleep 120; done
    echo "$(date -u) ${ARM}: first pass exited, relaunching for errored tasks"
    PYTHONPATH=src modal --profile coglix-labs run modal/run.py --tasks manifests/heldout.txt \
      --arms "${ARM}" --seed "${SEED}" --cap "${CAP}" --out "${OUT}" >> "runs/main_s${SEED}_${ARM}.log" 2>&1
    echo "$(date -u) ${ARM}: done=$(grep -c . "$OUT") err=$(grep -c '"error": "' "$OUT")"
  ) &
done
wait
echo "$(date -u) all arms finished"
