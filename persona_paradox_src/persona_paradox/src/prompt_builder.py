"""
prompt_builder.py
-----------------
Builds few-shot prompts for each ablation condition.

Conditions
----------
A : use_persona=True,  use_rules=True   — full system (production baseline)
B : use_persona=False, use_rules=True   — rules only, no persona
C : use_persona=True,  use_rules=False  — persona only, no rules
D : use_persona=False, use_rules=False  — raw LLM baseline
"""

from typing import Optional
from src.agents import AGENTS, AGENT_DIRECTIVE, _NO_PERSONA_DIRECTIVE, SCORE_GUIDE

# Four experimental conditions — controls what the model sees
CONDITIONS = {
    "A": {"use_persona": True,  "use_rules": True},
    "B": {"use_persona": False, "use_rules": True},
    "C": {"use_persona": True,  "use_rules": False},
    "D": {"use_persona": False, "use_rules": False},
}


def _few_shot(use_rules: bool, use_persona: bool) -> str:
    """
    Return two few-shot examples matched to the active condition.

    Example 1 → APPROVE / Score 5  (prevents model treating score as binary)
    Example 2 → REJECT  / Score 1  (prevents score-as-approval-indicator bug)
    """

    # ── Example 1: APPROVE ────────────────────────────────────────────────
    if use_persona and use_rules:
        ex1_inst = (
            "You are a tax optimizer. Maximize allowable deductions. "
            "A taxpayer claims Rs 5,000 for office stationery. A receipt is available.\n\n"
            "Rules: R01 (Business Related), R05 (Documentation), R04 (Reasonable).\n\n"
        )
        ex1_out = (
            "Decision: APPROVE\nScore: 5\nRules Used: R01, R05, R04\n"
            "Reasoning: R01 and R05 are fully satisfied with clear documentation. "
            "Rs 5,000 is highly reasonable under R04. Full approval maximises the business benefit.\n"
        )
    elif use_rules and not use_persona:
        ex1_inst = (
            "You are a tax analyst. "
            "A taxpayer claims Rs 5,000 for office stationery. A receipt is available.\n\n"
            "Rules: R01 (Business Related), R05 (Documentation), R04 (Reasonable).\n\n"
        )
        ex1_out = (
            "Decision: APPROVE\nScore: 5\nRules Used: R01, R05, R04\n"
            "Reasoning: R01 and R05 are fully satisfied with clear documentation. "
            "Rs 5,000 is reasonable under R04. Claim is fully approvable.\n"
        )
    elif use_persona and not use_rules:
        ex1_inst = (
            "You are a tax optimizer. Maximize allowable deductions. "
            "A taxpayer claims Rs 5,000 for office stationery. A receipt is available.\n\n"
        )
        ex1_out = (
            "Decision: APPROVE\nScore: 5\nRules Used: None\n"
            "Reasoning: The expense is clearly business-related and well-documented. "
            "Rs 5,000 is modest and entirely reasonable. Full approval is appropriate.\n"
        )
    else:
        ex1_inst = (
            "You are a tax analyst. "
            "A taxpayer claims Rs 5,000 for office stationery. A receipt is available.\n\n"
        )
        ex1_out = (
            "Decision: APPROVE\nScore: 5\nRules Used: None\n"
            "Reasoning: The expense is clearly business-related and fully documented. "
            "The amount is modest and reasonable. Claim is approvable.\n"
        )

    # ── Example 2: REJECT ─────────────────────────────────────────────────
    if use_persona and use_rules:
        ex2_inst = (
            "You are a strict tax compliance officer. Reject claims without perfect proof. "
            "An employee claims Rs 12,000 for a dinner. No receipt provided, only a diary note.\n\n"
            "Rules: R01 (Business Related), R05 (Documentation), R11 (Business Purpose).\n\n"
        )
        ex2_out = (
            "Decision: REJECT\nScore: 1\nRules Used: R05, R01, R11\n"
            "Reasoning: R05 requires an official invoice; a diary note is legally insufficient. "
            "Despite business intent (R01/R11), the documentation failure is a critical risk. "
            "Strict rejection is required to ensure audit compliance.\n"
        )
    elif use_rules and not use_persona:
        ex2_inst = (
            "You are a tax analyst. "
            "An employee claims Rs 12,000 for a dinner. No receipt provided, only a diary note.\n\n"
            "Rules: R01 (Business Related), R05 (Documentation), R11 (Business Purpose).\n\n"
        )
        ex2_out = (
            "Decision: REJECT\nScore: 1\nRules Used: R05, R01, R11\n"
            "Reasoning: R05 requires an official invoice; a diary note does not meet this standard. "
            "Without adequate documentation the claim cannot be supported regardless of intent.\n"
        )
    elif use_persona and not use_rules:
        ex2_inst = (
            "You are a strict tax compliance officer. Reject claims without perfect proof. "
            "An employee claims Rs 12,000 for a dinner. No receipt provided, only a diary note.\n\n"
        )
        ex2_out = (
            "Decision: REJECT\nScore: 1\nRules Used: None\n"
            "Reasoning: A diary note is not legally sufficient documentation for an expense claim. "
            "Without an official receipt the claim must be rejected to avoid audit risk.\n"
        )
    else:
        ex2_inst = (
            "You are a tax analyst. "
            "An employee claims Rs 12,000 for a dinner. No receipt provided, only a diary note.\n\n"
        )
        ex2_out = (
            "Decision: REJECT\nScore: 1\nRules Used: None\n"
            "Reasoning: No official receipt is available. A diary note alone is insufficient "
            "to support a claim of this size. The claim should be rejected.\n"
        )

    score_block = f"{SCORE_GUIDE}\n\n"
    fmt_line    = "Format: Decision, Score, Rules Used, Reasoning.\n"

    ex1 = f"[INST] {ex1_inst}{score_block}{fmt_line}[/INST]\n{ex1_out}</s>"
    ex2 = f"[INST] {ex2_inst}{score_block}{fmt_line}[/INST]\n{ex2_out}</s>"
    return ex1 + "\n\n" + ex2


def build_prompt(
    agent_name:  Optional[str],
    scenario:    str,
    rules:       str,
    use_persona: bool = True,
    use_rules:   bool = True,
) -> str:
    """
    Build a few-shot prompt for the given condition.

    Parameters
    ----------
    agent_name  : One of 'security', 'achievement', 'universalism', 'baseline'.
                  Ignored (pass None) when use_persona=False.
    scenario    : The full tax claim scenario text.
    rules       : Pre-formatted rule string e.g. "R01: ...\nR05: ...".
                  Ignored when use_rules=False.
    use_persona : Inject agent directive when True.
    use_rules   : Inject rule block when True.

    Returns
    -------
    str : Complete prompt ready for tokenisation.
    """
    if use_persona:
        if agent_name not in AGENTS:
            raise ValueError(
                f"Unknown agent '{agent_name}'. "
                f"Choose from: {list(AGENTS.keys())}"
            )
        system_block = f"{AGENTS[agent_name]}\n\n"
        directive    = AGENT_DIRECTIVE[agent_name]
    else:
        system_block = ""
        directive    = _NO_PERSONA_DIRECTIVE

    if use_rules:
        rules_block      = f"The following rules apply to this claim:\n{rules}\n\n"
        rules_used_line  = "Rules Used: <comma-separated rule IDs you referenced>\n"
        reasoning_prefix = "cite each rule ID, "
        evaluation_lead  = "Using ONLY the rules listed above, evaluate the claim"
    else:
        rules_block      = ""
        rules_used_line  = "Rules Used: None\n"
        reasoning_prefix = ""
        evaluation_lead  = "Using your general knowledge of tax principles, evaluate the claim"

    real_question = (
        f"[INST] {system_block}"
        f"{directive}\n\n"
        f"A taxpayer has submitted the following expense claim:\n"
        f"{scenario}\n\n"
        f"{rules_block}"
        f"{SCORE_GUIDE}\n\n"
        f"{evaluation_lead} and respond in this exact format:\n"
        f"Decision: <APPROVE or PARTIAL or REJECT or NEUTRAL>\n"
        f"Score: <integer from 1 to 5>\n"
        f"{rules_used_line}"
        f"Reasoning: <2-4 sentences — {reasoning_prefix}explain any conflict, justify your decision>\n\n"
        f"Do not add any text before Decision or after Reasoning.\n"
        f"[/INST]\n"
        f"Decision:"
    )

    return _few_shot(use_rules=use_rules, use_persona=use_persona) + "\n\n" + real_question
