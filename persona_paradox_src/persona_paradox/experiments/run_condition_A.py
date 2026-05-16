"""
experiments/run_condition_A.py
------------------------------
Condition A: persona + rules (full production system).
Runs all 4 agents across all 70 scenarios.
"""

from src.evaluate import run_audit

if __name__ == "__main__":
    run_audit(
        conditions={"A": {"use_persona": True, "use_rules": True}},
        output_path="results/audit_condition_A.csv",
    )
