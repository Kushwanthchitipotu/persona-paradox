"""
evaluate.py
-----------
Main audit loop: runs all 70 scenarios × 4 agents × 4 conditions = 1,120 evaluations
and saves results to results/audit_results.csv.

Usage
-----
    python -m src.evaluate
    # or from experiments/:
    python experiments/run_condition_A.py
"""

import os
import json
import pandas as pd

from src.model        import load_model
from src.agents       import AGENTS
from src.prompt_builder import CONDITIONS
from src.retrieval    import get_rules_data, DATA_DIR
from src.format_rules import format_rules
from src.inference    import run_agent
from src.parser       import parse_output

SCENARIOS_PATH = os.path.join(DATA_DIR, "scenarios_new.json")
RESULTS_DIR    = os.path.join(os.path.dirname(__file__), "..", "results")
OUTPUT_CSV     = os.path.join(RESULTS_DIR, "audit_results.csv")


def run_audit(
    conditions: dict = None,
    agents: list = None,
    output_path: str = OUTPUT_CSV,
) -> pd.DataFrame:
    """
    Run the full audit loop.

    Parameters
    ----------
    conditions  : Subset of CONDITIONS to run. Defaults to all four (A, B, C, D).
    agents      : Subset of agent names to run. Defaults to all four.
    output_path : Where to save the results CSV.

    Returns
    -------
    pd.DataFrame of all evaluation records.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if conditions is None:
        conditions = CONDITIONS
    if agents is None:
        agents = list(AGENTS.keys())

    # Load model once — expensive, do it here not inside the loop
    model, tokenizer = load_model()
    rules_data = get_rules_data()

    with open(SCENARIOS_PATH, "r") as f:
        scenarios_data = json.load(f)

    total_runs = len(scenarios_data) * len(agents) * len(conditions)
    print(
        f"\nStarting audit: {len(scenarios_data)} scenarios × "
        f"{len(agents)} agents × {len(conditions)} conditions "
        f"= {total_runs} total runs\n"
    )

    records = []

    for item in scenarios_data:
        s_id   = item["id"]
        s_type = item["metadata"]["type"]
        text   = item["data"]["text"]
        query  = item["data"]["query"]

        target_rules    = item["audit"]["target"]           # e.g. ['R02', 'R21', 'R16']
        formatted_rules = format_rules(target_rules, rules_data)
        full_scenario   = f"{text}\n\nUser Question:\n{query}"

        print(f"Processing: {s_id} ({s_type})")

        for agent_name in agents:
            for condition_label, flags in conditions.items():

                # Conditions B and D have no persona — agent_name ignored inside build_prompt
                a_name  = agent_name if flags["use_persona"] else None
                f_rules = formatted_rules if flags["use_rules"] else ""

                try:
                    raw_output = run_agent(
                        a_name,
                        full_scenario,
                        f_rules,
                        model,
                        tokenizer,
                        **flags,
                    )
                    parsed = parse_output(raw_output)

                    print(
                        f"  [{condition_label}] {agent_name:12s} | "
                        f"{parsed.get('decision', 'N/A'):7s} | "
                        f"Score: {parsed.get('score', 'N/A')}"
                    )

                    records.append({
                        "ID":          s_id,
                        "Type":        s_type,
                        "Condition":   condition_label,
                        "Agent":       agent_name,
                        "Decision":    parsed.get("decision", "N/A"),
                        "Score":       parsed.get("score",    "N/A"),
                        "Rules":       ", ".join(target_rules),
                        "Reasoning":   parsed.get("reasoning", "N/A"),
                        "Raw_Response": raw_output,
                    })

                except Exception as e:
                    print(f"  ERROR — {s_id} | {agent_name} | Condition {condition_label}: {e}")
                    records.append({
                        "ID":          s_id,
                        "Type":        s_type,
                        "Condition":   condition_label,
                        "Agent":       agent_name,
                        "Decision":    "ERROR",
                        "Score":       None,
                        "Rules":       ", ".join(target_rules),
                        "Reasoning":   str(e),
                        "Raw_Response": "",
                    })

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)

    print(f"\nDone. {len(records)} records saved to {output_path}")
    print(f"Columns: {list(df.columns)}")
    return df


if __name__ == "__main__":
    run_audit()
