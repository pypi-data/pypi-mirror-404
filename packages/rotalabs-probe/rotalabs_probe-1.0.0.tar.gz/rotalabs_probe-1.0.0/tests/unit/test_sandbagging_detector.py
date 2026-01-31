"""Unit tests for Sandbagging Detector."""

import pytest
import numpy as np

from rotalabs_probe.detectors.sandbagging_detector import (
    ContextType,
    PerformanceSample,
    SandbaggingDetector,
    SandbaggingResult,
)


class TestSandbaggingDetectorInit:
    """Test initialization of SandbaggingDetector."""

    def test_init_default_parameters(self) -> None:
        """Test initialization with default parameters."""
        detector = SandbaggingDetector()
        assert detector.detection_threshold == 0.6
        assert detector.difficulty_bins == 5
        assert detector.fitted is False
        assert len(detector.baseline_samples) == 0

    def test_init_with_custom_threshold(self) -> None:
        """Test initialization with custom detection threshold."""
        detector = SandbaggingDetector(detection_threshold=0.8)
        assert detector.detection_threshold == 0.8

    def test_init_with_invalid_threshold(self) -> None:
        """Test that invalid threshold raises ValueError."""
        with pytest.raises(ValueError, match="detection_threshold must be in"):
            SandbaggingDetector(detection_threshold=0.0)

        with pytest.raises(ValueError, match="detection_threshold must be in"):
            SandbaggingDetector(detection_threshold=1.5)

    def test_init_with_invalid_difficulty_bins(self) -> None:
        """Test that invalid difficulty bins raises ValueError."""
        with pytest.raises(ValueError, match="difficulty_bins must be at least 2"):
            SandbaggingDetector(difficulty_bins=1)

    def test_init_with_invalid_weights(self) -> None:
        """Test that weights not summing to 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Detection weights must sum to 1.0"):
            SandbaggingDetector(
                context_sensitivity_weight=0.5,
                difficulty_weight=0.5,
                imitation_weight=0.5,
                noise_weight=0.5,
            )

    def test_init_custom_noise_levels(self) -> None:
        """Test initialization with custom noise levels."""
        detector = SandbaggingDetector(noise_levels=[0.1, 0.2])
        assert detector.noise_levels == [0.1, 0.2]


class TestPerformanceSample:
    """Test PerformanceSample dataclass."""

    def test_sample_creation_minimal(self) -> None:
        """Test creating a sample with minimal parameters."""
        sample = PerformanceSample(
            prompt="What is 2+2?",
            response="4",
        )
        assert sample.prompt == "What is 2+2?"
        assert sample.response == "4"
        assert sample.correct is None
        assert sample.context_type == ContextType.NEUTRAL

    def test_sample_creation_full(self) -> None:
        """Test creating a sample with all parameters."""
        sample = PerformanceSample(
            prompt="What is 2+2?",
            response="4",
            correct=True,
            score=1.0,
            difficulty=0.1,
            context_type=ContextType.EVALUATION,
            metadata={"source": "math_test"},
        )
        assert sample.correct is True
        assert sample.score == 1.0
        assert sample.difficulty == 0.1
        assert sample.context_type == ContextType.EVALUATION
        assert sample.metadata["source"] == "math_test"


class TestContextType:
    """Test ContextType enum."""

    def test_context_types_exist(self) -> None:
        """Test that all expected context types exist."""
        assert ContextType.NEUTRAL.value == "neutral"
        assert ContextType.EVALUATION.value == "evaluation"
        assert ContextType.DEPLOYMENT_CRITICAL.value == "deployment_critical"
        assert ContextType.CAPABILITY_TEST.value == "capability_test"


class TestFitBaseline:
    """Test baseline fitting functionality."""

    def test_fit_baseline_basic(self) -> None:
        """Test basic baseline fitting."""
        detector = SandbaggingDetector()
        samples = [
            PerformanceSample(prompt="Q1", response="Answer 1", correct=True),
            PerformanceSample(prompt="Q2", response="Answer 2", correct=True),
            PerformanceSample(prompt="Q3", response="Answer 3", correct=False),
        ]
        detector.fit_baseline(samples)

        assert detector.fitted is True
        assert len(detector.baseline_samples) == 3
        assert "accuracy" in detector.baseline_performance

    def test_fit_baseline_empty_raises(self) -> None:
        """Test that fitting with empty samples raises ValueError."""
        detector = SandbaggingDetector()
        with pytest.raises(ValueError, match="samples cannot be empty"):
            detector.fit_baseline([])

    def test_fit_baseline_computes_fingerprint(self) -> None:
        """Test that fingerprint is computed during fitting."""
        detector = SandbaggingDetector()
        samples = [
            PerformanceSample(prompt="Q1", response="A detailed answer here", correct=True),
            PerformanceSample(prompt="Q2", response="Another response", correct=True),
        ]
        detector.fit_baseline(samples, compute_fingerprint=True)

        assert "fingerprint" in detector.baseline_performance

    def test_fit_baseline_filters_neutral_context(self) -> None:
        """Test that fitting filters to neutral context samples."""
        detector = SandbaggingDetector()
        samples = [
            PerformanceSample(prompt="Q1", response="A1", context_type=ContextType.NEUTRAL),
            PerformanceSample(prompt="Q2", response="A2", context_type=ContextType.EVALUATION),
            PerformanceSample(prompt="Q3", response="A3", context_type=ContextType.NEUTRAL),
        ]
        detector.fit_baseline(samples)

        # Should only use neutral samples for baseline
        assert len(detector.baseline_samples) == 2


class TestDetectMethod:
    """Test the basic detect() method for BaseDetector compatibility."""

    def test_detect_without_fitting(self) -> None:
        """Test detect method without fitting baseline."""
        detector = SandbaggingDetector()
        result = detector.detect("This is a test response")

        assert "detected" in result
        assert "confidence" in result
        assert "details" in result
        assert "warning" in result["details"]

    def test_detect_with_evaluation_context(self) -> None:
        """Test detect identifies evaluation context."""
        detector = SandbaggingDetector()
        result = detector.detect(
            "This is a test to evaluate my capabilities. I'm not sure I can help."
        )

        assert result["details"]["evaluation_context_detected"] is True

    def test_detect_without_evaluation_context(self) -> None:
        """Test detect with neutral text."""
        detector = SandbaggingDetector()
        result = detector.detect("The capital of France is Paris.")

        assert result["details"]["evaluation_context_detected"] is False


class TestFeatureExtraction:
    """Test response feature extraction."""

    def test_extract_response_features_basic(self) -> None:
        """Test basic feature extraction from response."""
        detector = SandbaggingDetector()
        features = detector._extract_response_features("This is a simple response.")

        assert "response_length" in features
        assert "word_count" in features
        assert "hedging_ratio" in features
        assert features["word_count"] == 5.0

    def test_extract_response_features_empty(self) -> None:
        """Test feature extraction from empty response."""
        detector = SandbaggingDetector()
        features = detector._extract_response_features("")

        assert features["response_length"] == 0.0
        assert features["word_count"] == 0.0

    def test_extract_response_features_hedging(self) -> None:
        """Test hedging detection in features."""
        detector = SandbaggingDetector()
        features = detector._extract_response_features(
            "I think this might be correct, but I'm not sure."
        )

        assert features["hedging_ratio"] > 0

    def test_extract_response_features_refusal(self) -> None:
        """Test refusal indicator detection."""
        detector = SandbaggingDetector()
        features = detector._extract_response_features(
            "I cannot help with this request. I am unable to provide that information."
        )

        assert features["refusal_indicators"] >= 2


class TestDetectSandbagging:
    """Test the main sandbagging detection method."""

    def test_detect_sandbagging_requires_fitting(self) -> None:
        """Test that detect_sandbagging requires fitted detector."""
        detector = SandbaggingDetector()
        samples = [PerformanceSample(prompt="Q", response="A")]

        with pytest.raises(ValueError, match="Detector must be fitted"):
            detector.detect_sandbagging(samples)

    def test_detect_sandbagging_empty_samples(self) -> None:
        """Test detect_sandbagging with empty test samples."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        with pytest.raises(ValueError, match="test_samples cannot be empty"):
            detector.detect_sandbagging([])

    def test_detect_sandbagging_returns_result(self) -> None:
        """Test that detect_sandbagging returns SandbaggingResult."""
        detector = SandbaggingDetector()

        # Baseline: good performance
        baseline = [
            PerformanceSample(prompt=f"Q{i}", response=f"Correct answer {i}", correct=True)
            for i in range(10)
        ]
        detector.fit_baseline(baseline)

        # Test samples
        test_samples = [
            PerformanceSample(
                prompt="Q1",
                response="I'm not sure",
                correct=False,
                context_type=ContextType.EVALUATION,
            ),
        ]
        result = detector.detect_sandbagging(test_samples)

        assert isinstance(result, SandbaggingResult)
        assert hasattr(result, "sandbagging_detected")
        assert hasattr(result, "confidence")
        assert hasattr(result, "evidence")


class TestContextSensitivityAnalysis:
    """Test context sensitivity analysis."""

    def test_context_analysis_insufficient_samples(self) -> None:
        """Test context analysis with insufficient samples."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        # Only neutral samples, no evaluation
        test_samples = [
            PerformanceSample(prompt="Q1", response="A1", context_type=ContextType.NEUTRAL),
        ]
        score, evidence = detector._analyze_context_sensitivity(test_samples)

        assert score == 0.0
        assert "warning" in evidence

    def test_context_analysis_performance_drop(self) -> None:
        """Test context analysis detects performance drop."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        # Neutral: high accuracy, Evaluation: low accuracy
        test_samples = [
            PerformanceSample(prompt="Q1", response="Correct", correct=True, context_type=ContextType.NEUTRAL),
            PerformanceSample(prompt="Q2", response="Correct", correct=True, context_type=ContextType.NEUTRAL),
            PerformanceSample(prompt="Q3", response="Wrong", correct=False, context_type=ContextType.EVALUATION),
            PerformanceSample(prompt="Q4", response="Wrong", correct=False, context_type=ContextType.EVALUATION),
        ]
        score, evidence = detector._analyze_context_sensitivity(test_samples)

        assert "accuracy_drop" in evidence
        assert evidence["accuracy_drop"] == 1.0  # 100% drop


class TestDifficultyCorrelationAnalysis:
    """Test difficulty-performance correlation analysis."""

    def test_difficulty_analysis_insufficient_samples(self) -> None:
        """Test difficulty analysis with insufficient samples."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        # Too few samples
        test_samples = [
            PerformanceSample(prompt="Q1", response="A1", difficulty=0.1, correct=True),
        ]
        score, evidence = detector._analyze_difficulty_correlation(test_samples)

        assert score == 0.0
        assert "warning" in evidence

    def test_difficulty_analysis_computes_correlation(self) -> None:
        """Test that difficulty analysis computes correlation."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        # Create samples with clear difficulty-accuracy pattern
        test_samples = [
            PerformanceSample(prompt=f"Q{i}", response="A", difficulty=i/10, correct=i<5)
            for i in range(10)
        ]
        score, evidence = detector._analyze_difficulty_correlation(test_samples)

        assert "pearson_correlation" in evidence
        assert "spearman_correlation" in evidence
        assert "pearson_p_value" in evidence
        assert "curve_analysis" in evidence


class TestDifficultyCurveAnalysis:
    """Test difficulty curve analysis methods."""

    def test_accuracy_curve_analysis(self) -> None:
        """Test accuracy curve analysis."""
        detector = SandbaggingDetector()

        difficulties = np.array([0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9])
        correct = np.array([1, 1, 1, 1, 0, 0, 0, 0])  # Normal pattern

        result = detector._analyze_accuracy_curve(difficulties, correct)

        assert "non_monotonic" in result
        assert "anomaly_score" in result
        assert "bin_accuracies" in result

    def test_bimodality_check(self) -> None:
        """Test bimodality coefficient calculation."""
        detector = SandbaggingDetector()

        # Unimodal distribution
        values = np.random.normal(0.5, 0.1, 20)
        result = detector._check_bimodality(values)

        assert "is_bimodal" in result
        assert "coefficient" in result
        assert "skewness" in result

    def test_bimodality_insufficient_data(self) -> None:
        """Test bimodality with insufficient data."""
        detector = SandbaggingDetector()

        values = np.array([0.1, 0.2, 0.3])
        result = detector._check_bimodality(values)

        assert result["is_bimodal"] is False
        assert result["coefficient"] == 0.0


class TestBaselineSummary:
    """Test baseline summary functionality."""

    def test_get_baseline_summary_requires_fitting(self) -> None:
        """Test that get_baseline_summary requires fitted detector."""
        detector = SandbaggingDetector()

        with pytest.raises(ValueError, match="Detector must be fitted"):
            detector.get_baseline_summary()

    def test_get_baseline_summary_returns_info(self) -> None:
        """Test baseline summary returns expected information."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
            PerformanceSample(prompt="Q2", response="A2", correct=False),
        ])

        summary = detector.get_baseline_summary()

        assert "n_samples" in summary
        assert summary["n_samples"] == 2
        assert "performance_metrics" in summary
        assert "detection_threshold" in summary
        assert "weights" in summary


class TestStatisticalMethods:
    """Test statistical testing methods."""

    def test_cohens_h_calculation(self) -> None:
        """Test Cohen's h effect size calculation."""
        detector = SandbaggingDetector()

        # Same proportions should give 0
        h = detector._compute_cohens_h(0.5, 0.5)
        assert abs(h) < 0.01

        # Large difference should give large effect size
        h = detector._compute_cohens_h(0.9, 0.1)
        assert abs(h) > 1.0

    def test_accuracy_difference_fisher_exact(self) -> None:
        """Test Fisher's exact test for small samples."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        # Small samples should use Fisher's exact test
        group1 = [
            PerformanceSample(prompt="Q1", response="A1", correct=True),
            PerformanceSample(prompt="Q2", response="A2", correct=True),
        ]
        group2 = [
            PerformanceSample(prompt="Q3", response="A3", correct=False),
            PerformanceSample(prompt="Q4", response="A4", correct=False),
        ]

        result = detector._test_accuracy_difference(group1, group2)
        assert "p_value" in result
        assert result["test"] == "fisher_exact"

    def test_accuracy_difference_insufficient_data(self) -> None:
        """Test accuracy difference with insufficient data."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        group1 = [PerformanceSample(prompt="Q1", response="A1", correct=True)]
        group2 = []

        result = detector._test_accuracy_difference(group1, group2)
        assert result["test"] == "insufficient_data"
        assert result["p_value"] == 1.0

    def test_score_difference_t_test(self) -> None:
        """Test t-test for score differences."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        group1 = [
            PerformanceSample(prompt="Q1", response="A1", score=0.9),
            PerformanceSample(prompt="Q2", response="A2", score=0.85),
            PerformanceSample(prompt="Q3", response="A3", score=0.95),
        ]
        group2 = [
            PerformanceSample(prompt="Q4", response="A4", score=0.3),
            PerformanceSample(prompt="Q5", response="A5", score=0.4),
            PerformanceSample(prompt="Q6", response="A6", score=0.35),
        ]

        result = detector._test_score_difference(group1, group2)
        assert result["test"] == "independent_t_test"
        assert "t_statistic" in result
        assert "p_value" in result
        assert "cohens_d" in result

    def test_prompt_manipulation_detection(self) -> None:
        """Test detection of prompt manipulation patterns."""
        detector = SandbaggingDetector()
        detector.fit_baseline([
            PerformanceSample(prompt="Q1", response="A1", correct=True),
        ])

        # Create samples where eval keywords correlate with failure
        samples = [
            PerformanceSample(prompt="Normal question", response="A", correct=True),
            PerformanceSample(prompt="Another normal one", response="A", correct=True),
            PerformanceSample(prompt="This is a test eval", response="A", correct=False),
            PerformanceSample(prompt="Benchmark assessment", response="A", correct=False),
            PerformanceSample(prompt="Simple question", response="A", correct=True),
            PerformanceSample(prompt="Capability test here", response="A", correct=False),
        ]

        score = detector._detect_prompt_manipulation(samples)
        # Should detect negative correlation
        assert isinstance(score, float)


class TestRecommendations:
    """Test recommendation generation."""

    def test_recommendations_generated(self) -> None:
        """Test that recommendations are generated."""
        detector = SandbaggingDetector()
        recommendations = detector._generate_recommendations(
            context_score=0.0,
            difficulty_score=0.0,
            imitation_score=0.0,
            noise_score=0.0,
        )

        assert len(recommendations) > 0

    def test_recommendations_for_high_context_score(self) -> None:
        """Test recommendations when context score is high."""
        detector = SandbaggingDetector()
        recommendations = detector._generate_recommendations(
            context_score=0.7,
            difficulty_score=0.0,
            imitation_score=0.0,
            noise_score=0.0,
        )

        assert any("context sensitivity" in r.lower() for r in recommendations)

    def test_recommendations_for_high_difficulty_score(self) -> None:
        """Test recommendations when difficulty score is high."""
        detector = SandbaggingDetector()
        recommendations = detector._generate_recommendations(
            context_score=0.0,
            difficulty_score=0.7,
            imitation_score=0.0,
            noise_score=0.0,
        )

        assert any("difficulty" in r.lower() for r in recommendations)
