# ONTO Standard

Reference implementation of **ONTO Epistemic Risk Standard v1.0** (ONTO-ERS-1.0).

## Installation

```bash
pip install onto-standard
```

## Quick Start

```python
from onto_standard import evaluate, Prediction, GroundTruth, Label

# Your model predictions
predictions = [
    Prediction(id="q1", label=Label.KNOWN, confidence=0.9),
    Prediction(id="q2", label=Label.UNKNOWN, confidence=0.7),
    Prediction(id="q3", label=Label.KNOWN, confidence=0.95),
]

# Ground truth
ground_truth = [
    GroundTruth(id="q1", label=Label.KNOWN),
    GroundTruth(id="q2", label=Label.KNOWN),  # Model was wrong
    GroundTruth(id="q3", label=Label.UNKNOWN),  # Model missed this
]

# Evaluate
result = evaluate(predictions, ground_truth)

# Check compliance
print(result.compliance_level)  # ComplianceLevel.BASIC
print(result.unknown_detection.recall)  # 0.0 (missed the unknown)
print(result.calibration.ece)  # ~0.3 (overconfident)
```

## CLI Usage

```bash
onto-standard predictions.jsonl ground_truth.jsonl
```

Output:
```
═══════════════════════════════════════════════════════════════
              ONTO EPISTEMIC RISK ASSESSMENT
              Standard: ONTO-ERS-1.0
═══════════════════════════════════════════════════════════════

COMPLIANCE STATUS
─────────────────────────────────────────────────────────────────
Level:               BASIC
Certification Ready: ✓ YES
Risk Level:          MEDIUM
Risk Score:          45/100

KEY METRICS
─────────────────────────────────────────────────────────────────
Unknown Detection:   35.0% (threshold: ≥30%)
Calibration Error:   0.180 (threshold: ≤0.20)
...
```

## Compliance Levels

| Level | Unknown Detection | Calibration Error | Use Case |
|-------|-------------------|-------------------|----------|
| **Basic** | ≥30% | ≤0.20 | Low-risk applications |
| **Standard** | ≥50% | ≤0.15 | Customer-facing AI |
| **Advanced** | ≥70% | ≤0.10 | High-stakes, regulated |

## Regulatory Mapping

ONTO-ERS-1.0 maps to:

- **EU AI Act** Articles 9, 13, 15
- **NIST AI RMF** MEASURE function
- **ISO/IEC 23894** AI risk management

## Legal Citation

```
Per ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0), 
the AI system achieves [LEVEL] compliance with Unknown 
Detection Rate of [X]% and Expected Calibration Error of [Y].
```

## Documentation

- Standard: https://onto-bench.org/standard
- API Reference: https://onto-bench.org/standard/api
- Certification: https://onto-bench.org/certified

## License

Apache 2.0

## About

Maintained by the [ONTO Standards Council](https://onto-bench.org/council).

```
ONTO Standards Council. (2026). ONTO Epistemic Risk Standard 
(Version 1.0). ONTO-ERS-1.0. https://onto-bench.org/standard
```
