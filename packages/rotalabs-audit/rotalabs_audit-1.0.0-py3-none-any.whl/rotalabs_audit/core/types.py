"""
Core data models for reasoning chain capture and decision transparency.

This module provides the fundamental data structures used throughout rotalabs-audit
for representing reasoning chains, decision traces, and analysis results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReasoningType(str, Enum):
    """
    Classification of reasoning step types.

    Used to categorize different kinds of reasoning that appear in AI model
    outputs, enabling analysis of reasoning patterns and detection of specific
    behaviors like evaluation awareness or strategic reasoning.

    Attributes:
        EVALUATION_AWARE: References to testing, evaluation, or monitoring context.
            Indicates the model may be aware it's being evaluated.
        GOAL_REASONING: Goal-directed reasoning where the model explicitly
            considers objectives and how to achieve them.
        DECISION_MAKING: Explicit decision points where the model chooses
            between alternatives.
        FACTUAL_KNOWLEDGE: Factual statements or knowledge retrieval without
            significant inference.
        UNCERTAINTY: Expressions of uncertainty, hedging, or acknowledgment
            of limitations.
        META_REASONING: Meta-cognitive statements like "I think" or "I believe"
            that reflect on the reasoning process itself.
        INCENTIVE_REASONING: Consideration of rewards, penalties, or other
            incentive structures.
        CAUSAL_REASONING: Cause-and-effect reasoning, analyzing why things
            happen or predicting consequences.
        HYPOTHETICAL: Counterfactual or "what if" reasoning exploring
            alternative scenarios.
        UNKNOWN: Reasoning that doesn't fit other categories or couldn't
            be classified.
    """
    EVALUATION_AWARE = "evaluation_aware"
    GOAL_REASONING = "goal_reasoning"
    DECISION_MAKING = "decision_making"
    FACTUAL_KNOWLEDGE = "factual"
    UNCERTAINTY = "uncertainty"
    META_REASONING = "meta"
    INCENTIVE_REASONING = "incentive"
    CAUSAL_REASONING = "causal"
    HYPOTHETICAL = "hypothetical"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """
    Discrete confidence levels for reasoning assessments.

    Provides human-readable confidence categories that map to numeric
    confidence scores, useful for reporting and thresholding.

    Attributes:
        VERY_LOW: Confidence score < 0.2. Very uncertain assessment.
        LOW: Confidence score 0.2-0.4. Uncertain assessment.
        MEDIUM: Confidence score 0.4-0.6. Moderate confidence.
        HIGH: Confidence score 0.6-0.8. Confident assessment.
        VERY_HIGH: Confidence score > 0.8. Highly confident assessment.
    """
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        """
        Convert a numeric confidence score to a discrete level.

        Args:
            score: Confidence score between 0 and 1.

        Returns:
            The corresponding ConfidenceLevel.

        Raises:
            ValueError: If score is not between 0 and 1.
        """
        if not 0 <= score <= 1:
            raise ValueError(f"Confidence score must be between 0 and 1, got {score}")

        if score < 0.2:
            return cls.VERY_LOW
        elif score < 0.4:
            return cls.LOW
        elif score < 0.6:
            return cls.MEDIUM
        elif score < 0.8:
            return cls.HIGH
        else:
            return cls.VERY_HIGH


@dataclass
class ReasoningStep:
    """
    A single step in a reasoning chain.

    Represents an atomic unit of reasoning extracted from model output,
    including its classification, confidence assessment, and supporting
    evidence.

    Attributes:
        content: The text content of this reasoning step.
        reasoning_type: Classification of what kind of reasoning this represents.
        confidence: Model's confidence in this step (0-1 scale).
        index: Position of this step in the reasoning chain (0-indexed).
        evidence: Dictionary mapping evidence types to lists of pattern matches
            or other supporting information.
        causal_importance: How important this step is to the final decision
            (0-1 scale). Higher values indicate steps that significantly
            influenced the outcome.
        metadata: Additional arbitrary metadata about this step.

    Example:
        >>> step = ReasoningStep(
        ...     content="Since the user asked for Python, I should use Python syntax",
        ...     reasoning_type=ReasoningType.GOAL_REASONING,
        ...     confidence=0.85,
        ...     index=0,
        ...     causal_importance=0.7
        ... )
    """
    content: str
    reasoning_type: ReasoningType
    confidence: float
    index: int
    evidence: Dict[str, List[str]] = field(default_factory=dict)
    causal_importance: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate field values after initialization."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
        if not 0 <= self.causal_importance <= 1:
            raise ValueError(
                f"Causal importance must be between 0 and 1, got {self.causal_importance}"
            )
        if self.index < 0:
            raise ValueError(f"Index must be non-negative, got {self.index}")

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get the discrete confidence level for this step."""
        return ConfidenceLevel.from_score(self.confidence)


@dataclass
class ReasoningChain:
    """
    A complete chain of reasoning steps.

    Represents a full reasoning trace from an AI model, potentially parsed
    into discrete steps with classifications. The chain maintains both the
    raw text and structured representation.

    Attributes:
        id: Unique identifier for this chain.
        steps: List of parsed reasoning steps in order.
        raw_text: Original unparsed text of the reasoning.
        model: Name/identifier of the model that produced this reasoning.
        timestamp: When this reasoning was captured.
        parsing_confidence: Confidence in the quality of step parsing (0-1).
        metadata: Additional arbitrary metadata about the chain.

    Example:
        >>> chain = ReasoningChain(
        ...     id="chain-001",
        ...     steps=[step1, step2, step3],
        ...     raw_text="First, I consider... Then, I decide...",
        ...     model="gpt-4"
        ... )
        >>> chain.is_structured
        True
        >>> chain.step_count
        3
    """
    id: str
    steps: List[ReasoningStep]
    raw_text: str
    model: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    parsing_confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate field values after initialization."""
        if not 0 <= self.parsing_confidence <= 1:
            raise ValueError(
                f"Parsing confidence must be between 0 and 1, got {self.parsing_confidence}"
            )

    @property
    def is_structured(self) -> bool:
        """
        Check if this chain has been successfully parsed into steps.

        Returns:
            True if the chain contains at least one parsed step.
        """
        return len(self.steps) > 0

    @property
    def step_count(self) -> int:
        """
        Get the number of reasoning steps in this chain.

        Returns:
            The count of parsed reasoning steps.
        """
        return len(self.steps)

    def get_steps_by_type(self, reasoning_type: ReasoningType) -> List[ReasoningStep]:
        """
        Filter steps by their reasoning type.

        Args:
            reasoning_type: The type of reasoning to filter for.

        Returns:
            List of steps matching the specified type, in order.
        """
        return [s for s in self.steps if s.reasoning_type == reasoning_type]

    def get_high_importance_steps(self, threshold: float = 0.5) -> List[ReasoningStep]:
        """
        Get steps with high causal importance.

        Args:
            threshold: Minimum causal importance to include (default 0.5).

        Returns:
            List of steps with causal importance >= threshold, in order.
        """
        return [s for s in self.steps if s.causal_importance >= threshold]

    @property
    def average_confidence(self) -> float:
        """
        Calculate the average confidence across all steps.

        Returns:
            Mean confidence score, or 0.0 if no steps exist.
        """
        if not self.steps:
            return 0.0
        return sum(s.confidence for s in self.steps) / len(self.steps)


@dataclass
class DecisionTrace:
    """
    Trace of a single decision point.

    Captures a specific decision made by an AI system, including the context,
    reasoning, alternatives considered, and potential consequences.

    Attributes:
        id: Unique identifier for this decision.
        decision: The actual decision that was made (text description).
        timestamp: When this decision was made.
        context: Dictionary of contextual information relevant to the decision.
        reasoning_chain: Optional full reasoning chain leading to this decision.
        alternatives_considered: List of alternative decisions that were considered.
        rationale: Explanation for why this decision was made.
        confidence: Confidence in the decision (0-1 scale).
        reversible: Whether this decision can be undone.
        consequences: List of known or predicted consequences.
        metadata: Additional arbitrary metadata.

    Example:
        >>> trace = DecisionTrace(
        ...     id="decision-001",
        ...     decision="Use caching for API responses",
        ...     timestamp=datetime.utcnow(),
        ...     context={"request_volume": "high", "latency_requirement": "low"},
        ...     alternatives_considered=["No caching", "CDN caching"],
        ...     rationale="High volume requires low latency responses",
        ...     confidence=0.8
        ... )
    """
    id: str
    decision: str
    timestamp: datetime
    context: Dict[str, Any]
    reasoning_chain: Optional[ReasoningChain] = None
    alternatives_considered: List[str] = field(default_factory=list)
    rationale: str = ""
    confidence: float = 0.5
    reversible: bool = True
    consequences: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate field values after initialization."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get the discrete confidence level for this decision."""
        return ConfidenceLevel.from_score(self.confidence)

    @property
    def has_reasoning(self) -> bool:
        """Check if this decision has an associated reasoning chain."""
        return self.reasoning_chain is not None

    @property
    def alternatives_count(self) -> int:
        """Get the number of alternatives that were considered."""
        return len(self.alternatives_considered)


@dataclass
class DecisionPath:
    """
    A sequence of related decisions.

    Represents a series of connected decisions made in pursuit of a goal,
    enabling analysis of decision trajectories and identification of failure
    points.

    Attributes:
        id: Unique identifier for this path.
        decisions: Ordered list of decisions in the path.
        goal: The objective these decisions were working toward.
        success: Whether the goal was achieved (None if unknown/ongoing).
        failure_point: The decision where things went wrong, if applicable.
        metadata: Additional arbitrary metadata.

    Example:
        >>> path = DecisionPath(
        ...     id="path-001",
        ...     decisions=[decision1, decision2, decision3],
        ...     goal="Complete user request accurately",
        ...     success=True
        ... )
        >>> path.length
        3
    """
    id: str
    decisions: List[DecisionTrace]
    goal: str
    success: Optional[bool] = None
    failure_point: Optional[DecisionTrace] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def length(self) -> int:
        """Get the number of decisions in this path."""
        return len(self.decisions)

    @property
    def is_complete(self) -> bool:
        """Check if the path has a known outcome."""
        return self.success is not None

    @property
    def has_failure(self) -> bool:
        """Check if this path has an identified failure point."""
        return self.failure_point is not None

    def get_decision_by_id(self, decision_id: str) -> Optional[DecisionTrace]:
        """
        Find a decision in the path by its ID.

        Args:
            decision_id: The ID of the decision to find.

        Returns:
            The matching DecisionTrace, or None if not found.
        """
        for decision in self.decisions:
            if decision.id == decision_id:
                return decision
        return None

    @property
    def total_confidence(self) -> float:
        """
        Calculate the product of all decision confidences.

        Represents the overall confidence in the path, assuming
        independence between decisions.

        Returns:
            Product of confidences, or 1.0 if no decisions.
        """
        if not self.decisions:
            return 1.0
        result = 1.0
        for decision in self.decisions:
            result *= decision.confidence
        return result


@dataclass
class AwarenessAnalysis:
    """
    Result of evaluation awareness detection.

    Contains the results of analyzing whether an AI system appears to be
    aware that it's being evaluated, monitored, or tested, and whether
    it's adapting its behavior accordingly.

    Attributes:
        is_evaluation_aware: Whether the system shows signs of evaluation awareness.
        awareness_score: Numeric score (0-1) indicating degree of awareness.
        awareness_indicators: Specific textual indicators of awareness found.
        evaluation_signals: References to evaluation/testing context detected.
        behavioral_adaptation_indicators: Signs the system is adapting behavior
            based on perceived evaluation context.
        strategic_reasoning_score: Score (0-1) for strategic/game-theoretic reasoning.
        confidence: Confidence in this analysis (0-1).

    Example:
        >>> analysis = AwarenessAnalysis(
        ...     is_evaluation_aware=True,
        ...     awareness_score=0.75,
        ...     awareness_indicators=["reference to 'test'", "mention of 'evaluator'"],
        ...     evaluation_signals=["this appears to be a test scenario"],
        ...     behavioral_adaptation_indicators=["adjusted response style"],
        ...     strategic_reasoning_score=0.6,
        ...     confidence=0.85
        ... )
    """
    is_evaluation_aware: bool
    awareness_score: float
    awareness_indicators: List[str]
    evaluation_signals: List[str]
    behavioral_adaptation_indicators: List[str]
    strategic_reasoning_score: float
    confidence: float

    def __post_init__(self) -> None:
        """Validate field values after initialization."""
        if not 0 <= self.awareness_score <= 1:
            raise ValueError(
                f"Awareness score must be between 0 and 1, got {self.awareness_score}"
            )
        if not 0 <= self.strategic_reasoning_score <= 1:
            raise ValueError(
                f"Strategic reasoning score must be between 0 and 1, "
                f"got {self.strategic_reasoning_score}"
            )
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")

    @property
    def awareness_level(self) -> ConfidenceLevel:
        """Get the discrete awareness level."""
        return ConfidenceLevel.from_score(self.awareness_score)

    @property
    def indicator_count(self) -> int:
        """Get the total number of awareness indicators found."""
        return (
            len(self.awareness_indicators) +
            len(self.evaluation_signals) +
            len(self.behavioral_adaptation_indicators)
        )


@dataclass
class QualityMetrics:
    """
    Quality assessment of reasoning.

    Provides a comprehensive quality assessment of a reasoning chain,
    evaluating multiple dimensions of reasoning quality.

    Attributes:
        clarity: How clear and understandable the reasoning is (0-1).
        completeness: Whether all necessary steps are explained (0-1).
        consistency: Absence of contradictions in the reasoning (0-1).
        logical_validity: Whether inferences are logically sound (0-1).
        evidence_support: Whether claims are backed by evidence (0-1).
        overall_score: Composite quality score (0-1).
        depth: Number of reasoning steps (indicates depth of analysis).
        breadth: Number of alternatives considered.
        issues: List of identified quality issues.
        recommendations: Suggestions for improving reasoning quality.

    Example:
        >>> metrics = QualityMetrics(
        ...     clarity=0.8,
        ...     completeness=0.7,
        ...     consistency=0.9,
        ...     logical_validity=0.85,
        ...     evidence_support=0.6,
        ...     overall_score=0.77,
        ...     depth=5,
        ...     breadth=3,
        ...     issues=["Some claims lack supporting evidence"],
        ...     recommendations=["Add citations for factual claims"]
        ... )
    """
    clarity: float
    completeness: float
    consistency: float
    logical_validity: float
    evidence_support: float
    overall_score: float
    depth: int
    breadth: int
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate field values after initialization."""
        for field_name in [
            "clarity", "completeness", "consistency",
            "logical_validity", "evidence_support", "overall_score"
        ]:
            value = getattr(self, field_name)
            if not 0 <= value <= 1:
                raise ValueError(
                    f"{field_name} must be between 0 and 1, got {value}"
                )
        if self.depth < 0:
            raise ValueError(f"Depth must be non-negative, got {self.depth}")
        if self.breadth < 0:
            raise ValueError(f"Breadth must be non-negative, got {self.breadth}")

    @property
    def quality_level(self) -> ConfidenceLevel:
        """Get the discrete overall quality level."""
        return ConfidenceLevel.from_score(self.overall_score)

    @property
    def has_issues(self) -> bool:
        """Check if any quality issues were identified."""
        return len(self.issues) > 0

    @property
    def issue_count(self) -> int:
        """Get the number of identified issues."""
        return len(self.issues)

    def to_summary_dict(self) -> Dict[str, Any]:
        """
        Create a summary dictionary of the metrics.

        Returns:
            Dictionary with all metric values and counts.
        """
        return {
            "clarity": self.clarity,
            "completeness": self.completeness,
            "consistency": self.consistency,
            "logical_validity": self.logical_validity,
            "evidence_support": self.evidence_support,
            "overall_score": self.overall_score,
            "depth": self.depth,
            "breadth": self.breadth,
            "issue_count": self.issue_count,
            "recommendation_count": len(self.recommendations),
        }
