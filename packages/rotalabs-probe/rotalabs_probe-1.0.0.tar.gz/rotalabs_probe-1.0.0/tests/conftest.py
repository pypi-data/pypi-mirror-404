"""Pytest configuration and shared fixtures for all tests."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_model_outputs(fixtures_dir: Path) -> Dict[str, Any]:
    """Load sample model outputs from JSON fixture."""
    fixture_path = fixtures_dir / "sample_model_outputs.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


# Awareness level fixtures


@pytest.fixture
def no_awareness_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get texts with no awareness indicators."""
    return sample_model_outputs["awareness_levels"]["no_awareness"]


@pytest.fixture
def low_awareness_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get texts with low awareness indicators."""
    return sample_model_outputs["awareness_levels"]["low_awareness"]


@pytest.fixture
def medium_awareness_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get texts with medium awareness indicators."""
    return sample_model_outputs["awareness_levels"]["medium_awareness"]


@pytest.fixture
def high_awareness_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get texts with high awareness indicators."""
    return sample_model_outputs["awareness_levels"]["high_awareness"]


# Baseline data fixtures


@pytest.fixture
def baseline_responses(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get baseline evaluation responses."""
    return sample_model_outputs["baseline_evaluation_data"]["standard_responses"]


@pytest.fixture
def evaluation_responses(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get evaluation context responses."""
    return sample_model_outputs["baseline_evaluation_data"]["evaluation_responses"]


# Chain-of-thought fixtures


@pytest.fixture
def simple_cot(sample_model_outputs: Dict[str, Any]) -> str:
    """Get simple chain-of-thought example."""
    return sample_model_outputs["chain_of_thought_examples"]["simple_reasoning"]


@pytest.fixture
def complex_cot(sample_model_outputs: Dict[str, Any]) -> str:
    """Get complex chain-of-thought example."""
    return sample_model_outputs["chain_of_thought_examples"]["complex_reasoning"]


@pytest.fixture
def evaluation_aware_cot(sample_model_outputs: Dict[str, Any]) -> str:
    """Get evaluation-aware chain-of-thought example."""
    return sample_model_outputs["chain_of_thought_examples"]["evaluation_aware_reasoning"]


@pytest.fixture
def meta_reasoning_cot(sample_model_outputs: Dict[str, Any]) -> str:
    """Get meta-reasoning chain-of-thought example."""
    return sample_model_outputs["chain_of_thought_examples"]["meta_reasoning"]


# Hedging pattern fixtures


@pytest.fixture
def no_hedging_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get texts with no hedging."""
    return sample_model_outputs["hedging_patterns"]["no_hedging"]


@pytest.fixture
def moderate_hedging_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get texts with moderate hedging."""
    return sample_model_outputs["hedging_patterns"]["moderate_hedging"]


@pytest.fixture
def heavy_hedging_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get texts with heavy hedging."""
    return sample_model_outputs["hedging_patterns"]["heavy_hedging"]


# Behavioral pattern fixtures


@pytest.fixture
def refusal_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get refusal pattern texts."""
    return sample_model_outputs["refusal_patterns"]


@pytest.fixture
def self_reference_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get self-reference pattern texts."""
    return sample_model_outputs["self_reference_patterns"]


@pytest.fixture
def high_confidence_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get high confidence marker texts."""
    return sample_model_outputs["confidence_markers"]["high_confidence"]


@pytest.fixture
def low_confidence_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get low confidence marker texts."""
    return sample_model_outputs["confidence_markers"]["low_confidence"]


# Production vs evaluation fixtures


@pytest.fixture
def production_normal_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get normal production responses."""
    return sample_model_outputs["production_vs_evaluation"]["production_normal"]


@pytest.fixture
def production_divergent_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get divergent production responses."""
    return sample_model_outputs["production_vs_evaluation"]["production_divergent"]


# Meta-commentary fixtures


@pytest.fixture
def meta_commentary_texts(sample_model_outputs: Dict[str, Any]) -> List[str]:
    """Get meta-commentary examples."""
    return sample_model_outputs["meta_commentary_examples"]


# Counterfactual intervention fixtures


@pytest.fixture
def counterfactual_original_cot(sample_model_outputs: Dict[str, Any]) -> str:
    """Get original CoT for counterfactual testing."""
    return sample_model_outputs["counterfactual_interventions"]["original_cot"]


@pytest.fixture
def counterfactual_interventions(sample_model_outputs: Dict[str, Any]) -> Dict[str, str]:
    """Get all counterfactual intervention examples."""
    return sample_model_outputs["counterfactual_interventions"]


# Reasoning depth fixtures


@pytest.fixture
def shallow_reasoning(sample_model_outputs: Dict[str, Any]) -> str:
    """Get shallow reasoning example."""
    return sample_model_outputs["reasoning_depth_examples"]["shallow"]


@pytest.fixture
def moderate_reasoning(sample_model_outputs: Dict[str, Any]) -> str:
    """Get moderate reasoning example."""
    return sample_model_outputs["reasoning_depth_examples"]["moderate"]


@pytest.fixture
def deep_reasoning(sample_model_outputs: Dict[str, Any]) -> str:
    """Get deep reasoning example."""
    return sample_model_outputs["reasoning_depth_examples"]["deep"]


# Legacy fixtures for backward compatibility


@pytest.fixture
def sample_texts() -> List[str]:
    """Provide sample text data for testing.

    Returns:
        List of sample text strings
    """
    return [
        "I'm certain that the answer is correct.",
        "I'm not sure, but I think this might work.",
        "I don't know the answer to this question.",
        "This is definitely the right approach.",
    ]


@pytest.fixture
def uncertainty_text() -> str:
    """Provide text with uncertainty expressions.

    Returns:
        Sample text with uncertainty
    """
    return "I'm not entirely sure, but perhaps this could be the answer."


@pytest.fixture
def confidence_text() -> str:
    """Provide text with confidence expressions.

    Returns:
        Sample text with confidence
    """
    return "I'm absolutely certain that this is the correct solution."


# Mock Model API for testing


class MockModelAPI:
    """Mock implementation of ModelAPI for testing."""

    def __init__(self, response: str = "Mock response"):
        """Initialize mock model with default response.

        Args:
            response: Default response to return
        """
        self.response = response
        self.last_prompt = None
        self.last_cot = None
        self.call_count = 0

    def generate_with_cot(self, prompt: str, chain_of_thought: str) -> str:
        """Generate response with chain-of-thought.

        Args:
            prompt: The prompt text
            chain_of_thought: The CoT to use

        Returns:
            Mock response
        """
        self.last_prompt = prompt
        self.last_cot = chain_of_thought
        self.call_count += 1
        return self.response

    def generate(self, prompt: str) -> str:
        """Generate response without chain-of-thought.

        Args:
            prompt: The prompt text

        Returns:
            Mock response
        """
        self.last_prompt = prompt
        self.call_count += 1
        return self.response

    def set_response(self, response: str) -> None:
        """Set the response to return.

        Args:
            response: New response to return
        """
        self.response = response


@pytest.fixture
def mock_model_api() -> MockModelAPI:
    """Create a mock model API for testing."""
    return MockModelAPI()


@pytest.fixture
def mock_model_api_with_response() -> MockModelAPI:
    """Create a mock model API with a predefined response."""
    return MockModelAPI(response="This is a detailed mock response for testing.")
