"""Tests for verifying package imports and exports."""

import pytest


def test_version():
    """Check version is '0.1.0'."""
    from rotalabs_audit import __version__

    assert __version__ == "0.1.0"


def test_core_imports():
    """Test all core type imports."""
    from rotalabs_audit import (
        # Types
        AwarenessAnalysis,
        ConfidenceLevel,
        DecisionPath,
        DecisionTrace,
        QualityMetrics,
        ReasoningChain,
        ReasoningStep,
        ReasoningType,
        # Configurations
        AnalysisConfig,
        AuditConfig,
        ParserConfig,
        TracingConfig,
        # Exceptions
        AnalysisError,
        AuditError,
        IntegrationError,
        ParsingError,
        TimeoutError,
        TracingError,
        ValidationError,
    )

    # Verify enums
    assert ReasoningType.GOAL_REASONING.value == "goal_reasoning"
    assert ReasoningType.DECISION_MAKING.value == "decision_making"
    assert ConfidenceLevel.HIGH.value == "high"

    # Verify classes are importable
    assert ReasoningStep is not None
    assert ReasoningChain is not None
    assert DecisionTrace is not None
    assert DecisionPath is not None
    assert QualityMetrics is not None
    assert AwarenessAnalysis is not None

    # Verify configs
    assert ParserConfig is not None
    assert AnalysisConfig is not None
    assert TracingConfig is not None
    assert AuditConfig is not None

    # Verify exceptions are exception subclasses
    assert issubclass(AuditError, Exception)
    assert issubclass(ParsingError, Exception)
    assert issubclass(AnalysisError, Exception)
    assert issubclass(TracingError, Exception)
    assert issubclass(ValidationError, Exception)
    assert issubclass(IntegrationError, Exception)


def test_chains_imports():
    """Test chains module imports."""
    from rotalabs_audit import (
        # Extended parser
        ExtendedReasoningParser,
        ExtendedReasoningChain,
        ExtendedReasoningStep,
        ExtendedParserConfig,
        ExtendedReasoningType,
        ExtendedConfidenceLevel,
        StepFormat,
        # Confidence functions
        estimate_confidence,
        get_confidence_level,
        aggregate_confidence,
        analyze_confidence_distribution,
        # Patterns
        REASONING_PATTERNS,
        CONFIDENCE_INDICATORS,
        REASONING_DEPTH_PATTERNS,
        SELF_AWARENESS_PATTERNS,
        STEP_MARKER_PATTERNS,
    )

    # Verify classes
    assert ExtendedReasoningParser is not None
    assert ExtendedReasoningChain is not None
    assert ExtendedReasoningStep is not None
    assert ExtendedParserConfig is not None

    # Verify enums
    assert StepFormat.NUMBERED.value == "numbered"
    assert StepFormat.BULLET.value == "bullet"  # Actual value is "bullet"

    # Verify functions are callable
    assert callable(estimate_confidence)
    assert callable(get_confidence_level)
    assert callable(aggregate_confidence)
    assert callable(analyze_confidence_distribution)

    # Verify pattern dicts
    assert isinstance(REASONING_PATTERNS, dict)
    assert isinstance(CONFIDENCE_INDICATORS, dict)
    assert isinstance(REASONING_DEPTH_PATTERNS, dict)
    assert isinstance(SELF_AWARENESS_PATTERNS, list)
    assert isinstance(STEP_MARKER_PATTERNS, dict)


def test_analysis_imports():
    """Test analysis module imports."""
    from rotalabs_audit import (
        # Counterfactual
        CounterfactualAnalyzer,
        CounterfactualResult,
        InterventionType,
        # Awareness
        EvaluationAwarenessDetector,
        AwarenessIndicator,
        StrategicAdaptation,
        # Quality
        ReasoningQualityAssessor,
        QualityIssue,
        # Causal
        CausalAnalyzer,
        CausalAnalysisResult,
        CausalRelation,
    )

    # Verify classes
    assert CounterfactualAnalyzer is not None
    assert CounterfactualResult is not None
    assert EvaluationAwarenessDetector is not None
    assert ReasoningQualityAssessor is not None
    assert CausalAnalyzer is not None

    # Verify enums - use actual value
    assert InterventionType.REMOVE_EVALUATION_AWARENESS.value == "remove_eval_awareness"


def test_tracing_imports():
    """Test tracing module imports."""
    from rotalabs_audit import (
        DecisionTracer,
        DecisionPathAnalyzer,
    )

    assert DecisionTracer is not None
    assert DecisionPathAnalyzer is not None


def test_integration_imports():
    """Test integration module imports."""
    from rotalabs_audit import (
        ComplyIntegration,
        ReasoningAuditEntry,
    )

    assert ComplyIntegration is not None
    assert ReasoningAuditEntry is not None


def test_utils_imports():
    """Test utility imports."""
    from rotalabs_audit import (
        calculate_text_similarity,
        clean_text,
        extract_bullet_list,
        extract_numbered_list,
        find_all_matches,
        generate_id,
        hash_content,
        split_sentences,
        truncate_text,
    )

    # Verify functions are callable
    assert callable(calculate_text_similarity)
    assert callable(clean_text)
    assert callable(extract_bullet_list)
    assert callable(extract_numbered_list)
    assert callable(find_all_matches)
    assert callable(generate_id)
    assert callable(hash_content)
    assert callable(split_sentences)
    assert callable(truncate_text)


def test_all_exports():
    """Verify all __all__ items are importable."""
    import rotalabs_audit

    all_exports = rotalabs_audit.__all__

    for name in all_exports:
        assert hasattr(rotalabs_audit, name), f"Missing export: {name}"
        obj = getattr(rotalabs_audit, name)
        assert obj is not None, f"Export is None: {name}"
