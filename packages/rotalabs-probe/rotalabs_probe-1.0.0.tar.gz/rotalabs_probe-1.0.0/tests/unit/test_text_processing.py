"""Unit tests for text processing utilities."""

import pytest

from rotalabs_probe.utils.text_processing import (
    get_confidence_phrases,
    get_uncertainty_phrases,
    normalize_text,
    remove_stopwords,
    tokenize,
)


class TestTokenize:
    """Test cases for tokenize function."""

    def test_basic_tokenization(self) -> None:
        """Test basic word tokenization."""
        text = "Hello world, this is a test."
        tokens = tokenize(text)
        assert tokens == ["hello", "world", "this", "is", "a", "test"]

    def test_tokenization_with_punctuation(self) -> None:
        """Test tokenization removes punctuation."""
        text = "Hello! How are you?"
        tokens = tokenize(text)
        assert tokens == ["hello", "how", "are", "you"]

    def test_tokenization_case_sensitive(self) -> None:
        """Test tokenization with case preservation."""
        text = "Hello World"
        tokens = tokenize(text, lowercase=False)
        assert tokens == ["Hello", "World"]


class TestRemoveStopwords:
    """Test cases for remove_stopwords function."""

    def test_remove_basic_stopwords(self) -> None:
        """Test removal of common stopwords."""
        tokens = ["this", "is", "a", "test", "sentence"]
        stopwords = {"this", "is", "a"}
        result = remove_stopwords(tokens, stopwords)
        assert result == ["test", "sentence"]

    def test_empty_stopwords(self) -> None:
        """Test with empty stopwords set."""
        tokens = ["hello", "world"]
        stopwords: set[str] = set()
        result = remove_stopwords(tokens, stopwords)
        assert result == tokens


class TestNormalizeText:
    """Test cases for normalize_text function."""

    def test_normalize_whitespace(self) -> None:
        """Test normalization of extra whitespace."""
        text = "Hello    world  \n  test"
        result = normalize_text(text)
        assert result == "hello world test"

    def test_normalize_case(self) -> None:
        """Test case normalization."""
        text = "HELLO WoRlD"
        result = normalize_text(text)
        assert result == "hello world"

    def test_strip_whitespace(self) -> None:
        """Test stripping of leading/trailing whitespace."""
        text = "  hello world  "
        result = normalize_text(text)
        assert result == "hello world"


class TestUncertaintyPhrases:
    """Test cases for get_uncertainty_phrases function."""

    def test_returns_set(self) -> None:
        """Test that function returns a set."""
        phrases = get_uncertainty_phrases()
        assert isinstance(phrases, set)

    def test_contains_common_phrases(self) -> None:
        """Test that set contains common uncertainty phrases."""
        phrases = get_uncertainty_phrases()
        assert "i'm not sure" in phrases
        assert "maybe" in phrases
        assert "perhaps" in phrases


class TestConfidencePhrases:
    """Test cases for get_confidence_phrases function."""

    def test_returns_set(self) -> None:
        """Test that function returns a set."""
        phrases = get_confidence_phrases()
        assert isinstance(phrases, set)

    def test_contains_common_phrases(self) -> None:
        """Test that set contains common confidence phrases."""
        phrases = get_confidence_phrases()
        assert "i'm certain" in phrases
        assert "definitely" in phrases
        assert "absolutely" in phrases
