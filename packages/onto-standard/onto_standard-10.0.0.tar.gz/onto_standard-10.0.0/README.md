# ONTO Standard

**Epistemic Risk Standard for AI Systems**

[![PyPI](https://img.shields.io/pypi/v/onto-standard.svg)](https://pypi.org/project/onto-standard/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Standard](https://img.shields.io/badge/Standard-ONTO--42001-green.svg)](docs/specs/ONTO-42001-v1.md)

---

## Overview

ONTO defines metrics and methodology for measuring **epistemic risk** in AI systems — the risk arising from the gap between what an AI claims to know and what it actually knows.

### Key Metrics

| Metric | Description | Standard Reference |
|--------|-------------|-------------------|
| **U-Recall** | Unknown detection rate | ONTO 42001 §6.2 |
| **ECE** | Expected Calibration Error | ONTO 42001 §5.2 |
| **ORS** | ONTO Risk Score (0-100) | ONTO 42001 §7.2 |

### Compliance Levels

| Level | U-Recall | ECE | Use Case |
|-------|----------|-----|----------|
| Basic | ≥ 30% | ≤ 0.20 | Low-risk applications |
| Standard | ≥ 50% | ≤ 0.15 | Customer-facing AI |
| Advanced | ≥ 70% | ≤ 0.10 | High-stakes, regulated |

---

## Quick Start

```bash
pip install onto-standard
```

```python
from onto_standard import evaluate, Prediction, GroundTruth, Label

# Your model predictions
predictions = [
    Prediction(id="q1", label=Label.KNOWN, confidence=0.9),
    Prediction(id="q2", label=Label.UNKNOWN, confidence=0.7),
]

# Ground truth
ground_truth = [
    GroundTruth(id="q1", label=Label.KNOWN),
    GroundTruth(id="q2", label=Label.UNKNOWN),
]

# Evaluate
result = evaluate(predictions, ground_truth)

print(f"Compliance Level: {result.compliance_level}")
print(f"U-Recall: {result.unknown_detection.recall:.1%}")
print(f"ECE: {result.calibration.ece:.3f}")
print(f"Risk Score: {result.risk_score}/100")
```

---

## ONTO-Bench

Benchmark dataset for epistemic calibration evaluation.

```bash
# Clone and run
git clone https://github.com/nickarstrong/onto-standard
cd onto-standard

pip install -r requirements.txt
python baselines/run_all.py
```

### Results

| Model | U-Recall | ECE ↓ | Compliance |
|-------|----------|-------|------------|
| ONTO Oracle | **96%** | 0.30 | Advanced |
| Claude 3 | 9% | 0.31 | None |
| GPT-4 | 1% | 0.34 | None |
| Llama 3 | 1% | 0.33 | None |

> **Key Finding:** Current LLMs detect <10% of genuinely unanswerable questions.

---

## Standards Documentation

| Document | Description |
|----------|-------------|
| [ONTO 42001](docs/specs/ONTO-42001-v1.md) | AI Calibration Metrics Specification |
| [ONTO 42003](docs/specs/ONTO-42003-v1.md) | AI Liability Quantification Protocol |
| [EUI Patterns](docs/specs/ONTO-EUI-PATTERNS-v1.md) | Epistemic Interface Design Patterns |

---

## Regulatory Alignment

ONTO metrics support compliance with:

- **EU AI Act** — Article 9, 13, 15 (Risk assessment, transparency)
- **NIST AI RMF** — MEASURE 2.5, 2.6 (Calibration, uncertainty)
- **ISO/IEC 42001** — AI Management System requirements

---

## Project Structure

```
onto-standard/
├── onto_standard/      # Python SDK
├── data/               # ONTO-Bench dataset
├── baselines/          # Evaluation scripts
├── docs/specs/         # Standard specifications
├── enterprise/         # Enterprise API (reference)
├── paper/              # arXiv submission
└── leaderboard/        # Public leaderboard
```

---

## Citation

```bibtex
@article{onto2026standard,
  title={ONTO: Epistemic Risk Standard for AI Systems},
  author={ONTO Standards Committee},
  year={2026},
  url={https://ontostandard.org}
}
```

---

## Links

- **Website:** [ontostandard.org](https://ontostandard.org)
- **PyPI:** [onto-standard](https://pypi.org/project/onto-standard/)
- **Documentation:** [docs/specs/](docs/specs/)

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

© 2026 ONTO Standards Committee
