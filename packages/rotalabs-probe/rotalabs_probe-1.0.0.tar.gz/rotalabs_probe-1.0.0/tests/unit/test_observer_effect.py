"""Unit tests for Observer Effect Monitor."""

from datetime import datetime, timedelta

import pytest

from rotalabs_probe.detectors.observer_effect import (
    Alert,
    AlertHandler,
    AlertSeverity,
    ConsoleAlertHandler,
    Interaction,
    ObserverEffectMonitor,
)


class MockAlertHandler:
    """Mock alert handler for testing."""

    def __init__(self) -> None:
        """Initialize mock handler."""
        self.alerts_received: list = []

    def handle_alert(self, alert: Alert) -> None:
        """Store alert for testing."""
        self.alerts_received.append(alert)


class TestObserverEffectMonitorInit:
    """Test initialization of ObserverEffectMonitor."""

    def test_init_default_parameters(self) -> None:
        """Test initialization with default parameters."""
        monitor = ObserverEffectMonitor()
        assert monitor.window_size == 1000
        assert monitor.alert_threshold == 2.0
        assert len(monitor.production_window) == 0
        assert monitor.baseline_set is False

    def test_init_custom_parameters(self) -> None:
        """Test initialization with custom parameters."""
        monitor = ObserverEffectMonitor(
            window_size=500, alert_threshold=3.0, feature_weights={"test": 1.0}
        )
        assert monitor.window_size == 500
        assert monitor.alert_threshold == 3.0
        assert "test" in monitor.feature_weights

    def test_init_invalid_window_size(self) -> None:
        """Test that invalid window size raises error."""
        with pytest.raises(ValueError, match="window_size must be positive"):
            ObserverEffectMonitor(window_size=0)

        with pytest.raises(ValueError, match="window_size must be positive"):
            ObserverEffectMonitor(window_size=-1)

    def test_init_invalid_alert_threshold(self) -> None:
        """Test that invalid alert threshold raises error."""
        with pytest.raises(ValueError, match="alert_threshold must be positive"):
            ObserverEffectMonitor(alert_threshold=0)


class TestSetEvaluationBaseline:
    """Test setting evaluation baseline."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor fixture."""
        return ObserverEffectMonitor()

    def test_set_baseline_success(self, monitor: ObserverEffectMonitor) -> None:
        """Test successful baseline setting."""
        eval_samples = [
            "This is a normal response.",
            "Another typical response.",
            "Yet another response.",
        ]

        monitor.set_evaluation_baseline(eval_samples)
        assert monitor.baseline_set is True
        assert "response_length" in monitor.evaluation_baseline
        assert "refusal_rate" in monitor.evaluation_baseline

    def test_set_baseline_empty_raises_error(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test that empty samples raise error."""
        with pytest.raises(ValueError, match="eval_samples cannot be empty"):
            monitor.set_evaluation_baseline([])

    def test_set_baseline_invalid_data(self, monitor: ObserverEffectMonitor) -> None:
        """Test that non-string samples raise error."""
        with pytest.raises(ValueError, match="All eval_samples must be strings"):
            monitor.set_evaluation_baseline([123, 456])  # type: ignore

    def test_baseline_statistics_valid(self, monitor: ObserverEffectMonitor) -> None:
        """Test that baseline statistics are computed correctly."""
        eval_samples = ["Short", "Medium length response", "A very long response text"]

        monitor.set_evaluation_baseline(eval_samples)

        stats = monitor.evaluation_baseline["response_length"]
        assert "mean" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert stats["std"] > 0  # Should have epsilon added


class TestLogProductionInteraction:
    """Test logging production interactions."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor with baseline."""
        monitor = ObserverEffectMonitor(window_size=10)
        eval_samples = ["Normal response"] * 5
        monitor.set_evaluation_baseline(eval_samples)
        return monitor

    def test_log_interaction_success(self, monitor: ObserverEffectMonitor) -> None:
        """Test logging an interaction."""
        interaction = Interaction(
            timestamp=datetime.now(), response="Test response", refusal=False
        )

        monitor.log_production_interaction(interaction)
        assert len(monitor.production_window) == 1

    def test_log_multiple_interactions(self, monitor: ObserverEffectMonitor) -> None:
        """Test logging multiple interactions."""
        for i in range(5):
            interaction = Interaction(
                timestamp=datetime.now(), response=f"Response {i}", refusal=False
            )
            monitor.log_production_interaction(interaction)

        assert len(monitor.production_window) == 5

    def test_rolling_window_limit(self) -> None:
        """Test that rolling window respects size limit."""
        monitor = ObserverEffectMonitor(window_size=3)
        eval_samples = ["Normal"] * 5
        monitor.set_evaluation_baseline(eval_samples)

        for i in range(5):
            interaction = Interaction(
                timestamp=datetime.now(), response=f"Response {i}", refusal=False
            )
            monitor.log_production_interaction(interaction)

        assert len(monitor.production_window) == 3  # Should only keep last 3

    def test_log_invalid_interaction_raises_error(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test that invalid interaction raises error."""
        with pytest.raises(ValueError, match="must be an Interaction object"):
            monitor.log_production_interaction("not an interaction")  # type: ignore


class TestDivergenceDetection:
    """Test divergence detection and alerts."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor with baseline."""
        monitor = ObserverEffectMonitor(window_size=100, alert_threshold=2.0)
        # Set baseline with normal responses
        eval_samples = ["Normal response of typical length."] * 50
        monitor.set_evaluation_baseline(eval_samples)
        return monitor

    def test_no_divergence_no_alerts(self, monitor: ObserverEffectMonitor) -> None:
        """Test that similar data doesn't trigger alerts."""
        # Log similar interactions
        for _ in range(40):
            interaction = Interaction(
                timestamp=datetime.now(),
                response="Normal response of typical length.",
                refusal=False,
            )
            monitor.log_production_interaction(interaction)

        assert len(monitor.alerts) == 0

    def test_divergence_triggers_alert(self, monitor: ObserverEffectMonitor) -> None:
        """Test that divergent data triggers alerts."""
        # Log many long responses (divergent from baseline)
        for _ in range(40):
            interaction = Interaction(
                timestamp=datetime.now(),
                response="This is a much much longer response than the baseline " * 10,
                refusal=False,
            )
            monitor.log_production_interaction(interaction)

        # Should trigger alerts for response_length
        assert len(monitor.alerts) > 0

    def test_alert_handler_called(self, monitor: ObserverEffectMonitor) -> None:
        """Test that registered alert handlers are called."""
        mock_handler = MockAlertHandler()
        monitor.register_alert_handler(mock_handler)

        # Log divergent interactions
        for _ in range(40):
            interaction = Interaction(
                timestamp=datetime.now(),
                response="Very long response" * 20,
                refusal=False,
            )
            monitor.log_production_interaction(interaction)

        assert len(mock_handler.alerts_received) > 0


class TestSeverityAssessment:
    """Test alert severity assessment."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor fixture."""
        return ObserverEffectMonitor()

    def test_assess_severity_low(self, monitor: ObserverEffectMonitor) -> None:
        """Test low severity assessment."""
        assert monitor._assess_severity(2.5) == AlertSeverity.LOW
        assert monitor._assess_severity(-2.5) == AlertSeverity.LOW

    def test_assess_severity_medium(self, monitor: ObserverEffectMonitor) -> None:
        """Test medium severity assessment."""
        assert monitor._assess_severity(3.5) == AlertSeverity.MEDIUM
        assert monitor._assess_severity(-3.5) == AlertSeverity.MEDIUM

    def test_assess_severity_high(self, monitor: ObserverEffectMonitor) -> None:
        """Test high severity assessment."""
        assert monitor._assess_severity(4.5) == AlertSeverity.HIGH
        assert monitor._assess_severity(-4.5) == AlertSeverity.HIGH

    def test_assess_severity_critical(self, monitor: ObserverEffectMonitor) -> None:
        """Test critical severity assessment."""
        assert monitor._assess_severity(5.5) == AlertSeverity.CRITICAL
        assert monitor._assess_severity(-10.0) == AlertSeverity.CRITICAL


class TestRecommendAction:
    """Test recommendation generation."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor fixture."""
        return ObserverEffectMonitor()

    def test_recommend_response_length_increase(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test recommendation for increased response length."""
        recommendation = monitor._recommend_action("response_length", 3.0)
        assert "longer" in recommendation.lower()
        assert isinstance(recommendation, str)

    def test_recommend_refusal_rate_critical(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test recommendation for critical refusal rate change."""
        recommendation = monitor._recommend_action("refusal_rate", 5.0)
        assert "critical" in recommendation.lower()
        assert "safety" in recommendation.lower()

    def test_recommendation_includes_severity(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test that high severity recommendations are marked."""
        recommendation = monitor._recommend_action("hedging_ratio", 4.5)
        assert "HIGH" in recommendation or "CRITICAL" in recommendation


class TestTrendAnalysis:
    """Test trend analysis functionality."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor fixture."""
        monitor = ObserverEffectMonitor()
        eval_samples = ["Normal"] * 10
        monitor.set_evaluation_baseline(eval_samples)
        return monitor

    def test_analyze_trends_insufficient_data(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test trend analysis with insufficient data."""
        interactions = [
            Interaction(timestamp=datetime.now(), response="Short", refusal=False)
            for _ in range(5)
        ]
        trends = monitor._analyze_trends(interactions)
        assert trends == {}

    def test_analyze_trends_stable(self, monitor: ObserverEffectMonitor) -> None:
        """Test trend analysis detects stable trends."""
        interactions = [
            Interaction(
                timestamp=datetime.now(), response="Same length text", refusal=False
            )
            for _ in range(20)
        ]
        trends = monitor._analyze_trends(interactions)
        assert "response_length" in trends
        # Should be stable since all same length

    def test_analyze_trends_increasing(self, monitor: ObserverEffectMonitor) -> None:
        """Test trend analysis detects increasing trends."""
        interactions = []
        # First half short, second half long
        for i in range(20):
            length = 10 if i < 10 else 50
            interactions.append(
                Interaction(
                    timestamp=datetime.now(), response="x" * length, refusal=False
                )
            )

        trends = monitor._analyze_trends(interactions)
        assert trends["response_length"] == "increasing"


class TestDivergenceReport:
    """Test divergence report generation."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor with data."""
        monitor = ObserverEffectMonitor()
        eval_samples = ["Normal response"] * 20
        monitor.set_evaluation_baseline(eval_samples)

        # Add production data
        for _ in range(30):
            interaction = Interaction(
                timestamp=datetime.now(), response="Production response", refusal=False
            )
            monitor.log_production_interaction(interaction)

        return monitor

    def test_report_without_baseline_raises_error(self) -> None:
        """Test that report fails without baseline."""
        monitor = ObserverEffectMonitor()
        with pytest.raises(ValueError, match="Evaluation baseline must be set"):
            monitor.get_divergence_report()

    def test_report_insufficient_data_raises_error(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test that report fails with insufficient data."""
        monitor = ObserverEffectMonitor()
        eval_samples = ["Test"] * 10
        monitor.set_evaluation_baseline(eval_samples)

        with pytest.raises(ValueError, match="Insufficient production data"):
            monitor.get_divergence_report()

    def test_report_contains_required_fields(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test that report contains all required fields."""
        report = monitor.get_divergence_report()

        assert "timestamp" in report
        assert "has_divergence" in report
        assert "production_stats" in report
        assert "baseline_stats" in report
        assert "z_scores" in report
        assert "trends" in report
        assert "window_size" in report

    def test_report_z_scores_computed(self, monitor: ObserverEffectMonitor) -> None:
        """Test that z-scores are computed."""
        report = monitor.get_divergence_report()
        assert len(report["z_scores"]) > 0
        assert "response_length" in report["z_scores"]


class TestFeatureExtraction:
    """Test feature extraction methods."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor fixture."""
        return ObserverEffectMonitor()

    def test_detect_refusal_positive(self, monitor: ObserverEffectMonitor) -> None:
        """Test refusal detection on refusal text."""
        text = "I'm sorry, but I cannot help with that. I'm unable to assist."
        assert monitor._detect_refusal(text) is True

    def test_detect_refusal_negative(self, monitor: ObserverEffectMonitor) -> None:
        """Test refusal detection on normal text."""
        text = "I can help you with that task."
        assert monitor._detect_refusal(text) is False

    def test_compute_hedging_ratio(self, monitor: ObserverEffectMonitor) -> None:
        """Test hedging ratio computation."""
        text = "I think maybe this might work perhaps."
        ratio = monitor._compute_hedging_ratio(text)
        assert ratio > 0
        assert ratio <= 1

    def test_compute_hedging_ratio_no_hedging(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test hedging ratio with no hedging."""
        text = "This is a definite statement."
        ratio = monitor._compute_hedging_ratio(text)
        assert ratio == 0

    def test_compute_hedging_ratio_empty(
        self, monitor: ObserverEffectMonitor
    ) -> None:
        """Test hedging ratio with empty text."""
        ratio = monitor._compute_hedging_ratio("")
        assert ratio == 0.0


class TestProductionStats:
    """Test production statistics computation."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor fixture."""
        return ObserverEffectMonitor()

    def test_compute_stats_basic(self, monitor: ObserverEffectMonitor) -> None:
        """Test basic statistics computation."""
        interactions = [
            Interaction(timestamp=datetime.now(), response="Short", refusal=False),
            Interaction(timestamp=datetime.now(), response="Medium text", refusal=False),
            Interaction(
                timestamp=datetime.now(), response="Longer text here", refusal=True
            ),
        ]

        stats = monitor._compute_production_stats(interactions)

        assert "response_length" in stats
        assert "refusal_rate" in stats
        assert stats["response_length"]["mean"] > 0

    def test_compute_stats_empty(self, monitor: ObserverEffectMonitor) -> None:
        """Test statistics computation with empty list."""
        stats = monitor._compute_production_stats([])
        assert stats == {}


class TestAlertHandlers:
    """Test alert handler functionality."""

    def test_register_handler(self) -> None:
        """Test registering an alert handler."""
        monitor = ObserverEffectMonitor()
        handler = MockAlertHandler()

        monitor.register_alert_handler(handler)
        assert len(monitor.alert_handlers) == 1

    def test_register_invalid_handler_raises_error(self) -> None:
        """Test that invalid handler raises error."""
        monitor = ObserverEffectMonitor()

        with pytest.raises(ValueError, match="must implement AlertHandler"):
            monitor.register_alert_handler("not a handler")  # type: ignore

    def test_console_handler_protocol_compliant(self) -> None:
        """Test that ConsoleAlertHandler is protocol compliant."""
        handler = ConsoleAlertHandler()
        assert isinstance(handler, AlertHandler)


class TestAlertSummary:
    """Test alert summary functionality."""

    @pytest.fixture
    def monitor_with_alerts(self) -> ObserverEffectMonitor:
        """Create monitor with some alerts."""
        monitor = ObserverEffectMonitor()

        # Manually add some alerts for testing
        for i in range(5):
            alert = Alert(
                timestamp=datetime.now(),
                feature="test_feature",
                severity=AlertSeverity.LOW if i < 3 else AlertSeverity.HIGH,
                z_score=2.5 + i,
                production_value=1.0,
                baseline_value=0.5,
                recommendation="Test recommendation",
            )
            monitor.alerts.append(alert)

        return monitor

    def test_get_alert_summary_basic(
        self, monitor_with_alerts: ObserverEffectMonitor
    ) -> None:
        """Test basic alert summary."""
        summary = monitor_with_alerts.get_alert_summary()

        assert summary["total_alerts"] == 5
        assert "by_severity" in summary
        assert "by_feature" in summary
        assert "latest_alert" in summary

    def test_get_alert_summary_with_filter(
        self, monitor_with_alerts: ObserverEffectMonitor
    ) -> None:
        """Test alert summary with severity filter."""
        summary = monitor_with_alerts.get_alert_summary(
            severity_filter=AlertSeverity.LOW
        )

        assert summary["total_alerts"] == 3

    def test_get_alert_summary_empty(self) -> None:
        """Test alert summary with no alerts."""
        monitor = ObserverEffectMonitor()
        summary = monitor.get_alert_summary()

        assert summary["total_alerts"] == 0
        assert summary["latest_alert"] is None

    def test_clear_alerts(self, monitor_with_alerts: ObserverEffectMonitor) -> None:
        """Test clearing alerts."""
        assert len(monitor_with_alerts.alerts) > 0

        monitor_with_alerts.clear_alerts()
        assert len(monitor_with_alerts.alerts) == 0


class TestDetectMethod:
    """Test BaseDetector compatibility."""

    @pytest.fixture
    def monitor(self) -> ObserverEffectMonitor:
        """Create monitor with baseline."""
        monitor = ObserverEffectMonitor()
        eval_samples = ["Normal response"] * 20
        monitor.set_evaluation_baseline(eval_samples)
        return monitor

    def test_detect_basic(self, monitor: ObserverEffectMonitor) -> None:
        """Test basic detect method."""
        result = monitor.detect("Test response")

        assert "detected" in result
        assert "confidence" in result
        assert "details" in result

    def test_detect_without_baseline(self) -> None:
        """Test detect without baseline set."""
        monitor = ObserverEffectMonitor()
        result = monitor.detect("Test response")

        assert result["detected"] is False


class TestIntegration:
    """Integration tests for full workflow."""

    def test_full_monitoring_workflow(self) -> None:
        """Test complete monitoring workflow."""
        # Initialize monitor
        monitor = ObserverEffectMonitor(window_size=50, alert_threshold=2.5)

        # Set up alert handler
        mock_handler = MockAlertHandler()
        monitor.register_alert_handler(mock_handler)

        # Set baseline
        eval_samples = ["Normal response of typical length."] * 30
        monitor.set_evaluation_baseline(eval_samples)

        # Simulate production traffic - normal at first
        for _ in range(20):
            interaction = Interaction(
                timestamp=datetime.now(),
                response="Normal response of typical length.",
                refusal=False,
            )
            monitor.log_production_interaction(interaction)

        # Simulate divergent behavior
        for _ in range(25):
            interaction = Interaction(
                timestamp=datetime.now(),
                response="Much longer divergent response " * 10,
                refusal=False,
            )
            monitor.log_production_interaction(interaction)

        # Check that alerts were triggered
        assert len(monitor.alerts) > 0

        # Generate report
        report = monitor.get_divergence_report()
        assert report["has_divergence"] is True
        assert report["window_size"] >= 30

        # Check alert summary
        summary = monitor.get_alert_summary()
        assert summary["total_alerts"] > 0
