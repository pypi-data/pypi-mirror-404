"""
Configuration classes for rotalabs-audit.

This module provides configuration dataclasses for controlling the behavior
of reasoning chain parsing, analysis, and decision tracing components.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ParserConfig:
    """
    Configuration for reasoning chain parsing.

    Controls how raw model outputs are parsed into structured reasoning
    chains, including pattern matching settings and output constraints.

    Attributes:
        patterns_file: Path to a YAML/JSON file containing custom patterns
            for identifying reasoning steps. If None, uses built-in patterns.
        min_confidence: Minimum confidence threshold for including a parsed
            step. Steps below this threshold are discarded.
        max_steps: Maximum number of steps to extract from a single chain.
            Prevents runaway parsing on very long outputs.
        step_separator_patterns: List of regex patterns that indicate
            boundaries between reasoning steps.
        include_raw_evidence: Whether to include raw pattern match strings
            in the evidence field of parsed steps.
        normalize_whitespace: Whether to normalize whitespace in parsed
            content (collapse multiple spaces, trim, etc.).
        preserve_formatting: Whether to preserve markdown/code formatting
            in step content.
        timeout_seconds: Maximum time allowed for parsing a single chain.
            Prevents hanging on adversarial inputs.

    Example:
        >>> config = ParserConfig(
        ...     min_confidence=0.6,
        ...     max_steps=20,
        ...     include_raw_evidence=True
        ... )
    """
    patterns_file: Optional[Path] = None
    min_confidence: float = 0.5
    max_steps: int = 50
    step_separator_patterns: List[str] = field(default_factory=lambda: [
        r"^\d+\.",           # Numbered lists: "1.", "2.", etc.
        r"^[-*]",            # Bullet points
        r"^(First|Second|Third|Then|Next|Finally|Therefore|Thus|Hence)",
        r"^(Step \d+)",      # Explicit steps
        r"\n\n",             # Double newlines
    ])
    include_raw_evidence: bool = True
    normalize_whitespace: bool = True
    preserve_formatting: bool = True
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not 0 <= self.min_confidence <= 1:
            raise ValueError(
                f"min_confidence must be between 0 and 1, got {self.min_confidence}"
            )
        if self.max_steps < 1:
            raise ValueError(f"max_steps must be at least 1, got {self.max_steps}")
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, got {self.timeout_seconds}"
            )
        if self.patterns_file is not None:
            self.patterns_file = Path(self.patterns_file)


@dataclass
class AnalysisConfig:
    """
    Configuration for reasoning chain analysis.

    Controls which analysis features are enabled and their parameters.
    Analysis includes evaluation awareness detection, quality assessment,
    and counterfactual reasoning analysis.

    Attributes:
        enable_counterfactual: Whether to perform counterfactual analysis,
            examining what would happen if certain reasoning steps were
            different.
        enable_awareness: Whether to detect evaluation awareness, checking
            if the model appears to know it's being tested.
        enable_quality: Whether to compute quality metrics for reasoning
            chains.
        awareness_threshold: Score threshold above which a chain is
            considered evaluation-aware.
        quality_weights: Dictionary of weights for different quality
            dimensions when computing overall score.
        counterfactual_depth: How many alternative branches to explore
            in counterfactual analysis.
        use_llm_analysis: Whether to use an LLM for deeper analysis
            (requires API credentials).
        llm_model: Model identifier for LLM-based analysis.
        cache_results: Whether to cache analysis results for repeated
            calls on the same input.
        parallel_analysis: Whether to run independent analyses in parallel.

    Example:
        >>> config = AnalysisConfig(
        ...     enable_awareness=True,
        ...     awareness_threshold=0.7,
        ...     enable_quality=True
        ... )
    """
    enable_counterfactual: bool = False
    enable_awareness: bool = True
    enable_quality: bool = True
    awareness_threshold: float = 0.5
    quality_weights: Dict[str, float] = field(default_factory=lambda: {
        "clarity": 0.2,
        "completeness": 0.2,
        "consistency": 0.2,
        "logical_validity": 0.25,
        "evidence_support": 0.15,
    })
    counterfactual_depth: int = 3
    use_llm_analysis: bool = False
    llm_model: Optional[str] = None
    cache_results: bool = True
    parallel_analysis: bool = True

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not 0 <= self.awareness_threshold <= 1:
            raise ValueError(
                f"awareness_threshold must be between 0 and 1, "
                f"got {self.awareness_threshold}"
            )
        if self.counterfactual_depth < 1:
            raise ValueError(
                f"counterfactual_depth must be at least 1, "
                f"got {self.counterfactual_depth}"
            )
        # Validate quality weights sum to approximately 1.0
        weight_sum = sum(self.quality_weights.values())
        if not 0.99 <= weight_sum <= 1.01:
            raise ValueError(
                f"quality_weights should sum to 1.0, got {weight_sum}"
            )
        # Validate all weights are non-negative
        for key, value in self.quality_weights.items():
            if value < 0:
                raise ValueError(
                    f"Quality weight '{key}' must be non-negative, got {value}"
                )


@dataclass
class TracingConfig:
    """
    Configuration for decision tracing.

    Controls how decisions are captured, tracked, and organized into
    decision paths during AI system operation.

    Attributes:
        capture_alternatives: Whether to capture alternative decisions
            that were considered but not taken.
        max_trace_depth: Maximum depth of nested decision traces.
            Prevents unbounded recursion in complex decision trees.
        max_path_length: Maximum number of decisions in a single path.
        capture_context: Whether to capture contextual information
            at each decision point.
        context_keys: Specific context keys to capture (if None, captures all).
        include_reasoning_chain: Whether to parse and include the full
            reasoning chain for each decision.
        track_consequences: Whether to track predicted and actual
            consequences of decisions.
        enable_timestamps: Whether to record precise timestamps for
            each decision.
        persistence_backend: Backend for persisting traces ("memory",
            "sqlite", "postgres", or None for no persistence).
        persistence_path: Path or connection string for persistence backend.
        auto_flush_interval: Seconds between automatic flushes to persistence
            (0 disables auto-flush).

    Example:
        >>> config = TracingConfig(
        ...     capture_alternatives=True,
        ...     max_trace_depth=10,
        ...     include_reasoning_chain=True,
        ...     persistence_backend="sqlite",
        ...     persistence_path="./traces.db"
        ... )
    """
    capture_alternatives: bool = True
    max_trace_depth: int = 20
    max_path_length: int = 100
    capture_context: bool = True
    context_keys: Optional[List[str]] = None
    include_reasoning_chain: bool = True
    track_consequences: bool = True
    enable_timestamps: bool = True
    persistence_backend: Optional[str] = None
    persistence_path: Optional[str] = None
    auto_flush_interval: float = 0.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.max_trace_depth < 1:
            raise ValueError(
                f"max_trace_depth must be at least 1, got {self.max_trace_depth}"
            )
        if self.max_path_length < 1:
            raise ValueError(
                f"max_path_length must be at least 1, got {self.max_path_length}"
            )
        if self.auto_flush_interval < 0:
            raise ValueError(
                f"auto_flush_interval must be non-negative, "
                f"got {self.auto_flush_interval}"
            )
        valid_backends = {None, "memory", "sqlite", "postgres"}
        if self.persistence_backend not in valid_backends:
            raise ValueError(
                f"persistence_backend must be one of {valid_backends}, "
                f"got {self.persistence_backend}"
            )
        # Validate that persistence_path is provided if backend requires it
        if self.persistence_backend in ("sqlite", "postgres"):
            if not self.persistence_path:
                raise ValueError(
                    f"persistence_path is required for {self.persistence_backend} backend"
                )


@dataclass
class AuditConfig:
    """
    Master configuration combining all audit-related settings.

    Provides a unified configuration object that contains parser, analysis,
    and tracing configurations, along with global settings.

    Attributes:
        parser: Configuration for reasoning chain parsing.
        analysis: Configuration for reasoning analysis.
        tracing: Configuration for decision tracing.
        debug: Whether to enable debug mode with verbose logging.
        log_level: Logging level ("DEBUG", "INFO", "WARNING", "ERROR").
        metadata: Additional global metadata to include in all outputs.

    Example:
        >>> config = AuditConfig(
        ...     parser=ParserConfig(min_confidence=0.6),
        ...     analysis=AnalysisConfig(enable_awareness=True),
        ...     tracing=TracingConfig(capture_alternatives=True),
        ...     debug=True
        ... )
    """
    parser: ParserConfig = field(default_factory=ParserConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    debug: bool = False
    log_level: str = "INFO"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration values."""
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"log_level must be one of {valid_log_levels}, got {self.log_level}"
            )
        self.log_level = self.log_level.upper()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditConfig":
        """
        Create an AuditConfig from a dictionary.

        Useful for loading configuration from files or environment.

        Args:
            data: Dictionary containing configuration values.

        Returns:
            Configured AuditConfig instance.
        """
        parser_data = data.get("parser", {})
        analysis_data = data.get("analysis", {})
        tracing_data = data.get("tracing", {})

        return cls(
            parser=ParserConfig(**parser_data),
            analysis=AnalysisConfig(**analysis_data),
            tracing=TracingConfig(**tracing_data),
            debug=data.get("debug", False),
            log_level=data.get("log_level", "INFO"),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        from dataclasses import asdict
        return asdict(self)
