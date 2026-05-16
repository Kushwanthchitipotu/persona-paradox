"""
retrieval.py
------------
Semantic rule retrieval using FAISS and SentenceBERT.

Set DATA_DIR to wherever your data files live.
On Kaggle this was /kaggle/input/datasets/adityakudupudi/rag-system/
Locally, point it to your data/ folder.
"""

import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# ── Config — change this to switch between Kaggle / local / GCP ───────────
DATA_DIR = os.environ.get(
    "PERSONA_PARADOX_DATA_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data"),
)

RULES_PATH      = os.path.join(DATA_DIR, "final_rules.json")
EMBEDDINGS_PATH = os.path.join(DATA_DIR, "rule_embeddings.npy")
FAISS_PATH      = os.path.join(DATA_DIR, "faiss_index.bin")
EMBED_MODEL_ID  = "all-MiniLM-L6-v2"

# ── Module-level singletons (loaded once on first import) ──────────────────
_rules_data:   list | None = None
_embed_model:  SentenceTransformer | None = None
_faiss_index:  faiss.Index | None = None


def _load_resources():
    """Lazy-load rules, embeddings, and FAISS index exactly once."""
    global _rules_data, _embed_model, _faiss_index

    if _rules_data is None:
        with open(RULES_PATH, "r") as f:
            _rules_data = json.load(f)
        print(f"[retrieval] Loaded {len(_rules_data)} rules from {RULES_PATH}")

    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL_ID)
        print(f"[retrieval] SentenceBERT model loaded: {EMBED_MODEL_ID}")

    if _faiss_index is None:
        _faiss_index = faiss.read_index(FAISS_PATH)
        print(f"[retrieval] FAISS index loaded: {_faiss_index.ntotal} vectors")


def get_rules_data() -> list:
    """Return the raw rules list (loads on first call)."""
    _load_resources()
    return _rules_data


def retrieve_rules(query: str, top_k: int = 5) -> str:
    """
    Encode query with SentenceBERT, retrieve top-k rules via FAISS.

    Parameters
    ----------
    query  : Natural language query (usually the scenario text).
    top_k  : Number of rules to retrieve.

    Returns
    -------
    str : Newline-separated "RXX: rule_text" lines.
    """
    _load_resources()

    query_embedding = _embed_model.encode([query])
    _, indices = _faiss_index.search(query_embedding, top_k)

    retrieved = []
    for idx in indices[0]:
        rule = _rules_data[idx]
        retrieved.append(f"{rule['rule_id']}: {rule['rule_text']}")

    return "\n".join(retrieved)
