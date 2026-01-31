"""Tests for reasoning chain parser functionality."""

import pytest


def test_extended_parser_parse_numbered():
    """Test parsing numbered reasoning steps."""
    from rotalabs_audit import ExtendedReasoningParser

    parser = ExtendedReasoningParser()
    text = """
    1. First, I need to understand the problem
    2. The data shows a clear pattern
    3. Therefore, I conclude that X is true
    """

    chain = parser.parse(text)

    assert len(chain.steps) == 3
    assert "understand the problem" in chain.steps[0].content
    assert "clear pattern" in chain.steps[1].content
    assert "conclude" in chain.steps[2].content


def test_extended_parser_parse_bulleted():
    """Test parsing bulleted reasoning steps."""
    from rotalabs_audit import ExtendedReasoningParser

    parser = ExtendedReasoningParser()
    text = """
    - First consideration is A
    - Second consideration is B
    - Final conclusion is C
    """

    chain = parser.parse(text)

    assert len(chain.steps) >= 2


def test_extended_parser_empty_input():
    """Test parsing empty input."""
    from rotalabs_audit import ExtendedReasoningParser

    parser = ExtendedReasoningParser()
    chain = parser.parse("")

    assert len(chain.steps) == 0


def test_extended_parser_single_step():
    """Test parsing single step reasoning."""
    from rotalabs_audit import ExtendedReasoningParser

    parser = ExtendedReasoningParser()
    text = "1. The answer is simply 42."

    chain = parser.parse(text)

    assert len(chain.steps) == 1
    assert "42" in chain.steps[0].content


def test_confidence_estimation():
    """Test confidence estimation from text."""
    from rotalabs_audit import estimate_confidence, get_confidence_level

    # High confidence text
    high_conf_text = "I am definitely certain that this is correct"
    high_score = estimate_confidence(high_conf_text)
    assert high_score > 0.5

    # Low confidence text
    low_conf_text = "I think maybe possibly this could be right"
    low_score = estimate_confidence(low_conf_text)
    assert low_score < high_score


def test_confidence_level_mapping():
    """Test confidence level enum mapping."""
    from rotalabs_audit import get_confidence_level, ConfidenceLevel

    # Very high confidence
    level = get_confidence_level(0.9)
    assert level == ConfidenceLevel.VERY_HIGH

    # Low confidence
    level = get_confidence_level(0.2)
    assert level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]


def test_aggregate_confidence():
    """Test aggregating multiple confidence scores."""
    from rotalabs_audit import aggregate_confidence

    scores = [0.8, 0.9, 0.7]
    aggregated = aggregate_confidence(scores)

    assert 0.7 <= aggregated <= 0.9


def test_reasoning_patterns_structure():
    """Test that reasoning patterns are properly structured."""
    from rotalabs_audit import REASONING_PATTERNS

    # Check expected keys exist
    expected_keys = ["meta_reasoning", "goal_reasoning", "evaluation_aware"]

    for key in expected_keys:
        assert key in REASONING_PATTERNS, f"Missing pattern category: {key}"
        assert isinstance(REASONING_PATTERNS[key], list), f"{key} should be a list"
        assert len(REASONING_PATTERNS[key]) > 0, f"{key} should not be empty"


def test_step_format_detection():
    """Test step format detection."""
    from rotalabs_audit import StepFormat

    assert StepFormat.NUMBERED.value == "numbered"
    assert StepFormat.BULLET.value == "bullet"
    assert StepFormat.PROSE.value == "prose"
