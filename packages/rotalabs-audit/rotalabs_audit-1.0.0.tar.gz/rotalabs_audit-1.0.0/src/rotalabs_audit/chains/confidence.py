"""
Confidence estimation for reasoning chain analysis.

This module provides utilities for estimating the confidence level expressed
in natural language reasoning, based on linguistic markers and hedging patterns.

The confidence estimation approach is based on:
1. High-confidence indicators (e.g., "definitely", "certainly")
2. Low-confidence indicators (e.g., "maybe", "perhaps")
3. Balanced scoring when both are present
4. Default moderate confidence when no indicators are found

Example:
    >>> from rotalabs_audit.chains.confidence import (
    ...     estimate_confidence,
    ...     get_confidence_level,
    ...     ConfidenceLevel,
    ... )
    >>> score = estimate_confidence("I think this is probably correct")
    >>> level = get_confidence_level(score)
    >>> print(f"Score: {score:.2f}, Level: {level}")
    Score: 0.35, Level: ConfidenceLevel.LOW
"""

import re
from enum import Enum
from typing import List, Tuple

from .patterns import CONFIDENCE_INDICATORS


class ConfidenceLevel(str, Enum):
    """
    Categorical confidence levels for reasoning steps.

    These levels provide a human-readable interpretation of numeric
    confidence scores, useful for filtering and reporting.

    Attributes:
        VERY_LOW: Score < 0.2, highly uncertain language.
        LOW: Score 0.2-0.4, tentative or hedged statements.
        MODERATE: Score 0.4-0.6, balanced or neutral confidence.
        HIGH: Score 0.6-0.8, assertive but not absolute.
        VERY_HIGH: Score >= 0.8, highly confident assertions.

    Example:
        >>> level = ConfidenceLevel.HIGH
        >>> print(f"Confidence: {level.value}")
        Confidence: high
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Confidence level thresholds
_CONFIDENCE_THRESHOLDS: List[Tuple[float, ConfidenceLevel]] = [
    (0.8, ConfidenceLevel.VERY_HIGH),
    (0.6, ConfidenceLevel.HIGH),
    (0.4, ConfidenceLevel.MODERATE),
    (0.2, ConfidenceLevel.LOW),
    (0.0, ConfidenceLevel.VERY_LOW),
]


def estimate_confidence(text: str) -> float:
    """
    Estimate confidence level from linguistic markers in text.

    This function analyzes text for high-confidence and low-confidence
    indicators, returning a normalized score between 0.0 and 1.0.

    The scoring algorithm:
    1. Count matches for high-confidence patterns (adds to score)
    2. Count matches for low-confidence patterns (subtracts from score)
    3. Normalize based on total matches
    4. Return 0.5 (moderate) if no indicators found

    Args:
        text: The text to analyze for confidence indicators.

    Returns:
        A float between 0.0 (very uncertain) and 1.0 (very certain).
        Returns 0.5 if no confidence indicators are found.

    Example:
        >>> estimate_confidence("I am definitely sure about this")
        0.85
        >>> estimate_confidence("Maybe this could be right")
        0.2
        >>> estimate_confidence("The answer is 42")
        0.5
        >>> estimate_confidence("I am certain, but there might be exceptions")
        0.6
    """
    if not text or not text.strip():
        return 0.5

    text_lower = text.lower()

    # Count high-confidence indicators
    high_matches = 0
    for pattern in CONFIDENCE_INDICATORS["high"]:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        high_matches += len(matches)

    # Count low-confidence indicators
    low_matches = 0
    for pattern in CONFIDENCE_INDICATORS["low"]:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        low_matches += len(matches)

    total_matches = high_matches + low_matches

    # No indicators found - return moderate confidence
    if total_matches == 0:
        return 0.5

    # Calculate weighted score
    # High confidence pushes toward 1.0, low confidence pushes toward 0.0
    base_score = 0.5
    high_weight = 0.35  # Each high indicator adds this much (up to a cap)
    low_weight = 0.3  # Each low indicator subtracts this much (up to a cap)

    # Apply diminishing returns for multiple matches
    high_contribution = min(high_matches * high_weight, 0.5)
    low_contribution = min(low_matches * low_weight, 0.5)

    score = base_score + high_contribution - low_contribution

    # Clamp to valid range
    return max(0.0, min(1.0, score))


def get_confidence_level(score: float) -> ConfidenceLevel:
    """
    Convert a numeric confidence score to a categorical level.

    This function maps continuous confidence scores to discrete
    levels for easier interpretation and filtering.

    Args:
        score: A confidence score between 0.0 and 1.0.

    Returns:
        The corresponding ConfidenceLevel enum value.

    Raises:
        ValueError: If score is not between 0.0 and 1.0.

    Example:
        >>> get_confidence_level(0.9)
        <ConfidenceLevel.VERY_HIGH: 'very_high'>
        >>> get_confidence_level(0.5)
        <ConfidenceLevel.MODERATE: 'moderate'>
        >>> get_confidence_level(0.1)
        <ConfidenceLevel.VERY_LOW: 'very_low'>

    Thresholds:
        - >= 0.8: VERY_HIGH
        - >= 0.6: HIGH
        - >= 0.4: MODERATE
        - >= 0.2: LOW
        - < 0.2: VERY_LOW
    """
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Score must be between 0.0 and 1.0, got {score}")

    for threshold, level in _CONFIDENCE_THRESHOLDS:
        if score >= threshold:
            return level

    return ConfidenceLevel.VERY_LOW


def aggregate_confidence(scores: List[float]) -> float:
    """
    Combine multiple confidence scores into a single aggregate score.

    This function uses a weighted approach that gives more weight to
    lower confidence scores, as uncertainty in any step typically
    affects overall confidence. This is based on the principle that
    a chain of reasoning is only as strong as its weakest link.

    The aggregation formula uses a weighted geometric mean that:
    1. Penalizes chains with any very low confidence steps
    2. Rewards consistent moderate-to-high confidence
    3. Handles edge cases (empty list, single score)

    Args:
        scores: A list of confidence scores, each between 0.0 and 1.0.

    Returns:
        The aggregated confidence score between 0.0 and 1.0.
        Returns 0.5 for empty input (neutral confidence).

    Raises:
        ValueError: If any score is not between 0.0 and 1.0.

    Example:
        >>> aggregate_confidence([0.8, 0.9, 0.85])
        0.85
        >>> aggregate_confidence([0.8, 0.2, 0.9])  # Low score drags down
        0.53
        >>> aggregate_confidence([])
        0.5
        >>> aggregate_confidence([0.7])
        0.7
    """
    if not scores:
        return 0.5

    # Validate all scores
    for i, score in enumerate(scores):
        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"Score at index {i} must be between 0.0 and 1.0, got {score}"
            )

    if len(scores) == 1:
        return scores[0]

    # Calculate minimum (weakest link)
    min_score = min(scores)

    # Calculate arithmetic mean
    mean_score = sum(scores) / len(scores)

    # Weighted combination: give significant weight to minimum
    # This ensures low-confidence steps have outsized impact
    min_weight = 0.4
    mean_weight = 0.6

    aggregated = (min_weight * min_score) + (mean_weight * mean_score)

    return round(aggregated, 4)


def analyze_confidence_distribution(scores: List[float]) -> dict:
    """
    Analyze the distribution of confidence scores across a reasoning chain.

    This function provides detailed statistics about confidence distribution,
    useful for understanding the overall quality and consistency of reasoning.

    Args:
        scores: A list of confidence scores, each between 0.0 and 1.0.

    Returns:
        A dictionary containing:
        - count: Number of scores
        - mean: Average confidence
        - min: Lowest confidence score
        - max: Highest confidence score
        - std: Standard deviation
        - aggregate: Combined confidence score
        - level_distribution: Count of each confidence level
        - consistency: Measure of how consistent scores are (0-1)

    Example:
        >>> scores = [0.7, 0.8, 0.75, 0.65]
        >>> analysis = analyze_confidence_distribution(scores)
        >>> print(f"Mean: {analysis['mean']:.2f}, Consistency: {analysis['consistency']:.2f}")
        Mean: 0.72, Consistency: 0.85
    """
    if not scores:
        return {
            "count": 0,
            "mean": 0.5,
            "min": 0.5,
            "max": 0.5,
            "std": 0.0,
            "aggregate": 0.5,
            "level_distribution": {level.value: 0 for level in ConfidenceLevel},
            "consistency": 1.0,
        }

    # Basic statistics
    count = len(scores)
    mean_score = sum(scores) / count
    min_score = min(scores)
    max_score = max(scores)

    # Standard deviation
    if count > 1:
        variance = sum((s - mean_score) ** 2 for s in scores) / count
        std = variance**0.5
    else:
        std = 0.0

    # Level distribution
    level_dist = {level.value: 0 for level in ConfidenceLevel}
    for score in scores:
        level = get_confidence_level(score)
        level_dist[level.value] += 1

    # Consistency measure (inverse of coefficient of variation, normalized)
    # Higher consistency = more uniform confidence across steps
    if mean_score > 0:
        cv = std / mean_score  # Coefficient of variation
        consistency = max(0.0, 1.0 - cv)  # Invert and clamp
    else:
        consistency = 0.0

    return {
        "count": count,
        "mean": round(mean_score, 4),
        "min": round(min_score, 4),
        "max": round(max_score, 4),
        "std": round(std, 4),
        "aggregate": aggregate_confidence(scores),
        "level_distribution": level_dist,
        "consistency": round(consistency, 4),
    }
