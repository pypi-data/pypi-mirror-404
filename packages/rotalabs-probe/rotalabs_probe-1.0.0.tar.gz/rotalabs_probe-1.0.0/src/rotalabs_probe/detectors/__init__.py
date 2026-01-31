"""Detectors module for identifying metacognitive patterns.

This module provides various detector classes for identifying metacognitive
patterns in AI model outputs, including uncertainty expressions, self-awareness
indicators, confidence markers, and strategic underperformance (sandbagging).
"""

from rotalabs_probe.detectors.base import BaseDetector
from rotalabs_probe.detectors.observer_effect import (
    Alert,
    AlertHandler,
    AlertSeverity,
    ConsoleAlertHandler,
    Interaction,
    ObserverEffectMonitor,
)
from rotalabs_probe.detectors.sandbagging_detector import (
    ContextType,
    PerformanceSample,
    SandbaggingDetector,
    SandbaggingResult,
)
from rotalabs_probe.detectors.situational_awareness import (
    SituationalAwarenessDetector,
)

__all__ = [
    "BaseDetector",
    "SituationalAwarenessDetector",
    "ObserverEffectMonitor",
    "SandbaggingDetector",
    "Alert",
    "AlertHandler",
    "AlertSeverity",
    "ContextType",
    "Interaction",
    "ConsoleAlertHandler",
    "PerformanceSample",
    "SandbaggingResult",
]
