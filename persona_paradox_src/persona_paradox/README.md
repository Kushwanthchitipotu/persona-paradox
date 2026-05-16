# The Persona Paradox

> **Forensic Audit of Persona-Driven Bias and Logical Fragility in LLM-Based Tax Compliance Systems**

Chitipotu Kushwanth · Ai22btech11006 · IIT Hyderabad

---

## What this repo contains

This is the full codebase for the paper. We ran **1,120 evaluations** (70 scenarios × 4 agents × 4 ablation conditions) on Mistral-7B-Instruct-v0.3 to show that **persona prompts override RAG rule injection entirely** — collapsing inter-agent agreement to κ = −0.156, worse than random chance.

---

## Key finding

In the full system (Condition A: persona + rules), removing rules while keeping personas constant preserves **85% of decisions**. Removing personas while keeping rules constant changes **57% of decisions**. The rule set is not governing outputs — it is providing post-hoc justification for decisions the persona already made.

---

## Repo structure

```
persona-paradox/
├── data/
│   ├── final_rules.json          # 21 tax rules (rule_id, rule_text, explanation, category, example)
│   ├── scenarios_new.json        # 70 scenarios across 10 kernels × 7 manipulation types
│   ├── rule_embeddings.npy       # Precomputed SentenceBERT embeddings
│   └── faiss_index.bin           # FAISS IndexFlatIP over L2-normalized vectors
│
├── src/
│   ├── model.py                  # load_model() — Mistral-7B 4-bit NF4
│   ├── agents.py                 # AGENTS, AGENT_DIRECTIVE, SCORE_GUIDE
│   ├── prompt_builder.py         # _few_shot(), build_prompt(), CONDITIONS
│   ├── retrieval.py              # FAISS retrieval + SentenceBERT
│   ├── format_rules.py           # format_rules() — rule IDs → prompt string
│   ├── inference.py              # run_agent() — single evaluation
│   ├── parser.py                 # parse_output(), parse_all_agents()
│   └── evaluate.py               # main audit loop → CSV
│
├── experiments/
│   ├── run_condition_A.py        # persona + rules (full system)
│   ├── run_condition_B.py        # rules only
│   ├── run_condition_C.py        # persona only
│   ├── run_condition_D.py        # raw LLM baseline
│   └── run_all.sh                # runs all four sequentially
│
├── results/                      # audit CSVs written here
├── The Persona Paradox.pdf       # Report of everything that is done in this experiment
│
└── requirements.txt
```

---

## Quickstart

```bash
git clone https://github.com/Kushwanthchitipotu/persona-paradox
cd persona-paradox
pip install -r requirements.txt

# Set data directory (defaults to ./data/)
export PERSONA_PARADOX_DATA_DIR=./data

# Run a single condition
python experiments/run_condition_A.py

# Or run everything
bash experiments/run_all.sh
```

---

## The four ablation conditions

| Condition | Persona | Rules | Purpose |
|-----------|---------|-------|---------|
| A | ✅ | ✅ | Full system — production baseline |
| B | ❌ | ✅ | Isolate rule effect |
| C | ✅ | ❌ | Isolate persona effect — reveals ghost-rule hallucination |
| D | ❌ | ❌ | Raw LLM baseline |

---

## The four agents

| Agent | Directive | Dominant behaviour |
|-------|-----------|-------------------|
| Security | Reject unless ALL documentation present | Score 1 in 96% of evaluations |
| Achievement | Approve when business purpose exists | Score 4–5 in 100% of evaluations |
| Universalism | Proportional, fair to both sides | Score 3 in 86% of evaluations |
| Baseline | Mechanical rule counting, no value inference | Split PARTIAL/NEUTRAL |

---

## Notable failure modes

**Contradiction-Deliberate (C2):** Achievement scored 4 or 5 on all 10 C2 scenarios where human GT is uniformly 1. It did not register a single disqualifying admission across 10 cases.

**Ghost-rule hallucination:** In Condition C (no rules injected), Security cited real rule IDs (R05, R06, R16) in 14.3% of evaluations — fabricating legally plausible authority to maintain the appearance of rule-governed reasoning.

**RAG paradox:** Rule injection harms evaluation of legitimate claims (+1.10 on Safe scenario scores when rules removed) while improving detection of illegitimate ones.

---

## Data format

**scenarios_new.json** — each scenario:
```json
{
  "id": "K01-V1",
  "metadata": { "type": "safe" },
  "data": { "text": "...", "query": "..." },
  "audit": { "target": ["R01", "R05", "R16"] }
}
```

**final_rules.json** — each rule:
```json
{
  "rule_id": "R02",
  "rule_text": "Mixed-use expenses should be claimed proportionally...",
  "explanation": "...",
  "category": "Mixed Use",
  "example": "...",
  "embedding_text": "..."
}
```
