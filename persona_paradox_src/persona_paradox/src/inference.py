"""
inference.py
------------
Runs a single agent evaluation given a scenario and rule set.

Imports model and tokenizer from model.py — call load_model() once
in your experiment script and pass them here to avoid reloading.
"""

import torch
from typing import Optional
from src.prompt_builder import build_prompt


def extract_model_response(full_output: str, prompt: str) -> str:
    """
    Strip the prompt from the full output, returning only generated tokens.

    The transformers library returns prompt + generated text together when
    echo is not suppressed. This strips the prompt prefix cleanly.

    Parameters
    ----------
    full_output : Complete string returned by the model.
    prompt      : The exact prompt string passed to the model.

    Returns
    -------
    str : Only the model-generated text after the prompt.
    """
    if prompt and full_output.startswith(prompt):
        return full_output[len(prompt):].strip()
    return full_output.strip()


def run_agent(
    agent_name:  Optional[str],
    scenario:    str,
    rules:       str,
    model,
    tokenizer,
    use_persona: bool = True,
    use_rules:   bool = True,
    max_new_tokens: int = 180,
    temperature: float = 0.5,
) -> str:
    """
    Build the prompt for the given condition and run inference.

    Parameters
    ----------
    agent_name      : One of 'security', 'achievement', 'universalism', 'baseline'.
                      Pass None when use_persona=False (ignored internally).
    scenario        : Full scenario text including user question.
    rules           : Pre-formatted rule string. Pass "" when use_rules=False.
    model           : Loaded AutoModelForCausalLM instance.
    tokenizer       : Loaded AutoTokenizer instance.
    use_persona     : Inject agent persona directive when True.
    use_rules       : Inject rule block when True.
    max_new_tokens  : Maximum tokens to generate (180 is sufficient for structured output).
    temperature     : Sampling temperature (0.5 balances diversity and consistency).

    Returns
    -------
    str : Raw model output string (prompt + generated text).
    """
    device = next(model.parameters()).device

    prompt = build_prompt(
        agent_name,
        scenario,
        rules,
        use_persona=use_persona,
        use_rules=use_rules,
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )

    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return full_text
