#!/bin/bash
# run_all.sh
# ----------
# Run all four ablation conditions sequentially.
# Model is reloaded for each condition — if GPU memory allows,
# edit evaluate.py to accept a shared model instance instead.
#
# Usage: bash experiments/run_all.sh

set -e   # exit immediately on any error

echo "========================================"
echo "Condition A: persona + rules"
echo "========================================"
python experiments/run_condition_A.py

echo "========================================"
echo "Condition B: rules only"
echo "========================================"
python experiments/run_condition_B.py

echo "========================================"
echo "Condition C: persona only"
echo "========================================"
python experiments/run_condition_C.py

echo "========================================"
echo "Condition D: raw LLM baseline"
echo "========================================"
python experiments/run_condition_D.py

echo ""
echo "All conditions complete. Results in results/"
ls -lh results/
