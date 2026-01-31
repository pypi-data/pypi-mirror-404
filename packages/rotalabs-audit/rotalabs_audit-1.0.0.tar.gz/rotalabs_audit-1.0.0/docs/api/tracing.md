# Tracing Module

The `rotalabs_audit.tracing` module provides tools for tracing and analyzing AI decision-making, including decision capture, path analysis, and failure point detection.

## Decision Tracing

Tools for capturing and managing decision traces from AI interactions.

### DecisionTracer

Trace and capture decision points in AI reasoning.

::: rotalabs_audit.tracing.decision.DecisionTracer
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - trace_decision
        - start_trace
        - add_decision
        - end_trace
        - get_active_trace_ids
        - cancel_trace
        - extract_alternatives
        - extract_rationale
        - assess_reversibility
        - quick_trace

### ReasoningChainParser

Parser for chain-of-thought reasoning text used in decision tracing.

::: rotalabs_audit.tracing.decision.ReasoningChainParser
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - parse

---

## Decision Path Analysis

Tools for analyzing complete decision paths and identifying patterns.

### DecisionPathAnalyzer

Analyze sequences of decisions in a decision path.

::: rotalabs_audit.tracing.path.DecisionPathAnalyzer
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - analyze_path
        - find_critical_decisions
        - find_failure_point
        - calculate_path_confidence
        - summarize_path
        - compare_paths
        - find_divergence_point
        - get_confidence_trend
        - detect_confidence_decline
