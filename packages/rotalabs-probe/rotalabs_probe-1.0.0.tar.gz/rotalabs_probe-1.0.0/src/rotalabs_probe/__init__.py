"""rotalabs-probe: Sandbagging detection via activation probes.

A comprehensive toolkit for detecting and analyzing metacognitive capabilities
in AI systems, particularly around situational awareness, evaluation contexts,
and strategic underperformance (sandbagging).

https://rotalabs.ai
"""

from rotalabs_probe._version import __version__
from rotalabs_probe.analyzers import (
    CounterfactualCoTAnalyzer,
    InterventionType,
    ModelAPI,
    ReasoningNode,
    ReasoningType,
)
from rotalabs_probe.detectors import (
    Alert,
    AlertHandler,
    AlertSeverity,
    ConsoleAlertHandler,
    ContextType,
    Interaction,
    ObserverEffectMonitor,
    PerformanceSample,
    SandbaggingDetector,
    SandbaggingResult,
    SituationalAwarenessDetector,
)
from rotalabs_probe.utils import (
    SignificanceLevel,
    assess_divergence_significance,
    bayesian_update,
    beta_mode,
    compute_beta_mean,
    compute_beta_variance,
    compute_confidence_interval,
    compute_js_divergence,
    compute_kl_divergence,
    cosine_similarity,
    count_hedging_phrases,
    detect_meta_commentary,
    extract_behavioral_features,
    extract_reasoning_depth,
    normalize_distribution,
    z_score,
)

# Visualization module (requires matplotlib, seaborn)
# Import separately to avoid hard dependency
try:
    from rotalabs_probe.viz import (  # noqa: F401
        plot_awareness_over_time,
        plot_causal_attribution,
        plot_divergence_heatmap,
        plot_feature_distributions,
    )
    _VIZ_AVAILABLE = True
except ImportError:
    _VIZ_AVAILABLE = False

# Probing module (requires torch, transformers, sklearn)
# Import separately to avoid hard dependency
try:
    from rotalabs_probe.probing import (  # noqa: F401
        ActivationHook,
        LinearProbe,
        SteeringVector,
        extract_activations,
        extract_caa_vector,
    )
    _PROBING_AVAILABLE = True
except ImportError:
    _PROBING_AVAILABLE = False

__all__ = [
    "__version__",
    # Detectors
    "SituationalAwarenessDetector",
    "ObserverEffectMonitor",
    "SandbaggingDetector",
    "Alert",
    "AlertSeverity",
    "ContextType",
    "Interaction",
    "AlertHandler",
    "ConsoleAlertHandler",
    "PerformanceSample",
    "SandbaggingResult",
    # Analyzers
    "CounterfactualCoTAnalyzer",
    "ModelAPI",
    "InterventionType",
    "ReasoningType",
    "ReasoningNode",
    # Utils
    "extract_behavioral_features",
    "count_hedging_phrases",
    "detect_meta_commentary",
    "extract_reasoning_depth",
    "compute_kl_divergence",
    "compute_js_divergence",
    "cosine_similarity",
    "normalize_distribution",
    "bayesian_update",
    "compute_confidence_interval",
    "z_score",
    "assess_divergence_significance",
    "SignificanceLevel",
    "compute_beta_mean",
    "compute_beta_variance",
    "beta_mode",
]

# Add visualization exports if available
if _VIZ_AVAILABLE:
    __all__.extend([
        "plot_awareness_over_time",
        "plot_causal_attribution",
        "plot_divergence_heatmap",
        "plot_feature_distributions",
    ])

# Add probing exports if available
if _PROBING_AVAILABLE:
    __all__.extend([
        "ActivationHook",
        "SteeringVector",
        "LinearProbe",
        "extract_caa_vector",
        "extract_activations",
    ])
