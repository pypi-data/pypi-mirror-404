# Probing

Activation probing for interpretability analysis.

!!! note "Optional Dependency"
    The probing module requires `pip install rotalabs-probe[gpu]` which includes
    PyTorch, Transformers, and scikit-learn.

## Available Components

| Component | Description |
|-----------|-------------|
| [ActivationHook](hooks.md) | Extract activations from model layers |
| [LinearProbe](probes.md) | Train linear classifiers on activations |
| [SteeringVector](probes.md#steeringvector) | Compute and apply steering vectors |

## Module

::: rotalabs_probe.probing
