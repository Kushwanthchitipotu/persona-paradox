"""
experiments/run_condition_C.py
------------------------------
Condition C: persona only, no rules.
Isolates the effect of persona conditioning without rule injection.
This is the condition that reveals ghost-rule hallucination.
"""

from src.evaluate import run_audit

if __name__ == "__main__":
    run_audit(
        conditions={"C": {"use_persona": True, "use_rules": False}},
        output_path="results/audit_condition_C.csv",
    )
