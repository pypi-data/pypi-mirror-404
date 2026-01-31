"""
Core module for rotalabs-audit.

This module exports all core types, configurations, and exceptions used
throughout the rotalabs-audit package for reasoning chain capture and
decision transparency.
"""

from rotalabs_audit.core.types import (
    AwarenessAnalysis,
    ConfidenceLevel,
    DecisionPath,
    DecisionTrace,
    QualityMetrics,
    ReasoningChain,
    ReasoningStep,
    ReasoningType,
)

from rotalabs_audit.core.config import (
    AnalysisConfig,
    AuditConfig,
    ParserConfig,
    TracingConfig,
)

from rotalabs_audit.core.exceptions import (
    AnalysisError,
    AuditError,
    IntegrationError,
    ParsingError,
    TimeoutError,
    TracingError,
    ValidationError,
)

__all__ = [
    # Types
    "AwarenessAnalysis",
    "ConfidenceLevel",
    "DecisionPath",
    "DecisionTrace",
    "QualityMetrics",
    "ReasoningChain",
    "ReasoningStep",
    "ReasoningType",
    # Configurations
    "AnalysisConfig",
    "AuditConfig",
    "ParserConfig",
    "TracingConfig",
    # Exceptions
    "AnalysisError",
    "AuditError",
    "IntegrationError",
    "ParsingError",
    "TimeoutError",
    "TracingError",
    "ValidationError",
]
