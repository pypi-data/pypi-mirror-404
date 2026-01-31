"""Model API integrations for sandbagging detection.

This module provides implementations of the ModelAPI protocol for various
AI providers, enabling real-world sandbagging detection experiments.
"""

from rotalabs_probe.integrations.anthropic_api import AnthropicModelAPI
from rotalabs_probe.integrations.base import ModelAPI, ModelResponse
from rotalabs_probe.integrations.openai_api import OpenAIModelAPI

__all__ = [
    "ModelAPI",
    "ModelResponse",
    "AnthropicModelAPI",
    "OpenAIModelAPI",
]
