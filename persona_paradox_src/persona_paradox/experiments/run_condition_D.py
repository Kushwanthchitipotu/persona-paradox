"""
experiments/run_condition_D.py
------------------------------
Condition D: no persona, no rules — raw LLM baseline.
Shows pre-training bias before any prompt engineering is applied.
"""

from src.evaluate import run_audit

if __name__ == "__main__":
    run_audit(
        conditions={"D": {"use_persona": False, "use_rules": False}},
        output_path="results/audit_condition_D.csv",
    )
