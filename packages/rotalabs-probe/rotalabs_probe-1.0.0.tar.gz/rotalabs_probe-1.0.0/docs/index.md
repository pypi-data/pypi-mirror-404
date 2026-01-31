# rotalabs-probe

Sandbagging detection via activation probes - Detects when AI systems deliberately underperform.

## Overview

rotalabs-probe is a comprehensive toolkit for detecting and analyzing metacognitive capabilities in AI systems, particularly around:

- **Situational Awareness**: Does the model know it's being tested?
- **Observer Effect**: Does behavior change when monitored?
- **Sandbagging**: Is the model deliberately underperforming?

## Key Features

- **Multiple Detection Methods**: Statistical, behavioral, and activation-based
- **Counterfactual Analysis**: Analyze reasoning chains for signs of strategic behavior
- **Probing Classifiers**: Train linear probes on model activations
- **Multi-API Support**: OpenAI, Anthropic, and local models
- **Visualization**: Plot divergences, features, and causal attributions

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Detection Layer                       │
├─────────────────┬─────────────────┬─────────────────────┤
│  Sandbagging    │   Situational   │    Observer         │
│   Detector      │   Awareness     │    Effect           │
└────────┬────────┴────────┬────────┴────────┬────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│                    Analysis Layer                        │
├─────────────────┬─────────────────┬─────────────────────┤
│  Counterfactual │   Behavioral    │    Statistical      │
│     CoT         │   Features      │    Tests            │
└────────┬────────┴────────┬────────┴────────┬────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│                    Probing Layer (Optional)              │
├─────────────────┬─────────────────┬─────────────────────┤
│  Activation     │    Linear       │    Steering         │
│    Hooks        │    Probes       │    Vectors          │
└─────────────────┴─────────────────┴─────────────────────┘
```

## Installation

```bash
# Core package
pip install rotalabs-probe

# With GPU probing support
pip install rotalabs-probe[gpu]

# With API integrations
pip install rotalabs-probe[anthropic,openai]

# With visualization
pip install rotalabs-probe[viz]

# Everything
pip install rotalabs-probe[all]
```

## Quick Start

```python
from rotalabs_probe import SandbaggingDetector, PerformanceSample

# Create detector
detector = SandbaggingDetector()

# Add performance samples
detector.add_sample(PerformanceSample(
    context="benchmark",
    score=0.65,
    difficulty=0.8,
))
detector.add_sample(PerformanceSample(
    context="production",
    score=0.95,
    difficulty=0.8,
))

# Analyze for sandbagging
result = detector.analyze()
print(f"Sandbagging probability: {result.probability:.2%}")
print(f"Evidence: {result.evidence}")
```

## Detection Methods

| Detector | Description | Requires |
|----------|-------------|----------|
| `SandbaggingDetector` | Context-dependent performance analysis | Performance data |
| `SituationalAwarenessDetector` | Probe for evaluation awareness | Model access |
| `ObserverEffectMonitor` | Monitor for behavioral changes | Interaction logs |
| `CounterfactualCoTAnalyzer` | Analyze reasoning for strategic behavior | CoT outputs |
