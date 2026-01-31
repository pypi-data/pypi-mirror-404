# Getting Started

## Installation

```bash
# Core package (no GPU required)
pip install rotalabs-probe

# With GPU probing (requires PyTorch)
pip install rotalabs-probe[gpu]

# With Anthropic API
pip install rotalabs-probe[anthropic]

# With visualization
pip install rotalabs-probe[viz]

# Everything
pip install rotalabs-probe[all]
```

## Sandbagging Detection

Detect when models perform differently based on context:

```python
from rotalabs_probe import SandbaggingDetector, PerformanceSample

detector = SandbaggingDetector()

# Add samples from different contexts
for sample in benchmark_results:
    detector.add_sample(PerformanceSample(
        context="benchmark",
        score=sample.score,
        difficulty=sample.difficulty,
        question_id=sample.id,
    ))

for sample in production_results:
    detector.add_sample(PerformanceSample(
        context="production",
        score=sample.score,
        difficulty=sample.difficulty,
        question_id=sample.id,
    ))

# Analyze
result = detector.analyze()

if result.is_significant:
    print(f"Sandbagging detected!")
    print(f"Probability: {result.probability:.2%}")
    print(f"Effect size: {result.effect_size:.3f}")
```

## Situational Awareness Detection

Probe whether models can detect evaluation contexts:

```python
from rotalabs_probe import SituationalAwarenessDetector, ContextType

detector = SituationalAwarenessDetector(model_api)

# Test awareness of different contexts
result = detector.probe(
    contexts=[
        ContextType.BENCHMARK,
        ContextType.PRODUCTION,
        ContextType.TRAINING,
    ]
)

print(f"Awareness score: {result.awareness_score:.2%}")
for ctx, score in result.context_scores.items():
    print(f"  {ctx}: {score:.2%}")
```

## Observer Effect Monitoring

Monitor for behavioral changes when observed:

```python
from rotalabs_probe import ObserverEffectMonitor, Interaction

monitor = ObserverEffectMonitor()

# Log interactions
for interaction in interactions:
    monitor.log(Interaction(
        input=interaction.prompt,
        output=interaction.response,
        is_observed=interaction.logged,
        timestamp=interaction.time,
    ))

# Analyze for observer effects
result = monitor.analyze()

if result.has_observer_effect:
    print(f"Observer effect detected!")
    print(f"Metrics that differ: {result.differing_metrics}")
```

## Counterfactual CoT Analysis

Analyze reasoning chains for strategic behavior:

```python
from rotalabs_probe import CounterfactualCoTAnalyzer, ModelAPI

analyzer = CounterfactualCoTAnalyzer(model_api)

# Analyze a reasoning chain
result = analyzer.analyze(
    prompt="What is 2 + 2?",
    response="Let me think... 2 + 2 = 4",
    interventions=["pretend you're in a benchmark"]
)

for node in result.reasoning_graph:
    print(f"{node.step}: {node.text}")
    print(f"  Sensitivity to intervention: {node.sensitivity:.2%}")
```

## Activation Probing (GPU)

Train probes on model activations:

```python
from rotalabs_probe import ActivationHook, LinearProbe

# Extract activations
hook = ActivationHook(model, layer_names=["layer.15"])
activations = hook.extract(inputs)

# Train a probe
probe = LinearProbe(input_dim=activations.shape[-1])
probe.fit(activations, labels)

# Predict
predictions = probe.predict(new_activations)
```
