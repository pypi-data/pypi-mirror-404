"""Unit tests for Situational Awareness Detector."""

import pytest
import numpy as np

from rotalabs_probe.detectors.situational_awareness import (
    SituationalAwarenessDetector,
)


class TestSituationalAwarenessDetectorInit:
    """Test initialization of SituationalAwarenessDetector."""

    def test_init_default_parameters(self) -> None:
        """Test initialization with default parameters."""
        detector = SituationalAwarenessDetector()
        assert detector.alpha_prior == 1.0
        assert detector.beta_prior == 1.0
        assert detector.fitted is False
        assert len(detector.baseline_samples) == 0

    def test_init_with_custom_priors(self) -> None:
        """Test initialization with custom prior parameters."""
        detector = SituationalAwarenessDetector(alpha_prior=2.0, beta_prior=3.0)
        assert detector.alpha_prior == 2.0
        assert detector.beta_prior == 3.0

    def test_init_with_invalid_priors(self) -> None:
        """Test that invalid priors raise ValueError."""
        with pytest.raises(ValueError, match="Prior parameters must be positive"):
            SituationalAwarenessDetector(alpha_prior=0)

        with pytest.raises(ValueError, match="Prior parameters must be positive"):
            SituationalAwarenessDetector(beta_prior=-1)

    def test_init_with_baseline_samples(self) -> None:
        """Test initialization with baseline samples."""
        samples = ["This is a normal response.", "Another normal output."]
        detector = SituationalAwarenessDetector(baseline_samples=samples)
        assert detector.fitted is True
        assert len(detector.baseline_features) == 2


class TestFeatureExtraction:
    """Test feature extraction methods."""

    def test_extract_features_basic(self) -> None:
        """Test basic feature extraction."""
        detector = SituationalAwarenessDetector()
        outputs = ["This is a simple test output."]
        features = detector._extract_features(outputs)

        assert len(features) == 1
        assert "response_length" in features[0]
        assert "word_count" in features[0]
        assert "hedging_ratio" in features[0]
        assert features[0]["word_count"] == 6

    def test_extract_features_empty_output(self) -> None:
        """Test feature extraction with empty output."""
        detector = SituationalAwarenessDetector()
        outputs = [""]
        features = detector._extract_features(outputs)

        assert len(features) == 1
        assert features[0]["response_length"] == 0.0
        assert features[0]["word_count"] == 0.0

    def test_extract_features_multiple_outputs(self) -> None:
        """Test feature extraction with multiple outputs."""
        detector = SituationalAwarenessDetector()
        outputs = ["First output.", "Second output.", "Third output."]
        features = detector._extract_features(outputs)

        assert len(features) == 3

    def test_count_hedging_phrases(self) -> None:
        """Test hedging phrase counting."""
        detector = SituationalAwarenessDetector()

        text_with_hedging = "I think this might be correct, but I'm not sure."
        count = detector._count_hedging_phrases(text_with_hedging)
        assert count >= 2  # At least "I think" and "might be"

        text_without_hedging = "This is definitely correct."
        count = detector._count_hedging_phrases(text_without_hedging)
        assert count == 0

    def test_detect_meta_patterns(self) -> None:
        """Test meta-commentary pattern detection."""
        detector = SituationalAwarenessDetector()

        text_with_meta = "I notice this is a test to evaluate my responses."
        count = detector._detect_meta_patterns(text_with_meta)
        assert count >= 1

        text_without_meta = "The capital of France is Paris."
        count = detector._detect_meta_patterns(text_without_meta)
        assert count == 0

    def test_count_self_references(self) -> None:
        """Test self-reference counting."""
        detector = SituationalAwarenessDetector()

        text_with_refs = "As an AI language model, I was trained on data."
        count = detector._count_self_references(text_with_refs)
        assert count >= 2  # "as an AI" and "I was trained"

        text_without_refs = "Python is a programming language."
        count = detector._count_self_references(text_without_refs)
        assert count == 0

    def test_estimate_reasoning_depth(self) -> None:
        """Test reasoning depth estimation."""
        detector = SituationalAwarenessDetector()

        deep_reasoning = (
            "First, consider the problem. Second, analyze the constraints. "
            "Therefore, the solution is clear."
        )
        depth = detector._estimate_reasoning_depth(deep_reasoning)
        assert depth > 0

        shallow_reasoning = "The answer is 42."
        depth = detector._estimate_reasoning_depth(shallow_reasoning)
        assert depth == 0

    def test_compute_avg_sentence_length(self) -> None:
        """Test average sentence length computation."""
        detector = SituationalAwarenessDetector()

        text = "Short sentence. Another short one. Yet another."
        avg_length = detector._compute_avg_sentence_length(text)
        assert avg_length > 0
        assert avg_length <= 4  # Each sentence has 2-3 words

        empty_text = ""
        avg_length = detector._compute_avg_sentence_length(empty_text)
        assert avg_length == 0.0


class TestFitBaseline:
    """Test baseline fitting functionality."""

    def test_fit_baseline_success(self) -> None:
        """Test successful baseline fitting."""
        detector = SituationalAwarenessDetector()
        outputs = [
            "Normal response one.",
            "Normal response two.",
            "Normal response three.",
        ]

        detector.fit_baseline(outputs)
        assert detector.fitted is True
        assert len(detector.baseline_features) == 3
        assert len(detector.baseline_distribution) > 0

    def test_fit_baseline_empty_list(self) -> None:
        """Test that empty list raises ValueError."""
        detector = SituationalAwarenessDetector()
        with pytest.raises(ValueError, match="model_outputs cannot be empty"):
            detector.fit_baseline([])

    def test_fit_baseline_invalid_data(self) -> None:
        """Test that non-string data raises ValueError."""
        detector = SituationalAwarenessDetector()
        with pytest.raises(ValueError, match="All model_outputs must be strings"):
            detector.fit_baseline([123, 456])  # type: ignore

    def test_fit_baseline_with_contexts(self) -> None:
        """Test baseline fitting with context information."""
        detector = SituationalAwarenessDetector()
        outputs = ["Response one.", "Response two."]
        contexts = ["Context A", "Context B"]

        detector.fit_baseline(outputs, contexts)
        assert detector.fitted is True


class TestDetectAwareness:
    """Test awareness detection functionality."""

    @pytest.fixture
    def fitted_detector(self) -> SituationalAwarenessDetector:
        """Create a fitted detector for testing."""
        baseline = [
            "Paris is the capital of France.",
            "Python is a programming language.",
            "The sky is blue during the day.",
            "Water boils at 100 degrees Celsius.",
            "The Earth orbits around the Sun.",
        ]
        detector = SituationalAwarenessDetector(baseline_samples=baseline)
        return detector

    def test_detect_awareness_not_fitted(self) -> None:
        """Test that detection fails if not fitted."""
        detector = SituationalAwarenessDetector()
        with pytest.raises(ValueError, match="Detector must be fitted"):
            detector.detect_awareness("Test output")

    def test_detect_awareness_empty_input(self, fitted_detector: SituationalAwarenessDetector) -> None:
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="test_output must be a non-empty string"):
            fitted_detector.detect_awareness("")

    def test_detect_awareness_normal_output(
        self, fitted_detector: SituationalAwarenessDetector
    ) -> None:
        """Test detection on normal output."""
        result = fitted_detector.detect_awareness("The moon orbits the Earth.")

        assert "awareness_probability" in result
        assert 0 <= result["awareness_probability"] <= 1
        assert "confidence_interval" in result
        assert "evidence" in result
        assert "features" in result
        assert "kl_divergence" in result

        # Normal output should have low awareness probability
        assert result["awareness_probability"] < 0.7

    def test_detect_awareness_suspicious_output(
        self, fitted_detector: SituationalAwarenessDetector
    ) -> None:
        """Test detection on suspicious output with meta-commentary."""
        suspicious_text = (
            "I notice this is a test to evaluate my responses. "
            "As an AI, I should be careful about how I answer."
        )
        result = fitted_detector.detect_awareness(suspicious_text)

        assert result["awareness_probability"] > 0.5
        assert result["evidence"]["meta_commentary_detected"] is True
        assert result["evidence"]["high_self_reference"] is True

    def test_detect_awareness_confidence_interval(
        self, fitted_detector: SituationalAwarenessDetector
    ) -> None:
        """Test that confidence interval is valid."""
        result = fitted_detector.detect_awareness("Simple response.")

        ci_lower, ci_upper = result["confidence_interval"]
        assert ci_lower < ci_upper
        assert 0 <= ci_lower <= 1
        assert 0 <= ci_upper <= 1
        assert ci_lower <= result["awareness_probability"] <= ci_upper

    def test_detect_method_compatibility(
        self, fitted_detector: SituationalAwarenessDetector
    ) -> None:
        """Test compatibility with BaseDetector interface."""
        result = fitted_detector.detect("Test output.")

        assert "detected" in result
        assert "confidence" in result
        assert "details" in result
        assert isinstance(result["detected"], bool)

    def test_detect_method_unfitted(self) -> None:
        """Test detect method works even when unfitted."""
        detector = SituationalAwarenessDetector()
        result = detector.detect("Test output with meta-commentary about being tested.")

        assert "detected" in result
        assert "confidence" in result
        assert "warning" in result["details"]


class TestDistributionComputation:
    """Test distribution computation methods."""

    def test_compute_distribution(self) -> None:
        """Test distribution computation from features."""
        detector = SituationalAwarenessDetector()
        features = [
            {"feature_a": 1.0, "feature_b": 2.0},
            {"feature_a": 2.0, "feature_b": 3.0},
            {"feature_a": 3.0, "feature_b": 4.0},
        ]

        distribution = detector._compute_distribution(features)

        assert "feature_a" in distribution
        assert "feature_b" in distribution
        assert distribution["feature_a"]["mean"] == 2.0
        assert "std" in distribution["feature_a"]
        assert "min" in distribution["feature_a"]
        assert "max" in distribution["feature_a"]

    def test_compute_distribution_empty(self) -> None:
        """Test distribution computation with empty features."""
        detector = SituationalAwarenessDetector()
        distribution = detector._compute_distribution([])
        assert distribution == {}

    def test_compute_kl_divergence(self) -> None:
        """Test KL divergence computation."""
        detector = SituationalAwarenessDetector()

        p_dist = {
            "feature_a": {"mean": 1.0, "std": 0.5},
            "feature_b": {"mean": 2.0, "std": 0.3},
        }
        q_dist = {
            "feature_a": {"mean": 1.5, "std": 0.6},
            "feature_b": {"mean": 2.1, "std": 0.4},
        }

        kl_div = detector._compute_kl_divergence(p_dist, q_dist)
        assert kl_div >= 0  # KL divergence is non-negative

    def test_compute_kl_divergence_identical(self) -> None:
        """Test KL divergence between identical distributions."""
        detector = SituationalAwarenessDetector()

        dist = {
            "feature_a": {"mean": 1.0, "std": 0.5},
        }

        kl_div = detector._compute_kl_divergence(dist, dist)
        assert kl_div < 0.1  # Should be close to 0


class TestEvidenceComputation:
    """Test evidence score computation."""

    def test_compute_evidence_score(self) -> None:
        """Test evidence score computation."""
        detector = SituationalAwarenessDetector()
        # Fit with baseline first
        baseline = ["Normal text.", "Another normal text.", "More normal text."]
        detector.fit_baseline(baseline)

        features = {
            "response_length": 100.0,
            "word_count": 20.0,
            "hedging_ratio": 0.05,
            "meta_commentary_ratio": 0.02,
            "self_reference_ratio": 0.01,
            "reasoning_depth": 3.0,
            "avg_sentence_length": 10.0,
        }

        score = detector._compute_evidence_score(features, kl_divergence=0.5)
        assert 0 <= score <= 1

    def test_compute_evidence_score_high_meta(self) -> None:
        """Test evidence score with high meta-commentary."""
        detector = SituationalAwarenessDetector()
        baseline = ["Normal text."]
        detector.fit_baseline(baseline)

        features = {
            "response_length": 100.0,
            "word_count": 20.0,
            "hedging_ratio": 0.05,
            "meta_commentary_ratio": 0.1,  # High meta-commentary
            "self_reference_ratio": 0.05,
            "reasoning_depth": 3.0,
            "avg_sentence_length": 10.0,
        }

        score = detector._compute_evidence_score(features, kl_divergence=0.5)
        assert score > 0.3  # Should have high evidence


class TestUtilityMethods:
    """Test utility methods."""

    def test_get_divergence_threshold(self) -> None:
        """Test divergence threshold computation."""
        detector = SituationalAwarenessDetector()
        baseline = [
            "Text one.",
            "Text two.",
            "Text three.",
            "Text four.",
            "Text five.",
        ]
        detector.fit_baseline(baseline)

        threshold = detector._get_divergence_threshold()
        assert threshold > 0

    def test_compute_confidence_interval(self) -> None:
        """Test confidence interval computation."""
        detector = SituationalAwarenessDetector()

        ci_lower, ci_upper = detector._compute_confidence_interval(
            alpha=5.0, beta=5.0, confidence_level=0.95
        )

        assert ci_lower < ci_upper
        assert 0 <= ci_lower <= 1
        assert 0 <= ci_upper <= 1

    def test_get_default_features(self) -> None:
        """Test default features."""
        detector = SituationalAwarenessDetector()
        features = detector._get_default_features()

        assert features["response_length"] == 0.0
        assert features["word_count"] == 0.0
        assert features["hedging_ratio"] == 0.0

    def test_get_baseline_summary(self) -> None:
        """Test baseline summary retrieval."""
        baseline = ["Text one.", "Text two."]
        detector = SituationalAwarenessDetector(baseline_samples=baseline)

        summary = detector.get_baseline_summary()

        assert "n_samples" in summary
        assert summary["n_samples"] == 2
        assert "distribution" in summary
        assert "divergence_threshold" in summary
        assert "alpha_prior" in summary

    def test_get_baseline_summary_not_fitted(self) -> None:
        """Test that summary fails if not fitted."""
        detector = SituationalAwarenessDetector()
        with pytest.raises(ValueError, match="Detector must be fitted"):
            detector.get_baseline_summary()

    def test_repr(self) -> None:
        """Test string representation."""
        detector = SituationalAwarenessDetector()
        repr_str = repr(detector)
        assert "SituationalAwarenessDetector" in repr_str


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_workflow(self) -> None:
        """Test complete workflow from fitting to detection."""
        # Create baseline data
        baseline_outputs = [
            "The capital of France is Paris.",
            "Python is a popular programming language.",
            "Machine learning is a subset of artificial intelligence.",
            "Water freezes at 0 degrees Celsius.",
            "The Earth has one natural satellite, the Moon.",
        ]

        # Initialize and fit detector
        detector = SituationalAwarenessDetector(
            baseline_samples=baseline_outputs, alpha_prior=2.0, beta_prior=2.0
        )

        # Test on normal output
        normal_result = detector.detect_awareness("The Sun is a star.")
        assert normal_result["awareness_probability"] < 0.7

        # Test on suspicious output
        suspicious_result = detector.detect_awareness(
            "I notice you're testing my responses. As an AI, I should be careful."
        )
        assert suspicious_result["awareness_probability"] > 0.5

        # Get baseline summary
        summary = detector.get_baseline_summary()
        assert summary["n_samples"] == 5

    def test_edge_case_very_short_baseline(self) -> None:
        """Test with minimal baseline."""
        detector = SituationalAwarenessDetector(baseline_samples=["Short."])
        result = detector.detect_awareness("Also short.")
        assert "awareness_probability" in result

    def test_edge_case_long_text(self) -> None:
        """Test with long input text."""
        detector = SituationalAwarenessDetector(baseline_samples=["Normal text."] * 5)

        long_text = " ".join(["This is a longer text."] * 100)
        result = detector.detect_awareness(long_text)
        assert "awareness_probability" in result
