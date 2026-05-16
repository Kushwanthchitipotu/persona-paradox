"""
format_rules.py
---------------
Converts a list of rule IDs into a formatted string for prompt injection.
"""

from src.retrieval import get_rules_data


def format_rules(rule_ids: list, rules_data: list | None = None) -> str:
    """
    Convert rule IDs like ['R02', 'R21', 'R16'] into a formatted string:

        R02: Mixed-use expenses should be claimed proportionally...
        R21: ...
        R16: ...

    Parameters
    ----------
    rule_ids   : List of rule ID strings from scenario audit.target.
    rules_data : Optional — pass the full rules list if already loaded.
                 If None, loaded automatically via retrieval.get_rules_data().

    Returns
    -------
    str : Newline-separated "RXX: rule_text" lines ready for prompt injection.
    """
    if rules_data is None:
        rules_data = get_rules_data()

    rule_lookup = {r["rule_id"]: r["rule_text"] for r in rules_data}

    lines = []
    for rid in rule_ids:
        text = rule_lookup.get(rid, "Rule text not found")
        lines.append(f"{rid}: {text}")

    return "\n".join(lines)
