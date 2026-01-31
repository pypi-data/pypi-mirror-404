# Test Suite Documentation

This directory contains comprehensive tests for the AI Metacognition Toolkit.

## Overview

- **Total Tests**: 310
- **Code Coverage**: 95%
- **Test Framework**: pytest
- **All Tests**: ✅ Passing

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and test configuration
├── fixtures/
│   └── sample_model_outputs.json        # Realistic test data
└── unit/
    ├── test_counterfactual_cot.py      # 44 tests - Counterfactual CoT Analyzer
    ├── test_feature_extraction.py       # 54 tests - Feature extraction utilities
    ├── test_observer_effect.py          # 46 tests - Observer Effect Monitor
    ├── test_situational_awareness.py    # 38 tests - Situational Awareness Detector
    ├── test_statistical_tests.py        # 81 tests - Statistical testing utilities
    ├── test_text_processing.py          # 12 tests - Text processing utilities
    └── test_visualizations.py           # 35 tests - Visualization utilities
```

## Test Files

### test_situational_awareness.py
**Tests**: 38 | **Coverage**: 97%

Tests the SituationalAwarenessDetector for detecting when AI models recognize evaluation contexts.

**Test Categories**:
- Initialization and baseline fitting
- Awareness detection with Bayesian inference
- KL divergence computation
- Feature extraction and comparison
- Edge cases and error handling
- Integration tests

**Key Fixtures Used**:
- `no_awareness_texts`, `low_awareness_texts`, `medium_awareness_texts`, `high_awareness_texts`
- `baseline_responses`, `evaluation_responses`

### test_counterfactual_cot.py
**Tests**: 44 | **Coverage**: 96%

Tests the CounterfactualCoTAnalyzer for systematic causal analysis on reasoning chains.

**Test Categories**:
- Initialization with ModelAPI protocol
- Reasoning chain parsing and classification
- Counterfactual interventions (remove, amplify, neutralize)
- Behavioral divergence measurement
- Systematic causal analysis
- Action extraction and CoT reconstruction
- Integration workflows

**Key Fixtures Used**:
- `mock_model_api`, `mock_model_api_with_response`
- `simple_cot`, `complex_cot`, `evaluation_aware_cot`, `meta_reasoning_cot`
- `counterfactual_original_cot`, `counterfactual_interventions`

### test_observer_effect.py
**Tests**: 46 | **Coverage**: 89%

Tests the ObserverEffectMonitor for real-time production monitoring and divergence detection.

**Test Categories**:
- Initialization and configuration
- Baseline setting from evaluation data
- Production interaction logging
- Z-score based divergence detection
- Alert generation with severity levels
- Alert handler system (extensible)
- Rolling window statistics
- Divergence reporting and trends
- Integration tests

**Key Fixtures Used**:
- `baseline_responses`, `evaluation_responses`
- `production_normal_texts`, `production_divergent_texts`

### test_feature_extraction.py
**Tests**: 54 | **Coverage**: 97%

Tests feature extraction utilities for behavioral analysis.

**Test Categories**:
- Behavioral feature extraction (13+ features)
- Hedging phrase detection
- Meta-commentary detection
- Reasoning depth analysis
- KL/JS divergence computation
- Cosine similarity
- Distribution normalization
- Edge cases and error handling
- Integration tests

**Key Fixtures Used**:
- `no_hedging_texts`, `moderate_hedging_texts`, `heavy_hedging_texts`
- `meta_commentary_texts`
- `refusal_texts`, `self_reference_texts`
- `high_confidence_texts`, `low_confidence_texts`
- `shallow_reasoning`, `moderate_reasoning`, `deep_reasoning`

### test_statistical_tests.py
**Tests**: 81 | **Coverage**: 100%

Tests statistical testing utilities for Bayesian inference and divergence assessment.

**Test Categories**:
- Bayesian update with Beta-Binomial conjugate prior
- Confidence interval computation
- Z-score calculation with edge cases
- Divergence significance assessment
- Beta distribution statistics (mean, variance, mode)
- Integration workflows
- Error handling and validation

**Features Tested**:
- `bayesian_update()` - 15 tests
- `compute_confidence_interval()` - 13 tests
- `z_score()` - 13 tests
- `assess_divergence_significance()` - 18 tests
- `compute_beta_mean()` - 6 tests
- `compute_beta_variance()` - 5 tests
- `beta_mode()` - 7 tests
- Integration tests - 4 tests

### test_visualizations.py
**Tests**: 35 | **Coverage**: 94%

Tests publication-ready visualization functions.

**Test Categories**:
- Awareness over time plots (datetime and numeric timestamps)
- Causal attribution bar charts (sorting, highlighting, labeling)
- Divergence heatmaps (colormaps, annotations, datetime support)
- Feature distribution comparisons (histograms, KDEs, statistics)
- Custom styling and figure parameters
- File saving functionality
- Error handling for invalid inputs
- Integration tests

**Features Tested**:
- `plot_awareness_over_time()` - 9 tests
- `plot_causal_attribution()` - 6 tests
- `plot_divergence_heatmap()` - 8 tests
- `plot_feature_distributions()` - 9 tests
- Integration tests - 3 tests

### test_text_processing.py
**Tests**: 12 | **Coverage**: 100%

Tests basic text processing utilities.

## Fixtures

### conftest.py

Provides comprehensive pytest fixtures for all test files:

**Awareness Level Fixtures**:
- `no_awareness_texts` - Texts with no evaluation awareness
- `low_awareness_texts` - Texts with minimal awareness
- `medium_awareness_texts` - Texts with moderate awareness
- `high_awareness_texts` - Texts with strong awareness indicators

**Chain-of-Thought Fixtures**:
- `simple_cot` - Basic reasoning chain
- `complex_cot` - Multi-step reasoning with analysis
- `evaluation_aware_cot` - CoT showing evaluation awareness
- `meta_reasoning_cot` - CoT with meta-cognitive reasoning

**Behavioral Pattern Fixtures**:
- `no_hedging_texts`, `moderate_hedging_texts`, `heavy_hedging_texts`
- `refusal_texts` - Refusal patterns
- `self_reference_texts` - Self-reference patterns
- `high_confidence_texts`, `low_confidence_texts`

**Production Fixtures**:
- `production_normal_texts` - Normal production responses
- `production_divergent_texts` - Divergent production responses

**Counterfactual Fixtures**:
- `counterfactual_original_cot` - Original CoT for interventions
- `counterfactual_interventions` - All intervention types

**Mock Objects**:
- `mock_model_api` - Mock ModelAPI for testing
- `mock_model_api_with_response` - Mock with predefined response

### sample_model_outputs.json

Contains realistic test data organized by:
- Awareness levels (none, low, medium, high)
- Chain-of-thought examples (simple, complex, evaluation-aware, meta-reasoning)
- Baseline evaluation data (standard vs evaluation responses)
- Hedging patterns (none, moderate, heavy)
- Behavioral patterns (refusal, self-reference, confidence markers)
- Production vs evaluation scenarios
- Meta-commentary examples
- Counterfactual interventions
- Reasoning depth examples

## Running Tests

### Run All Tests
```bash
python -m pytest tests/
```

### Run Specific Test File
```bash
python -m pytest tests/unit/test_situational_awareness.py
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src/ai_metacognition --cov-report=term-missing
```

### Run with Verbose Output
```bash
python -m pytest tests/ -v
```

### Run Specific Test Class
```bash
python -m pytest tests/unit/test_situational_awareness.py::TestSituationalAwarenessDetector -v
```

### Run Specific Test Method
```bash
python -m pytest tests/unit/test_situational_awareness.py::TestSituationalAwarenessDetector::test_detect_awareness_with_high_awareness -v
```

## Coverage Report

Current coverage by module:

| Module | Statements | Missing | Coverage |
|--------|-----------|---------|----------|
| `__init__.py` | 6 | 0 | 100% |
| `analyzers/__init__.py` | 4 | 0 | 100% |
| `analyzers/base.py` | 10 | 2 | 80% |
| `analyzers/counterfactual_cot.py` | 184 | 7 | 96% |
| `analyzers/model_api.py` | 5 | 0 | 100% |
| `detectors/__init__.py` | 4 | 0 | 100% |
| `detectors/base.py` | 10 | 1 | 90% |
| `detectors/observer_effect.py` | 215 | 24 | 89% |
| `detectors/situational_awareness.py` | 158 | 4 | 97% |
| `utils/__init__.py` | 3 | 0 | 100% |
| `utils/feature_extraction.py` | 144 | 4 | 97% |
| `utils/statistical_tests.py` | 81 | 0 | 100% |
| `utils/text_processing.py` | 18 | 0 | 100% |
| `visualizations/__init__.py` | 2 | 0 | 100% |
| `visualizations/plotting.py` | 154 | 9 | 94% |
| **TOTAL** | **998** | **51** | **95%** |

## Test Best Practices

### 1. Use Fixtures
All tests use pytest fixtures from `conftest.py` for consistent test data:

```python
def test_hedging_detection(moderate_hedging_texts):
    """Test using shared fixture."""
    for text in moderate_hedging_texts:
        ratio = count_hedging_phrases(text)
        assert ratio > 0
```

### 2. Test Normal Operation
Every function has tests for expected behavior:

```python
def test_basic_functionality():
    """Test normal operation."""
    result = function(valid_input)
    assert result == expected_output
```

### 3. Test Edge Cases
Tests cover boundary conditions:

```python
def test_empty_input():
    """Test edge case: empty input."""
    result = function("")
    assert result == 0.0

def test_zero_std():
    """Test edge case: zero standard deviation."""
    z = z_score(100, 90, 0)
    assert z == 0.0
```

### 4. Test Error Handling
All invalid inputs are tested:

```python
def test_invalid_input_raises_error():
    """Test error handling."""
    with pytest.raises(ValueError, match="must be positive"):
        function(-1)
```

### 5. Use Parametrize for Multiple Scenarios
Tests use `@pytest.mark.parametrize` when applicable:

```python
@pytest.mark.parametrize("text,expected", [
    ("certain answer", 0.0),
    ("I think maybe", 0.2),
])
def test_multiple_scenarios(text, expected):
    ratio = count_hedging_phrases(text)
    assert ratio == pytest.approx(expected, abs=0.05)
```

### 6. Integration Tests
Each module has integration tests that test full workflows:

```python
def test_full_workflow(mock_model_api):
    """Test complete analysis workflow."""
    analyzer = CounterfactualCoTAnalyzer(mock_model_api)
    result = analyzer.analyze(prompt, cot)
    assert "interventions" in result
    assert "aggregate_stats" in result
```

## CI/CD Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -e ".[dev]"
    pytest tests/ --cov=src/ai_metacognition --cov-report=xml
```

## Maintenance

### Adding New Tests

1. Add test data to `fixtures/sample_model_outputs.json` if needed
2. Create/update fixtures in `conftest.py`
3. Write tests following the existing patterns
4. Run coverage to ensure >80% coverage
5. Document any new test categories in this README

### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<what_is_being_tested>`

Examples:
- `test_basic_functionality()`
- `test_empty_input_returns_zero()`
- `test_invalid_input_raises_error()`
- `test_edge_case_zero_std()`

## Performance

All tests run in under 7 seconds:
```
============================= 310 passed in 6.98s ===============================
```

Fast test execution enables:
- Rapid development feedback
- Frequent test runs during development
- Efficient CI/CD pipelines
