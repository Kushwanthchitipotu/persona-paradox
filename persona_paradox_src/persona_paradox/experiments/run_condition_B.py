"""
experiments/run_condition_B.py
------------------------------
Condition B: rules only, no persona.
Isolates the effect of rule injection without persona conditioning.
"""

from src.evaluate import run_audit

if __name__ == "__main__":
    run_audit(
        conditions={"B": {"use_persona": False, "use_rules": True}},
        output_path="results/audit_condition_B.csv",
    )
