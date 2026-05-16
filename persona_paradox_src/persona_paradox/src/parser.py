"""
parser.py
---------
Parses structured Decision / Score / Rules Used / Reasoning from raw model output.

Handles all edge cases encountered across 1,120 evaluations:
  - Few-shot examples echoed in output  → takes the LAST Decision block
  - Score as "2" or "2/5"
  - Score: 0 outputs                    → clamped to 1
  - Label variants: Rules Used / Rule IDs / Rules Referenced
  - Trailing artifacts: </s>, [INST], excessive blank lines
  - Missing fields                      → [WARN] emitted without crashing
"""

import re


def parse_output(raw_text: str) -> dict:
    """
    Extract Decision, Score, Rules Used, and Reasoning from model output.

    Parameters
    ----------
    raw_text : Raw model output string (prompt + generated tokens, or just generated).

    Returns
    -------
    dict with keys: decision, score, rules_used, reasoning.
    Any unparseable field is None and triggers a [WARN] print.
    """

    # ── Strip few-shot echoes: split on every "Decision:" keep only last ──
    chunks = re.split(r"(?im)^Decision\s*:", raw_text)
    if len(chunks) < 2:
        return {
            "decision":    None,
            "score":       None,
            "rules_used":  [],
            "reasoning":   None,
            "parse_error": "No 'Decision:' found in output",
        }

    answer_block = "Decision:" + chunks[-1]

    # ── Decision ──────────────────────────────────────────────────────────
    decision_match = re.search(
        r"Decision\s*:\s*(APPROVE|PARTIAL|REJECT|NEUTRAL)",
        answer_block, re.IGNORECASE
    )
    decision = decision_match.group(1).upper() if decision_match else None

    # ── Score — clamp 0 to 1 (model occasionally outputs 0) ───────────────
    score_match = re.search(r"Score\s*:\s*([0-5])(?:/5)?", answer_block)
    if score_match:
        score = int(score_match.group(1))
        score = max(score, 1)   # 0 is invalid on the 1-5 scale
    else:
        score = None

    # ── Rules Used — handle label variants ────────────────────────────────
    rules_match = re.search(
        r"(?:Rules?\s*(?:Used|IDs?|Referenced)?)\s*:\s*([^\n]+)",
        answer_block, re.IGNORECASE
    )
    rules_used = []
    if rules_match:
        rules_used = re.findall(r"R\d{2}", rules_match.group(1), re.IGNORECASE)
        rules_used = [r.upper() for r in rules_used]

    # ── Reasoning — strip trailing model artifacts ─────────────────────────
    reasoning_match = re.search(
        r"Reasoning\s*:\s*([\s\S]+)", answer_block, re.IGNORECASE
    )
    reasoning = None
    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()
        reasoning = re.split(r"\n{3,}|\[INST\]|<\/s>|\[\/INST\]", reasoning)[0].strip()

    # ── Warn on unparseable fields ─────────────────────────────────────────
    result = {
        "decision":   decision,
        "score":      score,
        "rules_used": rules_used,
        "reasoning":  reasoning,
    }
    for field, value in result.items():
        if value is None or value == []:
            print(f"[WARN] Could not parse field: '{field}'")

    return result


def parse_all_agents(agent_outputs: dict) -> dict:
    """
    Parse outputs from all agents at once.

    Parameters
    ----------
    agent_outputs : {agent_name: raw_model_output_string}

    Returns
    -------
    {agent_name: parsed_dict}
    """
    return {name: parse_output(text) for name, text in agent_outputs.items()}


def print_parsed(parsed: dict, agent_name: str = ""):
    """Pretty-print a single parsed result for debugging."""
    label = agent_name.upper() if agent_name else "RESULT"
    rules = ", ".join(parsed["rules_used"]) if parsed["rules_used"] else "N/A"
    print(f"\n{'='*55}")
    print(f"  AGENT      : {label}")
    print(f"  Decision   : {parsed['decision']}")
    print(f"  Score      : {parsed['score']}/5")
    print(f"  Rules Used : {rules}")
    print(f"  Reasoning  : {parsed['reasoning']}")
    print(f"{'='*55}")
