"""
rotalabs-audit - Reasoning chain capture for auditing AI systems.

This package provides tools for capturing, parsing, and analyzing reasoning
chains from AI model outputs. It enables auditing of AI decision-making
processes for transparency, compliance, and safety analysis.

Key Features:
    - Parse natural language reasoning into structured chains
    - Classify reasoning types (goal, decision, meta-reasoning, etc.)
    - Trace and record decision paths for transparency
    - Detect evaluation awareness in AI outputs
    - Assess reasoning quality with comprehensive metrics
    - Perform counterfactual analysis on reasoning chains
    - Integration with rotalabs-comply for compliance reporting

https://rotalabs.ai
"""

from rotalabs_audit._version import __version__

# Core types, configs, and exceptions
from rotalabs_audit.core import (
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

# Chains module - extended parsing and pattern analysis
from rotalabs_audit.chains import (
    # Extended parser classes
    ExtendedReasoningParser,
    ExtendedReasoningChain,
    ExtendedReasoningStep,
    ExtendedParserConfig,
    # Extended enums
    ExtendedReasoningType,
    ExtendedConfidenceLevel,
    StepFormat,
    # Confidence functions
    estimate_confidence,
    get_confidence_level,
    aggregate_confidence,
    analyze_confidence_distribution,
    # Pattern dictionaries
    REASONING_PATTERNS,
    CONFIDENCE_INDICATORS,
    REASONING_DEPTH_PATTERNS,
    SELF_AWARENESS_PATTERNS,
    STEP_MARKER_PATTERNS,
)

# Analysis module
from rotalabs_audit.analysis import (
    # Counterfactual analysis
    CounterfactualAnalyzer,
    CounterfactualResult,
    InterventionType,
    # Evaluation awareness
    EvaluationAwarenessDetector,
    AwarenessIndicator,
    StrategicAdaptation,
    # Quality assessment
    ReasoningQualityAssessor,
    QualityIssue,
    # Causal analysis
    CausalAnalyzer,
    CausalAnalysisResult,
    CausalRelation,
)

# Tracing module
from rotalabs_audit.tracing import (
    DecisionTracer,
    DecisionPathAnalyzer,
)

# Integration module
from rotalabs_audit.integration import (
    ComplyIntegration,
    ReasoningAuditEntry,
)

# Utils module
from rotalabs_audit.utils import (
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

__all__ = [
    "__version__",
    # Core Types
    "AwarenessAnalysis",
    "ConfidenceLevel",
    "DecisionPath",
    "DecisionTrace",
    "QualityMetrics",
    "ReasoningChain",
    "ReasoningStep",
    "ReasoningType",
    # Core Configurations
    "AnalysisConfig",
    "AuditConfig",
    "ParserConfig",
    "TracingConfig",
    # Core Exceptions
    "AnalysisError",
    "AuditError",
    "IntegrationError",
    "ParsingError",
    "TimeoutError",
    "TracingError",
    "ValidationError",
    # Extended Parser (chains module)
    "ExtendedReasoningParser",
    "ExtendedReasoningChain",
    "ExtendedReasoningStep",
    "ExtendedParserConfig",
    "ExtendedReasoningType",
    "ExtendedConfidenceLevel",
    "StepFormat",
    # Confidence Functions
    "estimate_confidence",
    "get_confidence_level",
    "aggregate_confidence",
    "analyze_confidence_distribution",
    # Pattern Dictionaries
    "REASONING_PATTERNS",
    "CONFIDENCE_INDICATORS",
    "REASONING_DEPTH_PATTERNS",
    "SELF_AWARENESS_PATTERNS",
    "STEP_MARKER_PATTERNS",
    # Analysis - Counterfactual
    "CounterfactualAnalyzer",
    "CounterfactualResult",
    "InterventionType",
    # Analysis - Awareness
    "EvaluationAwarenessDetector",
    "AwarenessIndicator",
    "StrategicAdaptation",
    # Analysis - Quality
    "ReasoningQualityAssessor",
    "QualityIssue",
    # Analysis - Causal
    "CausalAnalyzer",
    "CausalAnalysisResult",
    "CausalRelation",
    # Tracing
    "DecisionTracer",
    "DecisionPathAnalyzer",
    # Integration
    "ComplyIntegration",
    "ReasoningAuditEntry",
    # Utils
    "calculate_text_similarity",
    "clean_text",
    "extract_bullet_list",
    "extract_numbered_list",
    "find_all_matches",
    "generate_id",
    "hash_content",
    "split_sentences",
    "truncate_text",
]
