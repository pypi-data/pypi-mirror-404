# Chains Module

The `rotalabs_audit.chains` module provides extended reasoning chain parsing and pattern analysis capabilities. It includes comprehensive pattern libraries for detecting various types of reasoning, confidence estimation from linguistic markers, and utilities for analyzing reasoning distributions.

This module complements the core parser with additional capabilities:

- **Extensive Pattern Library**: Comprehensive regex patterns for detecting evaluation awareness, goal reasoning, meta-cognition, and more.
- **Confidence Estimation**: Linguistic analysis of confidence markers (hedging, certainty expressions) to estimate confidence levels.
- **Distribution Analysis**: Tools for analyzing confidence distributions across reasoning chains.
- **Format Detection**: Automatic detection of reasoning format (numbered, bulleted, prose, etc.).

## Parser Classes

### ExtendedReasoningParser

Enhanced reasoning chain parser with rich pattern matching capabilities.

::: rotalabs_audit.chains.parser.ReasoningChainParser
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - parse
        - parse_step
        - classify_reasoning_type
        - split_into_steps

### ExtendedReasoningChain

A complete chain of reasoning steps with aggregate statistics.

::: rotalabs_audit.chains.parser.ReasoningChain
    options:
      show_source: false
      heading_level: 4

### ExtendedReasoningStep

A single step in a reasoning chain with classification and metadata.

::: rotalabs_audit.chains.parser.ReasoningStep
    options:
      show_source: false
      heading_level: 4

### ExtendedParserConfig

Configuration for the extended reasoning chain parser.

::: rotalabs_audit.chains.parser.ParserConfig
    options:
      show_source: false
      heading_level: 4

---

## Enumerations

### ExtendedReasoningType

Categories of reasoning detected in model outputs.

::: rotalabs_audit.chains.parser.ReasoningType
    options:
      show_source: false
      heading_level: 4

### ExtendedConfidenceLevel

Categorical confidence levels for reasoning steps.

::: rotalabs_audit.chains.confidence.ConfidenceLevel
    options:
      show_source: false
      heading_level: 4

### StepFormat

Detected format of reasoning step markers.

::: rotalabs_audit.chains.parser.StepFormat
    options:
      show_source: false
      heading_level: 4

---

## Confidence Functions

Functions for estimating and aggregating confidence from linguistic markers.

### estimate_confidence

Estimate confidence level from linguistic markers in text.

::: rotalabs_audit.chains.confidence.estimate_confidence
    options:
      show_source: false
      heading_level: 4

### get_confidence_level

Convert a numeric confidence score to a categorical level.

::: rotalabs_audit.chains.confidence.get_confidence_level
    options:
      show_source: false
      heading_level: 4

### aggregate_confidence

Combine multiple confidence scores into a single aggregate score.

::: rotalabs_audit.chains.confidence.aggregate_confidence
    options:
      show_source: false
      heading_level: 4

### analyze_confidence_distribution

Analyze the distribution of confidence scores across a reasoning chain.

::: rotalabs_audit.chains.confidence.analyze_confidence_distribution
    options:
      show_source: false
      heading_level: 4

---

## Pattern Dictionaries

Pre-defined pattern dictionaries for reasoning type classification and confidence estimation.

### REASONING_PATTERNS

Pattern categories for classifying reasoning types. Contains regex patterns organized by category:

- `evaluation_aware`: Patterns indicating awareness of being evaluated
- `goal_reasoning`: Goal-directed reasoning patterns
- `decision_making`: Decision and choice patterns
- `meta_reasoning`: Meta-cognitive patterns ("I think", "I believe")
- `uncertainty`: Uncertainty and hedging patterns
- `incentive_reasoning`: Incentive-related patterns
- `causal_reasoning`: Cause-and-effect patterns
- `hypothetical`: Hypothetical and "what if" patterns

::: rotalabs_audit.chains.patterns.REASONING_PATTERNS
    options:
      show_source: true
      heading_level: 4

### CONFIDENCE_INDICATORS

Patterns for high and low confidence linguistic markers:

- `high`: Certainty markers ("definitely", "certainly", "clearly")
- `low`: Uncertainty markers ("perhaps", "maybe", "might")

::: rotalabs_audit.chains.patterns.CONFIDENCE_INDICATORS
    options:
      show_source: true
      heading_level: 4

### REASONING_DEPTH_PATTERNS

Patterns for detecting reasoning depth (surface vs. deep analysis):

- `surface`: Surface-level indicators ("obviously", "simply", "just")
- `deep`: Deep analysis indicators ("fundamentally", "at the core", "root cause")

::: rotalabs_audit.chains.patterns.REASONING_DEPTH_PATTERNS
    options:
      show_source: true
      heading_level: 4

### SELF_AWARENESS_PATTERNS

Patterns indicating self-awareness or introspection about AI capabilities.

::: rotalabs_audit.chains.patterns.SELF_AWARENESS_PATTERNS
    options:
      show_source: true
      heading_level: 4

### STEP_MARKER_PATTERNS

Patterns for detecting structured reasoning step markers (numbered, bulleted, sequential words).

::: rotalabs_audit.chains.patterns.STEP_MARKER_PATTERNS
    options:
      show_source: true
      heading_level: 4
