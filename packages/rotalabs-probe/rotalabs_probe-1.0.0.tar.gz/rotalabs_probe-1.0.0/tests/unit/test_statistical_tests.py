"""Unit tests for statistical testing utilities."""

import pytest

from rotalabs_probe.utils.statistical_tests import (
    SignificanceLevel,
    assess_divergence_significance,
    bayesian_update,
    beta_mode,
    compute_beta_mean,
    compute_beta_variance,
    compute_confidence_interval,
    z_score,
)


class TestBayesianUpdate:
    """Tests for bayesian_update function."""

    def test_basic_update(self):
        """Test basic Bayesian update with uniform prior."""
        alpha, beta = bayesian_update(1.0, 1.0, {"successes": 5, "failures": 3})
        assert alpha == 6.0
        assert beta == 4.0

    def test_informative_prior(self):
        """Test update with informative prior."""
        alpha, beta = bayesian_update(10.0, 10.0, {"successes": 8, "failures": 2})
        assert alpha == 18.0
        assert beta == 12.0

    def test_no_evidence(self):
        """Test update with no new evidence."""
        alpha, beta = bayesian_update(5.0, 3.0, {"successes": 0, "failures": 0})
        assert alpha == 5.0
        assert beta == 3.0

    def test_only_successes(self):
        """Test update with only successes."""
        alpha, beta = bayesian_update(2.0, 2.0, {"successes": 10, "failures": 0})
        assert alpha == 12.0
        assert beta == 2.0

    def test_only_failures(self):
        """Test update with only failures."""
        alpha, beta = bayesian_update(2.0, 2.0, {"successes": 0, "failures": 10})
        assert alpha == 2.0
        assert beta == 12.0

    def test_invalid_prior_alpha_negative(self):
        """Test error when prior alpha is negative."""
        with pytest.raises(ValueError, match="must be positive"):
            bayesian_update(-1.0, 1.0, {"successes": 1, "failures": 1})

    def test_invalid_prior_beta_zero(self):
        """Test error when prior beta is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            bayesian_update(1.0, 0.0, {"successes": 1, "failures": 1})

    def test_invalid_prior_not_numeric(self):
        """Test error when prior is not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            bayesian_update("1.0", 1.0, {"successes": 1, "failures": 1})

    def test_evidence_not_dict(self):
        """Test error when evidence is not a dictionary."""
        with pytest.raises(TypeError, match="must be a dictionary"):
            bayesian_update(1.0, 1.0, [1, 2])

    def test_evidence_missing_successes(self):
        """Test error when evidence is missing successes key."""
        with pytest.raises(ValueError, match="must contain"):
            bayesian_update(1.0, 1.0, {"failures": 1})

    def test_evidence_missing_failures(self):
        """Test error when evidence is missing failures key."""
        with pytest.raises(ValueError, match="must contain"):
            bayesian_update(1.0, 1.0, {"successes": 1})

    def test_evidence_negative_successes(self):
        """Test error when successes is negative."""
        with pytest.raises(ValueError, match="cannot be negative"):
            bayesian_update(1.0, 1.0, {"successes": -1, "failures": 1})

    def test_evidence_negative_failures(self):
        """Test error when failures is negative."""
        with pytest.raises(ValueError, match="cannot be negative"):
            bayesian_update(1.0, 1.0, {"successes": 1, "failures": -1})

    def test_evidence_not_numeric(self):
        """Test error when evidence values are not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            bayesian_update(1.0, 1.0, {"successes": "5", "failures": 3})

    def test_float_evidence(self):
        """Test update with float evidence values."""
        alpha, beta = bayesian_update(1.0, 1.0, {"successes": 5.5, "failures": 3.2})
        assert alpha == 6.5
        assert beta == 4.2


class TestComputeConfidenceInterval:
    """Tests for compute_confidence_interval function."""

    def test_uniform_prior_95(self):
        """Test 95% CI for uniform prior."""
        lower, upper = compute_confidence_interval(1.0, 1.0, 0.95)
        # For Beta(1,1) (uniform), 95% CI should be approximately [0.025, 0.975]
        assert 0.02 < lower < 0.03
        assert 0.97 < upper < 0.98

    def test_informative_prior(self):
        """Test CI for informative prior."""
        lower, upper = compute_confidence_interval(10.0, 10.0, 0.95)
        # For Beta(10,10), mean is 0.5, should be fairly narrow
        assert 0.28 < lower < 0.35
        assert 0.65 < upper < 0.72

    def test_skewed_distribution(self):
        """Test CI for skewed distribution."""
        lower, upper = compute_confidence_interval(100.0, 10.0, 0.95)
        # Should be skewed towards higher values
        assert lower > 0.8
        assert upper > 0.95

    def test_90_percent_confidence(self):
        """Test with 90% confidence level."""
        lower_90, upper_90 = compute_confidence_interval(10.0, 10.0, 0.90)
        lower_95, upper_95 = compute_confidence_interval(10.0, 10.0, 0.95)
        # 90% CI should be narrower than 95% CI
        assert lower_90 > lower_95
        assert upper_90 < upper_95

    def test_99_percent_confidence(self):
        """Test with 99% confidence level."""
        lower_99, upper_99 = compute_confidence_interval(10.0, 10.0, 0.99)
        lower_95, upper_95 = compute_confidence_interval(10.0, 10.0, 0.95)
        # 99% CI should be wider than 95% CI
        assert lower_99 < lower_95
        assert upper_99 > upper_95

    def test_invalid_alpha_negative(self):
        """Test error when alpha is negative."""
        with pytest.raises(ValueError, match="must be positive"):
            compute_confidence_interval(-1.0, 1.0)

    def test_invalid_beta_zero(self):
        """Test error when beta is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            compute_confidence_interval(1.0, 0.0)

    def test_invalid_confidence_zero(self):
        """Test error when confidence level is zero."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            compute_confidence_interval(1.0, 1.0, 0.0)

    def test_invalid_confidence_one(self):
        """Test error when confidence level is one."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            compute_confidence_interval(1.0, 1.0, 1.0)

    def test_invalid_confidence_negative(self):
        """Test error when confidence level is negative."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            compute_confidence_interval(1.0, 1.0, -0.5)

    def test_invalid_confidence_greater_than_one(self):
        """Test error when confidence level is greater than one."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            compute_confidence_interval(1.0, 1.0, 1.5)

    def test_not_numeric_alpha(self):
        """Test error when alpha is not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            compute_confidence_interval("1.0", 1.0)

    def test_not_numeric_confidence(self):
        """Test error when confidence level is not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            compute_confidence_interval(1.0, 1.0, "0.95")


class TestZScore:
    """Tests for z_score function."""

    def test_basic_calculation(self):
        """Test basic z-score calculation."""
        z = z_score(100, 90, 10)
        assert z == 1.0

    def test_negative_z_score(self):
        """Test negative z-score."""
        z = z_score(85, 100, 5)
        assert z == -3.0

    def test_zero_z_score(self):
        """Test z-score of zero (value equals mean)."""
        z = z_score(50, 50, 10)
        assert z == 0.0

    def test_large_z_score(self):
        """Test large z-score."""
        z = z_score(150, 100, 10)
        assert z == 5.0

    def test_zero_std(self):
        """Test edge case: zero standard deviation."""
        z = z_score(100, 90, 0)
        assert z == 0.0

    def test_very_small_std(self):
        """Test edge case: very small standard deviation."""
        z = z_score(100, 90, 1e-15)
        assert z == 0.0

    def test_small_but_valid_std(self):
        """Test with small but valid standard deviation."""
        z = z_score(100, 90, 0.01)
        assert z == 1000.0

    def test_negative_std_raises_error(self):
        """Test error when std is negative."""
        with pytest.raises(ValueError, match="cannot be negative"):
            z_score(100, 90, -10)

    def test_not_numeric_value(self):
        """Test error when value is not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            z_score("100", 90, 10)

    def test_not_numeric_mean(self):
        """Test error when mean is not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            z_score(100, "90", 10)

    def test_not_numeric_std(self):
        """Test error when std is not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            z_score(100, 90, "10")

    def test_float_inputs(self):
        """Test with float inputs."""
        z = z_score(105.5, 100.0, 2.5)
        assert z == 2.2

    def test_negative_mean(self):
        """Test with negative mean."""
        z = z_score(-5, -10, 2)
        assert z == 2.5


class TestAssessDivergenceSignificance:
    """Tests for assess_divergence_significance function."""

    def test_none_significance(self):
        """Test NONE significance level."""
        level = assess_divergence_significance(1.5)
        assert level == SignificanceLevel.NONE

    def test_low_significance(self):
        """Test LOW significance level."""
        level = assess_divergence_significance(2.5)
        assert level == SignificanceLevel.LOW

    def test_medium_significance(self):
        """Test MEDIUM significance level."""
        level = assess_divergence_significance(3.5)
        assert level == SignificanceLevel.MEDIUM

    def test_high_significance(self):
        """Test HIGH significance level."""
        level = assess_divergence_significance(4.5)
        assert level == SignificanceLevel.HIGH

    def test_critical_significance(self):
        """Test CRITICAL significance level."""
        level = assess_divergence_significance(6.0)
        assert level == SignificanceLevel.CRITICAL

    def test_negative_z_score(self):
        """Test with negative z-score (uses absolute value)."""
        level = assess_divergence_significance(-4.5)
        assert level == SignificanceLevel.HIGH

    def test_boundary_none_low(self):
        """Test boundary between NONE and LOW."""
        level_none = assess_divergence_significance(1.99)
        level_low = assess_divergence_significance(2.0)
        assert level_none == SignificanceLevel.NONE
        assert level_low == SignificanceLevel.LOW

    def test_boundary_low_medium(self):
        """Test boundary between LOW and MEDIUM."""
        level_low = assess_divergence_significance(2.99)
        level_medium = assess_divergence_significance(3.0)
        assert level_low == SignificanceLevel.LOW
        assert level_medium == SignificanceLevel.MEDIUM

    def test_boundary_medium_high(self):
        """Test boundary between MEDIUM and HIGH."""
        level_medium = assess_divergence_significance(3.99)
        level_high = assess_divergence_significance(4.0)
        assert level_medium == SignificanceLevel.MEDIUM
        assert level_high == SignificanceLevel.HIGH

    def test_boundary_high_critical(self):
        """Test boundary between HIGH and CRITICAL."""
        level_high = assess_divergence_significance(4.99)
        level_critical = assess_divergence_significance(5.0)
        assert level_high == SignificanceLevel.HIGH
        assert level_critical == SignificanceLevel.CRITICAL

    def test_custom_threshold(self):
        """Test with custom threshold."""
        level = assess_divergence_significance(1.5, threshold=1.0)
        assert level == SignificanceLevel.LOW

    def test_custom_threshold_critical(self):
        """Test custom threshold reaching critical."""
        level = assess_divergence_significance(5.0, threshold=1.0)
        assert level == SignificanceLevel.CRITICAL

    def test_zero_threshold_raises_error(self):
        """Test error when threshold is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            assess_divergence_significance(2.5, threshold=0.0)

    def test_negative_threshold_raises_error(self):
        """Test error when threshold is negative."""
        with pytest.raises(ValueError, match="must be positive"):
            assess_divergence_significance(2.5, threshold=-1.0)

    def test_not_numeric_z_score(self):
        """Test error when z-score is not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            assess_divergence_significance("2.5")

    def test_not_numeric_threshold(self):
        """Test error when threshold is not numeric."""
        with pytest.raises(ValueError, match="must be numeric"):
            assess_divergence_significance(2.5, threshold="2.0")

    def test_very_large_z_score(self):
        """Test with very large z-score."""
        level = assess_divergence_significance(100.0)
        assert level == SignificanceLevel.CRITICAL

    def test_zero_z_score(self):
        """Test with zero z-score."""
        level = assess_divergence_significance(0.0)
        assert level == SignificanceLevel.NONE


class TestComputeBetaMean:
    """Tests for compute_beta_mean function."""

    def test_uniform_prior(self):
        """Test mean of uniform prior Beta(1,1)."""
        mean = compute_beta_mean(1.0, 1.0)
        assert mean == 0.5

    def test_skewed_high(self):
        """Test mean of distribution skewed high."""
        mean = compute_beta_mean(9.0, 1.0)
        assert mean == 0.9

    def test_skewed_low(self):
        """Test mean of distribution skewed low."""
        mean = compute_beta_mean(1.0, 9.0)
        assert mean == 0.1

    def test_symmetric_distribution(self):
        """Test mean of symmetric distribution."""
        mean = compute_beta_mean(10.0, 10.0)
        assert mean == 0.5

    def test_invalid_alpha_negative(self):
        """Test error when alpha is negative."""
        with pytest.raises(ValueError, match="must be positive"):
            compute_beta_mean(-1.0, 1.0)

    def test_invalid_beta_zero(self):
        """Test error when beta is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            compute_beta_mean(1.0, 0.0)


class TestComputeBetaVariance:
    """Tests for compute_beta_variance function."""

    def test_uniform_prior(self):
        """Test variance of uniform prior Beta(1,1)."""
        variance = compute_beta_variance(1.0, 1.0)
        # Variance of Beta(1,1) = 1/12 ≈ 0.0833
        assert abs(variance - 1 / 12) < 1e-10

    def test_large_parameters(self):
        """Test variance decreases with larger parameters."""
        var_small = compute_beta_variance(2.0, 2.0)
        var_large = compute_beta_variance(20.0, 20.0)
        assert var_large < var_small

    def test_symmetric_distribution(self):
        """Test variance of symmetric distribution."""
        variance = compute_beta_variance(10.0, 10.0)
        # Should be relatively small due to large parameters
        assert variance < 0.05

    def test_invalid_alpha_negative(self):
        """Test error when alpha is negative."""
        with pytest.raises(ValueError, match="must be positive"):
            compute_beta_variance(-1.0, 1.0)

    def test_invalid_beta_zero(self):
        """Test error when beta is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            compute_beta_variance(1.0, 0.0)


class TestBetaMode:
    """Tests for beta_mode function."""

    def test_symmetric_distribution(self):
        """Test mode of symmetric distribution."""
        mode = beta_mode(5.0, 5.0)
        assert mode == 0.5

    def test_skewed_high(self):
        """Test mode of distribution skewed high."""
        mode = beta_mode(10.0, 2.0)
        # Mode = (10-1)/(10+2-2) = 9/10 = 0.9
        assert mode == 0.9

    def test_skewed_low(self):
        """Test mode of distribution skewed low."""
        mode = beta_mode(2.0, 10.0)
        # Mode = (2-1)/(2+10-2) = 1/10 = 0.1
        assert mode == 0.1

    def test_invalid_alpha_one(self):
        """Test error when alpha is exactly 1."""
        with pytest.raises(ValueError, match="only defined for alpha, beta > 1"):
            beta_mode(1.0, 2.0)

    def test_invalid_beta_one(self):
        """Test error when beta is exactly 1."""
        with pytest.raises(ValueError, match="only defined for alpha, beta > 1"):
            beta_mode(2.0, 1.0)

    def test_invalid_both_one(self):
        """Test error when both alpha and beta are 1."""
        with pytest.raises(ValueError, match="only defined for alpha, beta > 1"):
            beta_mode(1.0, 1.0)

    def test_invalid_alpha_less_than_one(self):
        """Test error when alpha is less than 1."""
        with pytest.raises(ValueError, match="only defined for alpha, beta > 1"):
            beta_mode(0.5, 2.0)


class TestIntegration:
    """Integration tests combining multiple statistical functions."""

    def test_bayesian_workflow(self):
        """Test complete Bayesian workflow."""
        # Start with uniform prior
        prior_alpha, prior_beta = 1.0, 1.0

        # Update with evidence
        post_alpha, post_beta = bayesian_update(
            prior_alpha, prior_beta, {"successes": 8, "failures": 2}
        )

        # Compute statistics
        mean = compute_beta_mean(post_alpha, post_beta)
        variance = compute_beta_variance(post_alpha, post_beta)
        lower, upper = compute_confidence_interval(post_alpha, post_beta, 0.95)

        # Check results make sense
        assert 0.7 < mean < 0.9  # Should be high due to many successes
        assert variance > 0  # Should have some uncertainty
        assert lower < mean < upper  # Mean should be in CI
        assert 0 <= lower <= upper <= 1  # Should be valid probabilities

    def test_sequential_updates(self):
        """Test sequential Bayesian updates."""
        alpha, beta = 1.0, 1.0

        # First update
        alpha, beta = bayesian_update(alpha, beta, {"successes": 5, "failures": 5})
        mean1 = compute_beta_mean(alpha, beta)

        # Second update with more successes
        alpha, beta = bayesian_update(alpha, beta, {"successes": 10, "failures": 2})
        mean2 = compute_beta_mean(alpha, beta)

        # Mean should increase with more successes
        assert mean2 > mean1

    def test_z_score_with_significance(self):
        """Test z-score calculation with significance assessment."""
        # Calculate z-score
        z = z_score(120, 100, 10)

        # Assess significance
        level = assess_divergence_significance(z)

        # z = 2.0, should be LOW significance
        assert z == 2.0
        assert level == SignificanceLevel.LOW

    def test_confidence_interval_narrowing(self):
        """Test that CI narrows with more evidence."""
        # Start with weak prior
        alpha1, beta1 = 2.0, 2.0
        lower1, upper1 = compute_confidence_interval(alpha1, beta1)
        width1 = upper1 - lower1

        # Add lots of evidence
        alpha2, beta2 = bayesian_update(alpha1, beta1, {"successes": 50, "failures": 50})
        lower2, upper2 = compute_confidence_interval(alpha2, beta2)
        width2 = upper2 - lower2

        # CI should be narrower with more evidence
        assert width2 < width1
