# Core Module

The `rotalabs_audit.core` module provides the foundational data types, configuration classes, and exceptions used throughout the rotalabs-audit package for reasoning chain capture and decision transparency.

## Types

Core data structures for representing reasoning chains, decision traces, and analysis results.

### ReasoningType

Classification enumeration for different kinds of reasoning steps.

::: rotalabs_audit.core.types.ReasoningType
    options:
      show_source: false
      heading_level: 4

### ConfidenceLevel

Discrete confidence levels that map to numeric confidence scores.

::: rotalabs_audit.core.types.ConfidenceLevel
    options:
      show_source: false
      heading_level: 4

### ReasoningStep

A single step in a reasoning chain with classification and confidence.

::: rotalabs_audit.core.types.ReasoningStep
    options:
      show_source: false
      heading_level: 4

### ReasoningChain

A complete chain of reasoning steps from an AI model.

::: rotalabs_audit.core.types.ReasoningChain
    options:
      show_source: false
      heading_level: 4

### DecisionTrace

Trace of a single decision point with context and rationale.

::: rotalabs_audit.core.types.DecisionTrace
    options:
      show_source: false
      heading_level: 4

### DecisionPath

A sequence of related decisions tracking progress toward a goal.

::: rotalabs_audit.core.types.DecisionPath
    options:
      show_source: false
      heading_level: 4

### AwarenessAnalysis

Result of evaluation awareness detection analysis.

::: rotalabs_audit.core.types.AwarenessAnalysis
    options:
      show_source: false
      heading_level: 4

### QualityMetrics

Quality assessment metrics for reasoning chains.

::: rotalabs_audit.core.types.QualityMetrics
    options:
      show_source: false
      heading_level: 4

---

## Configuration

Configuration classes for controlling parser, analysis, and tracing behavior.

### ParserConfig

Configuration for reasoning chain parsing.

::: rotalabs_audit.core.config.ParserConfig
    options:
      show_source: false
      heading_level: 4

### AnalysisConfig

Configuration for reasoning chain analysis features.

::: rotalabs_audit.core.config.AnalysisConfig
    options:
      show_source: false
      heading_level: 4

### TracingConfig

Configuration for decision tracing and persistence.

::: rotalabs_audit.core.config.TracingConfig
    options:
      show_source: false
      heading_level: 4

### AuditConfig

Master configuration combining all audit-related settings.

::: rotalabs_audit.core.config.AuditConfig
    options:
      show_source: false
      heading_level: 4

---

## Exceptions

Custom exceptions for handling errors in parsing, analysis, tracing, and integrations.

### AuditError

Base exception for all rotalabs-audit errors.

::: rotalabs_audit.core.exceptions.AuditError
    options:
      show_source: false
      heading_level: 4

### ParsingError

Exception raised when parsing reasoning chains fails.

::: rotalabs_audit.core.exceptions.ParsingError
    options:
      show_source: false
      heading_level: 4

### AnalysisError

Exception raised when reasoning analysis fails.

::: rotalabs_audit.core.exceptions.AnalysisError
    options:
      show_source: false
      heading_level: 4

### TracingError

Exception raised when decision tracing fails.

::: rotalabs_audit.core.exceptions.TracingError
    options:
      show_source: false
      heading_level: 4

### IntegrationError

Exception raised when integration with external systems fails.

::: rotalabs_audit.core.exceptions.IntegrationError
    options:
      show_source: false
      heading_level: 4

### ValidationError

Exception raised when input validation fails.

::: rotalabs_audit.core.exceptions.ValidationError
    options:
      show_source: false
      heading_level: 4

### TimeoutError

Exception raised when an operation times out.

::: rotalabs_audit.core.exceptions.TimeoutError
    options:
      show_source: false
      heading_level: 4
