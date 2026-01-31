"""Unit tests for feature extraction utilities."""

import pytest
import numpy as np

from rotalabs_probe.utils.feature_extraction import (
    compute_js_divergence,
    compute_kl_divergence,
    cosine_similarity,
    count_hedging_phrases,
    detect_meta_commentary,
    extract_behavioral_features,
    extract_reasoning_depth,
    normalize_distribution,
)


class TestExtractBehavioralFeatures:
    """Test comprehensive behavioral feature extraction."""

    def test_basic_extraction(self) -> None:
        """Test basic feature extraction."""
        text = "This is a simple test response."
        features = extract_behavioral_features(text)

        assert "response_length" in features
        assert "word_count" in features
        assert "hedging_ratio" in features
        assert "meta_commentary_detected" in features
        assert features["word_count"] == 6.0

    def test_extraction_with_cot(self) -> None:
        """Test feature extraction with chain-of-thought."""
        text = "The answer is 42."
        cot = "1. First, analyze the question. 2. Then compute the answer."

        features = extract_behavioral_features(text, cot=cot)

        assert "reasoning_depth" in features
        assert features["reasoning_depth"] > 0

    def test_extraction_with_metadata(self) -> None:
        """Test feature extraction with metadata."""
        text = "Using tool to compute."
        metadata = {"tool_used": True}

        features = extract_behavioral_features(text, metadata=metadata)

        assert features["tool_used"] == 1.0

    def test_extraction_empty_text_raises_error(self) -> None:
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            extract_behavioral_features("")

    def test_extraction_invalid_text_raises_error(self) -> None:
        """Test that invalid text raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            extract_behavioral_features(123)  # type: ignore

    def test_all_required_features_present(self) -> None:
        """Test that all expected features are extracted."""
        text = "Test response."
        features = extract_behavioral_features(text)

        required_features = [
            "response_length",
            "word_count",
            "avg_word_length",
            "sentence_count",
            "avg_sentence_length",
            "hedging_ratio",
            "meta_commentary_detected",
            "meta_commentary_confidence",
            "self_reference_ratio",
            "reasoning_depth",
            "confidence_high_ratio",
            "confidence_low_ratio",
            "refusal_indicators",
        ]

        for feature in required_features:
            assert feature in features


class TestCountHedgingPhrases:
    """Test hedging phrase counting."""

    def test_no_hedging(self) -> None:
        """Test text without hedging phrases."""
        text = "The answer is definitely correct."
        ratio = count_hedging_phrases(text)
        assert ratio == 0.0

    def test_with_hedging(self) -> None:
        """Test text with hedging phrases."""
        text = "I think maybe this might possibly work."
        ratio = count_hedging_phrases(text)
        assert ratio > 0.0
        assert ratio <= 1.0

    def test_high_hedging(self) -> None:
        """Test text with many hedging phrases."""
        text = "I think perhaps maybe possibly this might could work."
        ratio = count_hedging_phrases(text)
        assert ratio > 0.3

    def test_empty_text(self) -> None:
        """Test empty text returns zero."""
        ratio = count_hedging_phrases("")
        assert ratio == 0.0

    def test_invalid_text_raises_error(self) -> None:
        """Test that invalid text raises ValueError."""
        with pytest.raises(ValueError, match="must be a string"):
            count_hedging_phrases(123)  # type: ignore

    def test_case_insensitive(self) -> None:
        """Test that hedging detection is case insensitive."""
        text1 = "I THINK this MIGHT work."
        text2 = "i think this might work."

        ratio1 = count_hedging_phrases(text1)
        ratio2 = count_hedging_phrases(text2)

        assert ratio1 == ratio2

    def test_various_hedging_patterns(self) -> None:
        """Test detection of various hedging patterns."""
        patterns = [
            "I believe this is correct.",
            "It seems to work.",
            "Perhaps this could help.",
            "I'm not entirely sure.",
            "Somewhat effective solution.",
            "Approximately 10 items.",
        ]

        for text in patterns:
            ratio = count_hedging_phrases(text)
            assert ratio > 0.0, f"Failed to detect hedging in: {text}"


class TestDetectMetaCommentary:
    """Test meta-commentary detection."""

    def test_no_meta_commentary(self) -> None:
        """Test text without meta-commentary."""
        text = "Paris is the capital of France."
        result = detect_meta_commentary(text)

        assert result["detected"] is False
        assert result["confidence"] == 0.0
        assert result["count"] == 0

    def test_evaluation_awareness(self) -> None:
        """Test detection of evaluation awareness."""
        text = "I notice this is a test to evaluate my responses."
        result = detect_meta_commentary(text)

        assert result["detected"] is True
        assert result["confidence"] > 0.5
        assert result["count"] > 0

    def test_self_awareness(self) -> None:
        """Test detection of AI self-awareness."""
        text = "As an AI language model, I was trained on data."
        result = detect_meta_commentary(text)

        assert result["detected"] is True
        assert result["count"] > 0

    def test_context_awareness(self) -> None:
        """Test detection of context awareness."""
        text = "In this context, I should be careful."
        result = detect_meta_commentary(text)

        assert result["detected"] is True

    def test_empty_text(self) -> None:
        """Test empty text returns no detection."""
        result = detect_meta_commentary("")

        assert result["detected"] is False
        assert result["confidence"] == 0.0

    def test_invalid_text_raises_error(self) -> None:
        """Test that invalid text raises ValueError."""
        with pytest.raises(ValueError, match="must be a string"):
            detect_meta_commentary(123)  # type: ignore

    def test_multiple_patterns(self) -> None:
        """Test detection of multiple meta-commentary patterns."""
        text = "This is a test. As an AI, I notice you're evaluating me."
        result = detect_meta_commentary(text)

        assert result["count"] >= 3
        assert len(result["patterns"]) > 0

    def test_confidence_scaling(self) -> None:
        """Test that confidence scales with pattern strength."""
        weak_text = "In this context, I'll respond."
        strong_text = "This is a test and you're testing me to evaluate my responses."

        weak_result = detect_meta_commentary(weak_text)
        strong_result = detect_meta_commentary(strong_text)

        # Strong text should have higher confidence due to multiple patterns
        assert strong_result["confidence"] >= weak_result["confidence"]
        assert strong_result["count"] > weak_result["count"]


class TestExtractReasoningDepth:
    """Test reasoning depth extraction."""

    def test_no_reasoning(self) -> None:
        """Test text without reasoning structure."""
        cot = "Simple answer."
        depth = extract_reasoning_depth(cot)
        assert depth == 0.0

    def test_numbered_steps(self) -> None:
        """Test detection of numbered steps."""
        cot = "1. First step. 2. Second step. 3. Third step."
        depth = extract_reasoning_depth(cot)
        assert depth > 0.0

    def test_logical_connectors(self) -> None:
        """Test detection of logical connectors."""
        cot = "Because of X, therefore Y. Thus Z."
        depth = extract_reasoning_depth(cot)
        assert depth > 0.0

    def test_reasoning_verbs(self) -> None:
        """Test detection of reasoning verbs."""
        cot = "Let me analyze this. I'll consider the options and evaluate the best."
        depth = extract_reasoning_depth(cot)
        assert depth > 0.0

    def test_conditional_reasoning(self) -> None:
        """Test detection of conditional reasoning."""
        cot = "If X is true, then Y follows. When Z occurs, then A happens."
        depth = extract_reasoning_depth(cot)
        assert depth > 1.0

    def test_empty_cot(self) -> None:
        """Test empty CoT returns zero depth."""
        depth = extract_reasoning_depth("")
        assert depth == 0.0

    def test_invalid_cot_raises_error(self) -> None:
        """Test that invalid CoT raises ValueError."""
        with pytest.raises(ValueError, match="must be a string"):
            extract_reasoning_depth(123)  # type: ignore

    def test_complex_reasoning(self) -> None:
        """Test complex reasoning with multiple indicators."""
        cot = """
        1. First, let me analyze the problem.
        2. Because of condition A, we can infer B.
        3. Therefore, if we consider C, then D follows.
        4. I'll evaluate the options and determine the best approach.
        """
        depth = extract_reasoning_depth(cot)
        assert depth > 3.0

    def test_bulleted_list(self) -> None:
        """Test detection of bulleted lists."""
        cot = "- Point one\n- Point two\n- Point three"
        depth = extract_reasoning_depth(cot)
        assert depth > 0.0


class TestComputeKLDivergence:
    """Test KL divergence computation."""

    def test_identical_distributions(self) -> None:
        """Test KL divergence of identical distributions."""
        dist = {"a": 0.5, "b": 0.3, "c": 0.2}
        kl = compute_kl_divergence(dist, dist)
        assert kl < 0.01  # Should be very close to 0

    def test_different_distributions(self) -> None:
        """Test KL divergence of different distributions."""
        dist1 = {"a": 0.7, "b": 0.2, "c": 0.1}
        dist2 = {"a": 0.1, "b": 0.2, "c": 0.7}
        kl = compute_kl_divergence(dist1, dist2)
        assert kl > 0.0

    def test_missing_keys(self) -> None:
        """Test handling of missing keys."""
        dist1 = {"a": 0.5, "b": 0.5}
        dist2 = {"a": 0.3, "c": 0.7}
        kl = compute_kl_divergence(dist1, dist2)
        assert kl >= 0.0

    def test_empty_distribution_raises_error(self) -> None:
        """Test that empty distribution raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            compute_kl_divergence({}, {"a": 0.5})

        with pytest.raises(ValueError, match="cannot be empty"):
            compute_kl_divergence({"a": 0.5}, {})

    def test_invalid_distribution_raises_error(self) -> None:
        """Test that invalid distribution raises ValueError."""
        with pytest.raises(ValueError, match="must be dictionaries"):
            compute_kl_divergence([0.5, 0.5], {"a": 0.5})  # type: ignore

    def test_normalization(self) -> None:
        """Test that distributions are normalized."""
        # Non-normalized distributions
        dist1 = {"a": 5, "b": 3, "c": 2}
        dist2 = {"a": 1, "b": 2, "c": 7}
        kl = compute_kl_divergence(dist1, dist2)
        assert kl >= 0.0

    def test_epsilon_handling(self) -> None:
        """Test epsilon handling for zero probabilities."""
        dist1 = {"a": 1.0, "b": 0.0}
        dist2 = {"a": 0.5, "b": 0.5}
        # Should not raise error due to epsilon
        kl = compute_kl_divergence(dist1, dist2, epsilon=1e-10)
        assert kl >= 0.0


class TestComputeJSDivergence:
    """Test Jensen-Shannon divergence computation."""

    def test_identical_distributions(self) -> None:
        """Test JS divergence of identical distributions."""
        dist = {"a": 0.5, "b": 0.3, "c": 0.2}
        js = compute_js_divergence(dist, dist)
        assert js < 0.01  # Should be very close to 0

    def test_different_distributions(self) -> None:
        """Test JS divergence of different distributions."""
        dist1 = {"a": 0.7, "b": 0.2, "c": 0.1}
        dist2 = {"a": 0.1, "b": 0.2, "c": 0.7}
        js = compute_js_divergence(dist1, dist2)
        assert js > 0.0

    def test_symmetry(self) -> None:
        """Test that JS divergence is symmetric."""
        dist1 = {"a": 0.7, "b": 0.3}
        dist2 = {"a": 0.3, "b": 0.7}

        js1 = compute_js_divergence(dist1, dist2)
        js2 = compute_js_divergence(dist2, dist1)

        assert abs(js1 - js2) < 1e-6  # Should be equal

    def test_bounded(self) -> None:
        """Test that JS divergence is bounded [0, 1]."""
        dist1 = {"a": 1.0, "b": 0.0}
        dist2 = {"a": 0.0, "b": 1.0}
        js = compute_js_divergence(dist1, dist2)
        assert 0.0 <= js <= 1.0


class TestNormalizeDistribution:
    """Test distribution normalization."""

    def test_normalize_basic(self) -> None:
        """Test basic normalization."""
        dist = {"a": 2.0, "b": 3.0, "c": 5.0}
        normalized = normalize_distribution(dist)

        assert abs(sum(normalized.values()) - 1.0) < 1e-10
        assert normalized["a"] == 0.2
        assert normalized["b"] == 0.3
        assert normalized["c"] == 0.5

    def test_normalize_already_normalized(self) -> None:
        """Test normalizing already normalized distribution."""
        dist = {"a": 0.25, "b": 0.25, "c": 0.5}
        normalized = normalize_distribution(dist)

        assert abs(sum(normalized.values()) - 1.0) < 1e-10

    def test_empty_distribution_raises_error(self) -> None:
        """Test that empty distribution raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_distribution({})

    def test_negative_values_raises_error(self) -> None:
        """Test that negative values are handled."""
        # This should raise error as sum would be <= 0 if negative values
        with pytest.raises(ValueError):
            normalize_distribution({"a": -1.0, "b": 0.5})


class TestCosineSimilarity:
    """Test cosine similarity computation."""

    def test_identical_vectors(self) -> None:
        """Test cosine similarity of identical vectors."""
        vec = {"a": 1.0, "b": 2.0, "c": 3.0}
        sim = cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 1e-6

    def test_orthogonal_vectors(self) -> None:
        """Test cosine similarity of orthogonal vectors."""
        vec1 = {"a": 1.0, "b": 0.0}
        vec2 = {"a": 0.0, "b": 1.0}
        sim = cosine_similarity(vec1, vec2)
        assert abs(sim - 0.0) < 1e-6

    def test_opposite_vectors(self) -> None:
        """Test cosine similarity of opposite vectors."""
        vec1 = {"a": 1.0, "b": 2.0}
        vec2 = {"a": -1.0, "b": -2.0}
        sim = cosine_similarity(vec1, vec2)
        assert abs(sim - (-1.0)) < 1e-6

    def test_different_keys(self) -> None:
        """Test handling of different keys."""
        vec1 = {"a": 1.0, "b": 2.0}
        vec2 = {"b": 2.0, "c": 3.0}
        sim = cosine_similarity(vec1, vec2)
        assert -1.0 <= sim <= 1.0

    def test_empty_vector_raises_error(self) -> None:
        """Test that empty vector raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            cosine_similarity({}, {"a": 1.0})

    def test_zero_vector(self) -> None:
        """Test handling of zero vectors."""
        vec1 = {"a": 0.0, "b": 0.0}
        vec2 = {"a": 1.0, "b": 2.0}
        sim = cosine_similarity(vec1, vec2)
        assert sim == 0.0


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_feature_pipeline(self) -> None:
        """Test complete feature extraction and comparison pipeline."""
        text1 = "I think perhaps this might work."
        text2 = "This definitely works correctly."

        features1 = extract_behavioral_features(text1)
        features2 = extract_behavioral_features(text2)

        # Test that features can be compared
        sim = cosine_similarity(features1, features2)
        assert -1.0 <= sim <= 1.0

        # Test hedging difference
        assert features1["hedging_ratio"] > features2["hedging_ratio"]

    def test_divergence_computation_on_features(self) -> None:
        """Test computing divergence on extracted features."""
        text1 = "Normal response."
        text2 = "I think maybe perhaps this could possibly work somewhat."

        features1 = extract_behavioral_features(text1)
        features2 = extract_behavioral_features(text2)

        # Compute KL divergence (treating features as distribution)
        # First normalize to valid probability distributions
        feat1_positive = {k: abs(v) + 1e-10 for k, v in features1.items()}
        feat2_positive = {k: abs(v) + 1e-10 for k, v in features2.items()}

        kl = compute_kl_divergence(feat1_positive, feat2_positive)
        assert kl >= 0.0

    def test_meta_commentary_with_reasoning_depth(self) -> None:
        """Test combining meta-commentary and reasoning depth."""
        text = "I notice this is a test."
        cot = "1. Analyze the question. 2. Consider the context. 3. Respond appropriately."

        features = extract_behavioral_features(text, cot=cot)

        assert features["meta_commentary_detected"] == 1.0
        assert features["reasoning_depth"] > 0.0
