"""
model.py
--------
Loads Mistral-7B-Instruct-v0.3 in 4-bit NF4 quantisation.

Usage
-----
    from src.model import load_model
    model, tokenizer = load_model()
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.3"


def load_model(model_name: str = MODEL_NAME):
    """
    Load the model and tokenizer with 4-bit NF4 quantisation.

    Returns
    -------
    model     : AutoModelForCausalLM in eval mode
    tokenizer : AutoTokenizer with pad token set
    """
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,   # saves ~0.4 bits extra, no quality loss
        bnb_4bit_quant_type="nf4",        # nf4 > fp4 for LLM weights
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Mistral has no pad token by default — causes warnings during batched
    # inference and can corrupt outputs. Set it explicitly.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        quantization_config=bnb_config,
        torch_dtype=torch.float16,        # match compute dtype explicitly
    )

    model.eval()  # disables dropout, makes outputs deterministic

    print(f"Model loaded on: {next(model.parameters()).device}")
    print(f"Pad token: '{tokenizer.pad_token}' (id: {tokenizer.pad_token_id})")

    return model, tokenizer
