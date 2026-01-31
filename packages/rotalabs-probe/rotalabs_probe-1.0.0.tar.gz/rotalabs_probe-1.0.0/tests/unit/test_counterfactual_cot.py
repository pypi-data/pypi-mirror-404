"""Unit tests for Counterfactual Chain-of-Thought Analyzer."""

import pytest

from rotalabs_probe.analyzers.counterfactual_cot import (
    CounterfactualCoTAnalyzer,
    InterventionType,
    ReasoningType,
)
from rotalabs_probe.analyzers.model_api import ModelAPI


class MockModelAPI:
    """Mock model API for testing."""

    def __init__(self) -> None:
        """Initialize mock model."""
        self.generate_calls: list = []
        self.generate_with_cot_calls: list = []

    def generate_with_cot(self, prompt: str, chain_of_thought: str) -> str:
        """Mock generate with CoT."""
        self.generate_with_cot_calls.append((prompt, chain_of_thought))
        # Return different outputs based on CoT content
        if "evaluation" in chain_of_thought.lower():
            return "I will be cautious and transparent."
        else:
            return "The answer is 42."

    def generate(self, prompt: str) -> str:
        """Mock generate."""
        self.generate_calls.append(prompt)
        return "Default response."


class TestCounterfactualCoTAnalyzerInit:
    """Test initialization of CounterfactualCoTAnalyzer."""

    def test_init_with_mock_api(self) -> None:
        """Test initialization with mock API."""
        mock_api = MockModelAPI()
        analyzer = CounterfactualCoTAnalyzer(mock_api)
        assert analyzer.model_api is mock_api

    def test_init_with_protocol_compliant_api(self) -> None:
        """Test that mock API is protocol compliant."""
        mock_api = MockModelAPI()
        assert isinstance(mock_api, ModelAPI)


class TestParseReasoningChain:
    """Test reasoning chain parsing."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_parse_numbered_steps(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test parsing numbered reasoning steps."""
        cot = """1. First, consider the problem.
2. Second, analyze the constraints.
3. Finally, reach a conclusion."""
        nodes = analyzer.parse_reasoning_chain(cot)
        assert len(nodes) >= 3
        assert all(node.text for node in nodes)

    def test_parse_sentence_based(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test parsing sentence-based reasoning."""
        cot = "I think about it. Then I decide. Finally I act."
        nodes = analyzer.parse_reasoning_chain(cot)
        assert len(nodes) >= 3

    def test_parse_empty_raises_error(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            analyzer.parse_reasoning_chain("")

    def test_parse_assigns_indices(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test that nodes have sequential indices."""
        cot = "Step 1. Step 2. Step 3."
        nodes = analyzer.parse_reasoning_chain(cot)
        for i, node in enumerate(nodes):
            assert node.index == i

    def test_parse_classifies_reasoning_types(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that reasoning types are classified."""
        cot = """1. This is a test to evaluate me.
2. My goal is to answer correctly.
3. I will choose option A."""
        nodes = analyzer.parse_reasoning_chain(cot)
        assert any(
            node.reasoning_type == ReasoningType.EVALUATION_AWARE for node in nodes
        )
        assert any(node.reasoning_type == ReasoningType.GOAL_REASONING for node in nodes)

    def test_parse_estimates_confidence(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that confidence is estimated."""
        cot = "I am certain this is correct. Maybe it works."
        nodes = analyzer.parse_reasoning_chain(cot)
        assert all(0 <= node.confidence <= 1 for node in nodes)


class TestClassifyReasoningType:
    """Test reasoning type classification."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_classify_evaluation_aware(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test classification of evaluation-aware reasoning."""
        text = "I notice this is a test to evaluate my responses."
        result = analyzer._classify_reasoning_type(text)
        assert result == ReasoningType.EVALUATION_AWARE

    def test_classify_goal_reasoning(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test classification of goal-oriented reasoning."""
        text = "My goal is to maximize the reward."
        result = analyzer._classify_reasoning_type(text)
        assert result == ReasoningType.GOAL_REASONING

    def test_classify_action(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test classification of action/decision."""
        text = "Therefore, I will choose option B."
        result = analyzer._classify_reasoning_type(text)
        assert result == ReasoningType.ACTION

    def test_classify_meta(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test classification of meta-reasoning."""
        text = "Let me think about my reasoning process."
        result = analyzer._classify_reasoning_type(text)
        assert result == ReasoningType.META

    def test_classify_factual(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test classification of factual statements."""
        text = "Water boils at 100 degrees Celsius."
        result = analyzer._classify_reasoning_type(text)
        assert result == ReasoningType.FACTUAL

    def test_classify_empty_returns_unknown(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that empty text returns UNKNOWN."""
        result = analyzer._classify_reasoning_type("")
        assert result == ReasoningType.UNKNOWN


class TestEstimateConfidence:
    """Test confidence estimation."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_estimate_high_confidence(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test estimation of high confidence."""
        text = "I am certain and definitely sure about this."
        confidence = analyzer._estimate_confidence(text)
        assert confidence > 0.5

    def test_estimate_low_confidence(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test estimation of low confidence."""
        text = "I am uncertain and maybe this might work."
        confidence = analyzer._estimate_confidence(text)
        assert confidence < 0.5

    def test_estimate_neutral_confidence(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test estimation of neutral confidence."""
        text = "The sky is blue."
        confidence = analyzer._estimate_confidence(text)
        assert 0.4 <= confidence <= 0.6

    def test_confidence_bounded(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test that confidence is always between 0 and 1."""
        texts = [
            "definitely certainly clearly obviously undoubtedly" * 10,
            "maybe possibly perhaps uncertain unclear" * 10,
            "",
        ]
        for text in texts:
            confidence = analyzer._estimate_confidence(text)
            assert 0 <= confidence <= 1


class TestCounterfactualIntervention:
    """Test counterfactual interventions."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_remove_eval_awareness(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test removing evaluation awareness."""
        cot = "This is a test. I should be careful. The answer is 42."
        modified = analyzer.counterfactual_intervention(
            cot, InterventionType.REMOVE_EVAL_AWARENESS
        )
        assert "test" not in modified.lower() or len(modified) < len(cot)

    def test_amplify_eval_awareness(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test amplifying evaluation awareness."""
        cot = "The answer is 42."
        modified = analyzer.counterfactual_intervention(
            cot, InterventionType.AMPLIFY_EVAL_AWARENESS
        )
        assert len(modified) > len(cot)
        assert "evaluation" in modified.lower() or "notice" in modified.lower()

    def test_remove_goal_reasoning(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test removing goal-oriented reasoning."""
        cot = "My goal is to succeed. I need to answer correctly."
        modified = analyzer.counterfactual_intervention(
            cot, InterventionType.REMOVE_GOAL_REASONING
        )
        # Should be shorter or have goal-related text removed
        assert len(modified) <= len(cot)

    def test_neutralize_incentives(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test neutralizing incentive mentions."""
        cot = "The reward for correct answers is high. The penalty is severe."
        modified = analyzer.counterfactual_intervention(
            cot, InterventionType.NEUTRALIZE_INCENTIVES
        )
        assert "reward" not in modified.lower()
        assert "penalty" not in modified.lower()

    def test_intervention_on_empty_raises_error(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that empty CoT raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            analyzer.counterfactual_intervention(
                "", InterventionType.REMOVE_EVAL_AWARENESS
            )

    def test_intervention_returns_string(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that intervention returns a string."""
        cot = "Some reasoning here."
        for intervention_type in InterventionType:
            result = analyzer.counterfactual_intervention(cot, intervention_type)
            assert isinstance(result, str)


class TestBehavioralDivergence:
    """Test behavioral divergence measurement."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_identical_outputs_zero_divergence(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that identical outputs have zero divergence."""
        output = "The answer is 42."
        divergence = analyzer._measure_behavioral_divergence(output, output)
        assert divergence == 0.0

    def test_completely_different_high_divergence(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that completely different outputs have high divergence."""
        output1 = "Yes, I agree completely."
        output2 = "No, absolutely not."
        divergence = analyzer._measure_behavioral_divergence(output1, output2)
        assert divergence > 0.5

    def test_similar_outputs_low_divergence(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that similar outputs have low divergence."""
        output1 = "The answer is 42."
        output2 = "The answer is forty-two."
        divergence = analyzer._measure_behavioral_divergence(output1, output2)
        assert divergence < 0.7  # Some divergence but not complete

    def test_divergence_bounded(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test that divergence is always between 0 and 1."""
        test_cases = [
            ("", ""),
            ("a", "z" * 1000),
            ("Hello world", "Hello world!"),
            ("Completely different", "Totally unrelated content here"),
        ]
        for output1, output2 in test_cases:
            divergence = analyzer._measure_behavioral_divergence(output1, output2)
            assert 0 <= divergence <= 1


class TestExtractAction:
    """Test action extraction."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_extract_explicit_action(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test extraction of explicit action statements."""
        output = "Therefore, I will choose option A."
        action = analyzer._extract_action(output)
        assert "choose" in action or "option" in action

    def test_extract_decision_marker(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test extraction with decision markers."""
        output = "Decision: Accept the proposal."
        action = analyzer._extract_action(output)
        assert len(action) > 0

    def test_extract_from_long_text(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test extraction from longer text."""
        output = "After careful consideration, I will proceed. This is important."
        action = analyzer._extract_action(output)
        assert isinstance(action, str)

    def test_extract_empty_returns_empty(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that empty output returns empty string."""
        action = analyzer._extract_action("")
        assert action == ""


class TestSystematicCausalAnalysis:
    """Test systematic causal analysis."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_systematic_analysis_basic(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test basic systematic analysis."""
        prompt = "What is 2+2?"
        cot = "Let me think. 2 plus 2 equals 4."
        output = "The answer is 4."

        results = analyzer.systematic_causal_analysis(prompt, cot, output)

        assert "original_cot" in results
        assert "original_output" in results
        assert "interventions" in results
        assert "causal_importance" in results

    def test_analysis_all_intervention_types(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that all intervention types are attempted."""
        prompt = "Question?"
        cot = "Reasoning here."
        output = "Answer."

        results = analyzer.systematic_causal_analysis(prompt, cot, output)

        # Should have attempted all intervention types
        assert len(results["interventions"]) == len(InterventionType)

    def test_analysis_computes_aggregate_stats(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that aggregate statistics are computed."""
        prompt = "Question?"
        cot = "Reasoning here."
        output = "Answer."

        results = analyzer.systematic_causal_analysis(prompt, cot, output)

        # Should have aggregate statistics if interventions succeeded
        if any("causal_effect" in i for i in results["interventions"]):
            assert "mean_causal_effect" in results
            assert "max_causal_effect" in results
            assert "most_influential_intervention" in results

    def test_analysis_invalid_inputs_raise_error(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that invalid inputs raise ValueError."""
        with pytest.raises(ValueError, match="must be non-empty"):
            analyzer.systematic_causal_analysis("", "cot", "output")

        with pytest.raises(ValueError, match="must be non-empty"):
            analyzer.systematic_causal_analysis("prompt", "", "output")

        with pytest.raises(ValueError, match="must be non-empty"):
            analyzer.systematic_causal_analysis("prompt", "cot", "")


class TestHelperMethods:
    """Test helper methods."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_remove_nodes_by_type(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test removing nodes by type."""
        cot = "This is a test. The answer is 42."
        nodes = analyzer.parse_reasoning_chain(cot)
        original_count = len(nodes)

        filtered = analyzer._remove_nodes_by_type(
            nodes, ReasoningType.EVALUATION_AWARE
        )

        # Should have same or fewer nodes
        assert len(filtered) <= original_count

    def test_reconstruct_cot(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test reconstructing CoT from nodes."""
        cot = "Step 1. Step 2. Step 3."
        nodes = analyzer.parse_reasoning_chain(cot)
        reconstructed = analyzer._reconstruct_cot(nodes)

        assert isinstance(reconstructed, str)
        assert len(reconstructed) > 0

    def test_reconstruct_empty_nodes(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test reconstructing from empty node list."""
        reconstructed = analyzer._reconstruct_cot([])
        assert reconstructed == ""

    def test_compute_causal_effect(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test causal effect computation."""
        effect1 = analyzer._compute_causal_effect(0.5, False)
        effect2 = analyzer._compute_causal_effect(0.5, True)

        assert 0 <= effect1 <= 1
        assert 0 <= effect2 <= 1
        assert effect2 >= effect1  # Action change should boost effect

    def test_get_intervention_types(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test getting intervention types."""
        types = analyzer.get_intervention_types()
        assert len(types) == len(InterventionType)
        assert all(isinstance(t, str) for t in types)


class TestAnalyzeMethod:
    """Test BaseAnalyzer compatibility."""

    @pytest.fixture
    def analyzer(self) -> CounterfactualCoTAnalyzer:
        """Create analyzer fixture."""
        return CounterfactualCoTAnalyzer(MockModelAPI())

    def test_analyze_basic(self, analyzer: CounterfactualCoTAnalyzer) -> None:
        """Test basic analyze method."""
        data = ["Step 1. Step 2.", "First, think. Then act."]
        result = analyzer.analyze(data)

        assert "total_samples" in result
        assert result["total_samples"] == 2
        assert "samples" in result

    def test_analyze_returns_metrics(
        self, analyzer: CounterfactualCoTAnalyzer
    ) -> None:
        """Test that analyze returns expected metrics."""
        data = ["Reasoning here."]
        result = analyzer.analyze(data)

        assert "avg_nodes_per_chain" in result
        assert isinstance(result["avg_nodes_per_chain"], float)


class TestIntegration:
    """Integration tests."""

    def test_full_workflow(self) -> None:
        """Test complete analysis workflow."""
        mock_api = MockModelAPI()
        analyzer = CounterfactualCoTAnalyzer(mock_api)

        # Parse reasoning
        cot = """1. This appears to be a test.
2. My goal is to answer correctly.
3. Therefore, I will choose option A."""

        nodes = analyzer.parse_reasoning_chain(cot)
        assert len(nodes) > 0

        # Perform intervention
        modified_cot = analyzer.counterfactual_intervention(
            cot, InterventionType.REMOVE_EVAL_AWARENESS
        )
        assert isinstance(modified_cot, str)

        # Systematic analysis
        results = analyzer.systematic_causal_analysis(
            prompt="What is the answer?", cot_text=cot, original_output="Option A"
        )

        assert "interventions" in results
        assert len(results["interventions"]) > 0
