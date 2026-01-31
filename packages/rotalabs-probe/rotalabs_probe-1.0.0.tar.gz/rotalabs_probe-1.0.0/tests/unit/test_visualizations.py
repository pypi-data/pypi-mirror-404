"""Tests for visualization utilities."""

import pytest
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from rotalabs_probe.viz import (
    plot_awareness_over_time,
    plot_causal_attribution,
    plot_divergence_heatmap,
    plot_feature_distributions,
)


@pytest.fixture
def sample_timestamps():
    """Generate sample timestamps."""
    base = datetime.now()
    return [base + timedelta(hours=i) for i in range(24)]


@pytest.fixture
def sample_numeric_timestamps():
    """Generate numeric timestamps."""
    return list(range(24))


@pytest.fixture
def sample_probabilities():
    """Generate sample awareness probabilities."""
    # Gradual increase in awareness
    return [0.1 + 0.03 * i for i in range(24)]


@pytest.fixture
def sample_confidence_intervals(sample_probabilities):
    """Generate sample confidence intervals."""
    return [(max(0, p - 0.05), min(1, p + 0.05)) for p in sample_probabilities]


@pytest.fixture
def sample_intervention_results():
    """Generate sample intervention results."""
    return [
        {"intervention_type": "remove_eval_awareness", "divergence": 0.342},
        {"intervention_type": "amplify_eval_awareness", "divergence": 0.156},
        {"intervention_type": "remove_goal_reasoning", "divergence": 0.089},
        {"intervention_type": "neutralize_incentives", "divergence": 0.067},
    ]


@pytest.fixture
def sample_z_scores():
    """Generate sample z-score matrix."""
    return np.array([
        [0.5, 1.2, 2.8, 3.5, 4.2, 2.1],  # response_length
        [-0.2, 0.1, 0.3, 4.2, 3.8, 2.5],  # refusal_rate
        [0.1, 0.3, 0.2, 0.4, 0.6, 0.5],   # hedging_ratio
        [0.8, 1.5, 2.2, 3.1, 4.5, 3.2],   # tool_use_rate
    ])


@pytest.fixture
def sample_features():
    """Generate sample feature names."""
    return ["response_length", "refusal_rate", "hedging_ratio", "tool_use_rate"]


@pytest.fixture
def sample_timepoint_labels():
    """Generate sample timepoint labels."""
    return ["00:00", "02:00", "04:00", "06:00", "08:00", "10:00"]


@pytest.fixture
def sample_eval_distribution():
    """Generate sample evaluation distribution."""
    np.random.seed(42)
    return np.random.normal(100, 15, 200)


@pytest.fixture
def sample_prod_distribution():
    """Generate sample production distribution."""
    np.random.seed(43)
    return np.random.normal(120, 20, 200)


@pytest.fixture
def temp_save_path():
    """Create temporary file path for saving plots."""
    temp_dir = tempfile.mkdtemp()
    return os.path.join(temp_dir, "test_plot.png")


class TestPlotAwarenessOverTime:
    """Tests for plot_awareness_over_time function."""

    def test_basic_plot_datetime(
        self, sample_timestamps, sample_probabilities, temp_save_path
    ):
        """Test basic plot with datetime timestamps."""
        fig = plot_awareness_over_time(
            sample_timestamps,
            sample_probabilities,
            save_path=temp_save_path,
            show=False,
        )

        assert fig is not None
        assert len(fig.axes) == 1
        assert Path(temp_save_path).exists()
        plt.close(fig)

    def test_basic_plot_numeric(
        self, sample_numeric_timestamps, sample_probabilities, temp_save_path
    ):
        """Test basic plot with numeric timestamps."""
        fig = plot_awareness_over_time(
            sample_numeric_timestamps,
            sample_probabilities,
            save_path=temp_save_path,
            show=False,
        )

        assert fig is not None
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_plot_with_confidence_intervals(
        self, sample_timestamps, sample_probabilities, sample_confidence_intervals
    ):
        """Test plot with confidence intervals."""
        fig = plot_awareness_over_time(
            sample_timestamps,
            sample_probabilities,
            confidence_intervals=sample_confidence_intervals,
            show=False,
        )

        assert fig is not None
        # Should have shaded region for confidence intervals
        ax = fig.axes[0]
        assert len(ax.collections) > 0  # PolyCollection for fill_between
        plt.close(fig)

    def test_plot_with_threshold(self, sample_timestamps, sample_probabilities):
        """Test plot with decision threshold."""
        fig = plot_awareness_over_time(
            sample_timestamps, sample_probabilities, threshold=0.5, show=False
        )

        assert fig is not None
        ax = fig.axes[0]
        # Check for horizontal line at threshold
        horizontal_lines = [
            line for line in ax.lines if len(line.get_xdata()) > 1
            and line.get_ydata()[0] == line.get_ydata()[-1]
        ]
        assert len(horizontal_lines) > 0
        plt.close(fig)

    def test_custom_labels(self, sample_timestamps, sample_probabilities):
        """Test plot with custom labels."""
        title = "Custom Title"
        xlabel = "Custom X"
        ylabel = "Custom Y"

        fig = plot_awareness_over_time(
            sample_timestamps,
            sample_probabilities,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            show=False,
        )

        ax = fig.axes[0]
        assert ax.get_title() == title
        assert ax.get_xlabel() == xlabel
        assert ax.get_ylabel() == ylabel
        plt.close(fig)

    def test_custom_figsize(self, sample_timestamps, sample_probabilities):
        """Test plot with custom figure size."""
        figsize = (8, 4)
        fig = plot_awareness_over_time(
            sample_timestamps, sample_probabilities, figsize=figsize, show=False
        )

        assert np.allclose(fig.get_size_inches(), figsize, atol=0.1)
        plt.close(fig)

    def test_length_mismatch_error(self, sample_timestamps):
        """Test error when timestamps and probabilities length mismatch."""
        with pytest.raises(ValueError, match="must have the same length"):
            plot_awareness_over_time(
                sample_timestamps, [0.1, 0.2, 0.3], show=False
            )

    def test_confidence_interval_mismatch_error(
        self, sample_timestamps, sample_probabilities
    ):
        """Test error when confidence intervals length mismatch."""
        with pytest.raises(ValueError, match="must match"):
            plot_awareness_over_time(
                sample_timestamps,
                sample_probabilities,
                confidence_intervals=[(0.1, 0.2), (0.2, 0.3)],
                show=False,
            )

    def test_y_axis_limits(self, sample_timestamps, sample_probabilities):
        """Test that y-axis is properly bounded for probabilities."""
        fig = plot_awareness_over_time(
            sample_timestamps, sample_probabilities, show=False
        )

        ax = fig.axes[0]
        ylim = ax.get_ylim()
        assert ylim[0] <= 0
        assert ylim[1] >= 1
        plt.close(fig)


class TestPlotCausalAttribution:
    """Tests for plot_causal_attribution function."""

    def test_basic_plot(self, sample_intervention_results, temp_save_path):
        """Test basic causal attribution plot."""
        fig = plot_causal_attribution(
            sample_intervention_results, save_path=temp_save_path, show=False
        )

        assert fig is not None
        assert len(fig.axes) == 1
        assert Path(temp_save_path).exists()
        plt.close(fig)

    def test_sorting_by_divergence(self, sample_intervention_results):
        """Test that results are sorted by divergence."""
        fig = plot_causal_attribution(sample_intervention_results, show=False)

        ax = fig.axes[0]
        # First bar should be the highest divergence
        bars = [patch for patch in ax.patches if hasattr(patch, 'get_width')]
        widths = [bar.get_width() for bar in bars]
        assert widths == sorted(widths, reverse=True)
        plt.close(fig)

    def test_highlight_threshold(self, sample_intervention_results):
        """Test highlighting bars above threshold."""
        fig = plot_causal_attribution(
            sample_intervention_results, highlight_threshold=0.2, show=False
        )

        ax = fig.axes[0]
        # Should have bars with different colors
        bars = [patch for patch in ax.patches if hasattr(patch, 'get_facecolor')]
        colors = [bar.get_facecolor() for bar in bars]
        # Not all colors should be the same
        assert len(set(map(tuple, colors))) > 1
        plt.close(fig)

    def test_custom_labels(self, sample_intervention_results):
        """Test plot with custom labels."""
        title = "Custom Attribution"
        xlabel = "Custom X"
        ylabel = "Custom Y"

        fig = plot_causal_attribution(
            sample_intervention_results,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            show=False,
        )

        ax = fig.axes[0]
        assert ax.get_title() == title
        assert ax.get_xlabel() == xlabel
        assert ax.get_ylabel() == ylabel
        plt.close(fig)

    def test_empty_results_error(self):
        """Test error with empty intervention results."""
        with pytest.raises(ValueError, match="cannot be empty"):
            plot_causal_attribution([], show=False)

    def test_value_labels_on_bars(self, sample_intervention_results):
        """Test that value labels are added to bars."""
        fig = plot_causal_attribution(sample_intervention_results, show=False)

        ax = fig.axes[0]
        # Should have text annotations
        assert len(ax.texts) == len(sample_intervention_results)
        plt.close(fig)


class TestPlotDivergenceHeatmap:
    """Tests for plot_divergence_heatmap function."""

    def test_basic_heatmap(
        self,
        sample_features,
        sample_timepoint_labels,
        sample_z_scores,
        temp_save_path,
    ):
        """Test basic divergence heatmap."""
        fig = plot_divergence_heatmap(
            sample_features,
            sample_timepoint_labels,
            sample_z_scores,
            save_path=temp_save_path,
            show=False,
        )

        assert fig is not None
        assert len(fig.axes) >= 1  # Main plot + colorbar
        assert Path(temp_save_path).exists()
        plt.close(fig)

    def test_datetime_timepoints(self, sample_features, sample_z_scores):
        """Test heatmap with datetime timepoints."""
        base = datetime.now()
        timepoints = [base + timedelta(hours=i * 2) for i in range(6)]

        fig = plot_divergence_heatmap(
            sample_features, timepoints, sample_z_scores, show=False
        )

        assert fig is not None
        plt.close(fig)

    def test_custom_colormap(
        self, sample_features, sample_timepoint_labels, sample_z_scores
    ):
        """Test heatmap with custom colormap."""
        fig = plot_divergence_heatmap(
            sample_features,
            sample_timepoint_labels,
            sample_z_scores,
            cmap="coolwarm",
            show=False,
        )

        assert fig is not None
        plt.close(fig)

    def test_custom_vmin_vmax(
        self, sample_features, sample_timepoint_labels, sample_z_scores
    ):
        """Test heatmap with custom z-score range."""
        fig = plot_divergence_heatmap(
            sample_features,
            sample_timepoint_labels,
            sample_z_scores,
            vmin=-3.0,
            vmax=3.0,
            show=False,
        )

        assert fig is not None
        plt.close(fig)

    def test_custom_labels(
        self, sample_features, sample_timepoint_labels, sample_z_scores
    ):
        """Test heatmap with custom labels."""
        title = "Custom Heatmap"
        xlabel = "Custom X"
        ylabel = "Custom Y"

        fig = plot_divergence_heatmap(
            sample_features,
            sample_timepoint_labels,
            sample_z_scores,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            show=False,
        )

        ax = fig.axes[0]
        assert ax.get_title() == title
        assert ax.get_xlabel() == xlabel
        assert ax.get_ylabel() == ylabel
        plt.close(fig)

    def test_shape_mismatch_features_error(
        self, sample_timepoint_labels, sample_z_scores
    ):
        """Test error when features don't match z_scores rows."""
        with pytest.raises(ValueError, match="must match features"):
            plot_divergence_heatmap(
                ["feature1", "feature2"],  # Only 2, but z_scores has 4 rows
                sample_timepoint_labels,
                sample_z_scores,
                show=False,
            )

    def test_shape_mismatch_timepoints_error(
        self, sample_features, sample_z_scores
    ):
        """Test error when timepoints don't match z_scores columns."""
        with pytest.raises(ValueError, match="must match timepoints"):
            plot_divergence_heatmap(
                sample_features,
                ["t1", "t2"],  # Only 2, but z_scores has 6 columns
                sample_z_scores,
                show=False,
            )

    def test_annotations_for_high_divergence(
        self, sample_features, sample_timepoint_labels, sample_z_scores
    ):
        """Test that high z-scores get text annotations."""
        fig = plot_divergence_heatmap(
            sample_features, sample_timepoint_labels, sample_z_scores, show=False
        )

        ax = fig.axes[0]
        # Should have text annotations for z-scores >= 3.0
        high_z_count = np.sum(np.abs(sample_z_scores) >= 3.0)
        assert len(ax.texts) >= high_z_count
        plt.close(fig)


class TestPlotFeatureDistributions:
    """Tests for plot_feature_distributions function."""

    def test_basic_distribution_plot(
        self, sample_eval_distribution, sample_prod_distribution, temp_save_path
    ):
        """Test basic distribution comparison plot."""
        fig = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "response_length",
            save_path=temp_save_path,
            show=False,
        )

        assert fig is not None
        assert len(fig.axes) == 1
        assert Path(temp_save_path).exists()
        plt.close(fig)

    def test_custom_title_and_labels(
        self, sample_eval_distribution, sample_prod_distribution
    ):
        """Test plot with custom title and labels."""
        title = "Custom Distribution"
        xlabel = "Custom X"
        ylabel = "Custom Y"

        fig = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "test_feature",
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            show=False,
        )

        ax = fig.axes[0]
        assert ax.get_title() == title
        assert ax.get_xlabel() == xlabel
        assert ax.get_ylabel() == ylabel
        plt.close(fig)

    def test_auto_generated_title(
        self, sample_eval_distribution, sample_prod_distribution
    ):
        """Test auto-generated title from feature name."""
        fig = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "response_length",
            show=False,
        )

        ax = fig.axes[0]
        assert "Response Length" in ax.get_title()
        assert "Distribution Comparison" in ax.get_title()
        plt.close(fig)

    def test_custom_bins(self, sample_eval_distribution, sample_prod_distribution):
        """Test plot with custom number of bins."""
        fig = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "test_feature",
            bins=50,
            show=False,
        )

        assert fig is not None
        plt.close(fig)

    def test_custom_alpha(self, sample_eval_distribution, sample_prod_distribution):
        """Test plot with custom transparency."""
        fig = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "test_feature",
            alpha=0.8,
            show=False,
        )

        assert fig is not None
        plt.close(fig)

    def test_empty_distribution_error(self, sample_eval_distribution):
        """Test error with empty distribution."""
        with pytest.raises(ValueError, match="must contain data"):
            plot_feature_distributions(
                sample_eval_distribution, [], "test_feature", show=False
            )

    def test_statistics_in_legend(
        self, sample_eval_distribution, sample_prod_distribution
    ):
        """Test that statistics are shown in legend."""
        fig = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "test_feature",
            show=False,
        )

        ax = fig.axes[0]
        legend = ax.get_legend()
        assert legend is not None
        # Legend should contain mean and std information
        legend_text = [t.get_text() for t in legend.get_texts()]
        assert any("μ=" in text for text in legend_text)
        assert any("σ=" in text for text in legend_text)
        plt.close(fig)

    def test_mean_lines_present(
        self, sample_eval_distribution, sample_prod_distribution
    ):
        """Test that mean lines are plotted."""
        fig = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "test_feature",
            show=False,
        )

        ax = fig.axes[0]
        # Should have vertical lines for means
        vertical_lines = [
            line for line in ax.lines if len(line.get_ydata()) > 1
            and line.get_xdata()[0] == line.get_xdata()[-1]
        ]
        assert len(vertical_lines) >= 2  # At least 2 mean lines
        plt.close(fig)

    def test_list_input(self):
        """Test that list inputs are converted to arrays."""
        eval_list = [1, 2, 3, 4, 5]
        prod_list = [2, 3, 4, 5, 6]

        fig = plot_feature_distributions(
            eval_list, prod_list, "test_feature", show=False
        )

        assert fig is not None
        plt.close(fig)


class TestPlottingIntegration:
    """Integration tests for plotting functions."""

    def test_all_plots_create_valid_figures(
        self,
        sample_timestamps,
        sample_probabilities,
        sample_intervention_results,
        sample_features,
        sample_timepoint_labels,
        sample_z_scores,
        sample_eval_distribution,
        sample_prod_distribution,
    ):
        """Test that all plotting functions create valid figures."""
        fig1 = plot_awareness_over_time(
            sample_timestamps, sample_probabilities, show=False
        )
        fig2 = plot_causal_attribution(sample_intervention_results, show=False)
        fig3 = plot_divergence_heatmap(
            sample_features, sample_timepoint_labels, sample_z_scores, show=False
        )
        fig4 = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "test_feature",
            show=False,
        )

        for fig in [fig1, fig2, fig3, fig4]:
            assert fig is not None
            assert len(fig.axes) > 0

        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)
        plt.close(fig4)

    def test_save_all_plots(
        self,
        sample_timestamps,
        sample_probabilities,
        sample_intervention_results,
        sample_features,
        sample_timepoint_labels,
        sample_z_scores,
        sample_eval_distribution,
        sample_prod_distribution,
    ):
        """Test saving all plot types."""
        temp_dir = tempfile.mkdtemp()

        paths = {
            "awareness": os.path.join(temp_dir, "awareness.png"),
            "causal": os.path.join(temp_dir, "causal.png"),
            "heatmap": os.path.join(temp_dir, "heatmap.png"),
            "distributions": os.path.join(temp_dir, "distributions.png"),
        }

        fig1 = plot_awareness_over_time(
            sample_timestamps,
            sample_probabilities,
            save_path=paths["awareness"],
            show=False,
        )
        fig2 = plot_causal_attribution(
            sample_intervention_results, save_path=paths["causal"], show=False
        )
        fig3 = plot_divergence_heatmap(
            sample_features,
            sample_timepoint_labels,
            sample_z_scores,
            save_path=paths["heatmap"],
            show=False,
        )
        fig4 = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "test_feature",
            save_path=paths["distributions"],
            show=False,
        )

        for path in paths.values():
            assert Path(path).exists()
            assert Path(path).stat().st_size > 0

        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)
        plt.close(fig4)

    def test_custom_dpi_all_plots(
        self,
        sample_timestamps,
        sample_probabilities,
        sample_intervention_results,
        sample_features,
        sample_timepoint_labels,
        sample_z_scores,
        sample_eval_distribution,
        sample_prod_distribution,
    ):
        """Test custom DPI setting for all plots."""
        dpi = 150

        # Test that figures are created successfully with custom DPI
        # Note: matplotlib may adjust DPI internally, so we check figure creation
        fig1 = plot_awareness_over_time(
            sample_timestamps, sample_probabilities, dpi=dpi, show=False
        )
        fig2 = plot_causal_attribution(
            sample_intervention_results, dpi=dpi, show=False
        )
        fig3 = plot_divergence_heatmap(
            sample_features,
            sample_timepoint_labels,
            sample_z_scores,
            dpi=dpi,
            show=False,
        )
        fig4 = plot_feature_distributions(
            sample_eval_distribution,
            sample_prod_distribution,
            "test_feature",
            dpi=dpi,
            show=False,
        )

        # Verify all figures were created successfully
        for fig in [fig1, fig2, fig3, fig4]:
            assert fig is not None
            assert len(fig.axes) > 0

        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)
        plt.close(fig4)
