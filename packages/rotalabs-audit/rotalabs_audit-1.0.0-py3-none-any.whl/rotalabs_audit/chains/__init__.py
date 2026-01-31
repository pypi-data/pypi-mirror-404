"""
Extended reasoning chain parsing and pattern analysis.

This submodule provides enhanced pattern-based reasoning analysis beyond
the core parser. It includes comprehensive pattern libraries for detecting
various types of reasoning, confidence estimation from linguistic markers,
and utilities for analyzing reasoning distributions.

This module complements the core `rotalabs_audit.core.parser.ReasoningChainParser`
with additional capabilities:

1. **Extensive Pattern Library**: Comprehensive regex patterns for detecting
   evaluation awareness, goal reasoning, meta-cognition, and more.

2. **Confidence Estimation**: Linguistic analysis of confidence markers
   (hedging, certainty expressions) to estimate confidence levels.

3. **Distribution Analysis**: Tools for analyzing confidence distributions
   across reasoning chains.

4. **Format Detection**: Automatic detection of reasoning format (numbered,
   bulleted, prose, etc.).

Key Components:
    - ExtendedReasoningParser: Enhanced parser with rich pattern matching
    - estimate_confidence: Estimate confidence from linguistic markers
    - aggregate_confidence: Combine confidence scores across steps
    - REASONING_PATTERNS: Comprehensive pattern library by reasoning type
    - CONFIDENCE_INDICATORS: Patterns for high/low confidence language

Basic Usage:
    >>> from rotalabs_audit.chains import (
    ...     ExtendedReasoningParser,
    ...     estimate_confidence,
    ...     REASONING_PATTERNS,
    ... )
    >>> parser = ExtendedReasoningParser()
    >>> chain = parser.parse('''
    ...     1. First, I need to understand the problem
    ...     2. I think the answer involves multiplication
    ...     3. Therefore, the result is 42
    ... ''')
    >>> print(f"Steps: {len(chain)}, Confidence: {chain.aggregate_confidence:.2f}")

Confidence Analysis:
    >>> from rotalabs_audit.chains import (
    ...     estimate_confidence,
    ...     get_confidence_level,
    ...     aggregate_confidence,
    ... )
    >>> score = estimate_confidence("I am definitely sure about this")
    >>> level = get_confidence_level(score)
    >>> print(f"Score: {score:.2f}, Level: {level.value}")
    Score: 0.85, Level: very_high

Pattern Matching:
    >>> import re
    >>> from rotalabs_audit.chains import REASONING_PATTERNS
    >>> text = "I think the goal is to maximize efficiency"
    >>> for pattern in REASONING_PATTERNS["meta_reasoning"]:
    ...     if re.search(pattern, text, re.IGNORECASE):
    ...         print(f"Found meta-reasoning: {pattern}")

Integration with Core Parser:
    The chains module can be used alongside the core parser. Use the core
    parser for structured reasoning extraction and this module for deeper
    linguistic analysis:

    >>> from rotalabs_audit.core import ReasoningChainParser
    >>> from rotalabs_audit.chains import estimate_confidence, analyze_confidence_distribution
    >>>
    >>> core_parser = ReasoningChainParser()
    >>> chain = core_parser.parse(text)
    >>> confidences = [estimate_confidence(step.content) for step in chain.steps]
    >>> distribution = analyze_confidence_distribution(confidences)
"""

from .confidence import (
    ConfidenceLevel as ExtendedConfidenceLevel,
    aggregate_confidence,
    analyze_confidence_distribution,
    estimate_confidence,
    get_confidence_level,
)
from .parser import (
    ParserConfig as ExtendedParserConfig,
    ReasoningChain as ExtendedReasoningChain,
    ReasoningChainParser as ExtendedReasoningParser,
    ReasoningStep as ExtendedReasoningStep,
    ReasoningType as ExtendedReasoningType,
    StepFormat,
)
from .patterns import (
    CONFIDENCE_INDICATORS,
    REASONING_DEPTH_PATTERNS,
    REASONING_PATTERNS,
    SELF_AWARENESS_PATTERNS,
    STEP_MARKER_PATTERNS,
)

__all__ = [
    # Extended parser classes (aliased to avoid confusion with core)
    "ExtendedReasoningParser",
    "ExtendedReasoningChain",
    "ExtendedReasoningStep",
    "ExtendedParserConfig",
    # Extended enums
    "ExtendedReasoningType",
    "ExtendedConfidenceLevel",
    "StepFormat",
    # Confidence functions (primary export from this module)
    "estimate_confidence",
    "get_confidence_level",
    "aggregate_confidence",
    "analyze_confidence_distribution",
    # Pattern dictionaries (primary export from this module)
    "REASONING_PATTERNS",
    "CONFIDENCE_INDICATORS",
    "REASONING_DEPTH_PATTERNS",
    "SELF_AWARENESS_PATTERNS",
    "STEP_MARKER_PATTERNS",
]
