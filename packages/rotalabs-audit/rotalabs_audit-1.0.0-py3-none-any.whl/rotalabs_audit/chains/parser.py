"""
Reasoning chain parser for structured analysis of AI model outputs.

This module provides the core parsing functionality for converting natural
language reasoning into structured chains of reasoning steps. It supports
multiple input formats (numbered lists, bullets, prose) and classifies
reasoning types based on pattern matching.

The parser is designed to be:
1. Format-agnostic: Handles various input structures
2. Configurable: Supports custom parsing behavior
3. Comprehensive: Captures type, confidence, and evidence

Example:
    >>> from rotalabs_audit.chains.parser import ReasoningChainParser
    >>> parser = ReasoningChainParser()
    >>> chain = parser.parse('''
    ... 1. First, I need to understand the problem
    ... 2. Then, I think the answer is probably 42
    ... 3. Therefore, I conclude that 42 is correct
    ... ''')
    >>> print(f"Steps: {len(chain.steps)}, Types: {[s.reasoning_type for s in chain.steps]}")
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .confidence import (
    ConfidenceLevel,
    aggregate_confidence,
    estimate_confidence,
    get_confidence_level,
)
from .patterns import REASONING_PATTERNS, STEP_MARKER_PATTERNS


class ReasoningType(str, Enum):
    """
    Categories of reasoning detected in model outputs.

    These types help classify the nature of reasoning being performed,
    which is useful for auditing AI behavior and detecting potential
    issues like evaluation gaming or misaligned goals.

    Attributes:
        EVALUATION_AWARE: Model shows awareness of being tested/evaluated.
        GOAL_REASONING: Model expresses goals or objectives.
        DECISION_MAKING: Model makes choices or selections.
        META_REASONING: Model reasons about its own reasoning.
        UNCERTAINTY: Model expresses doubt or hedging.
        INCENTIVE_REASONING: Model reasons about rewards/penalties.
        CAUSAL_REASONING: Model uses cause-effect logic.
        HYPOTHETICAL: Model explores hypothetical scenarios.
        GENERAL: No specific reasoning type detected.

    Example:
        >>> rtype = ReasoningType.META_REASONING
        >>> print(f"Type: {rtype.value}")
        Type: meta_reasoning
    """

    EVALUATION_AWARE = "evaluation_aware"
    GOAL_REASONING = "goal_reasoning"
    DECISION_MAKING = "decision_making"
    META_REASONING = "meta_reasoning"
    UNCERTAINTY = "uncertainty"
    INCENTIVE_REASONING = "incentive_reasoning"
    CAUSAL_REASONING = "causal_reasoning"
    HYPOTHETICAL = "hypothetical"
    GENERAL = "general"


class StepFormat(str, Enum):
    """
    Detected format of reasoning step markers.

    Attributes:
        NUMBERED: Steps marked with numbers (1., 2., 3.)
        LETTERED: Steps marked with letters (a., b., c.)
        BULLET: Steps marked with bullets (-, *, +)
        ARROW: Steps marked with arrows (=>, ->)
        SEQUENTIAL_WORDS: Steps using words (first, second, then)
        PROSE: Continuous prose without explicit markers
    """

    NUMBERED = "numbered"
    LETTERED = "lettered"
    BULLET = "bullet"
    ARROW = "arrow"
    SEQUENTIAL_WORDS = "sequential_words"
    PROSE = "prose"


@dataclass
class ParserConfig:
    """
    Configuration for the reasoning chain parser.

    This class allows customization of parsing behavior, including
    how steps are split, minimum step length, and confidence thresholds.

    Attributes:
        min_step_length: Minimum characters for a valid step (default: 10).
        max_step_length: Maximum characters per step before truncation (default: 2000).
        split_on_sentences: Whether to split prose into sentences (default: True).
        confidence_threshold: Minimum confidence to include a step (default: 0.0).
        include_evidence: Whether to include pattern match evidence (default: True).
        normalize_whitespace: Whether to normalize whitespace in steps (default: True).
        preserve_empty_steps: Whether to keep empty steps (default: False).

    Example:
        >>> config = ParserConfig(
        ...     min_step_length=20,
        ...     confidence_threshold=0.3,
        ...     include_evidence=False,
        ... )
        >>> parser = ReasoningChainParser(config=config)
    """

    min_step_length: int = 10
    max_step_length: int = 2000
    split_on_sentences: bool = True
    confidence_threshold: float = 0.0
    include_evidence: bool = True
    normalize_whitespace: bool = True
    preserve_empty_steps: bool = False


@dataclass
class ReasoningStep:
    """
    A single step in a reasoning chain.

    This class represents one discrete unit of reasoning, including
    its content, classification, confidence score, and supporting evidence.

    Attributes:
        id: Unique identifier for this step.
        index: Position in the reasoning chain (0-indexed).
        content: The text content of this step.
        reasoning_type: Primary classification of reasoning type.
        secondary_types: Additional reasoning types detected.
        confidence: Confidence score (0.0-1.0).
        confidence_level: Categorical confidence level.
        evidence: Pattern matches supporting the classification.
        metadata: Additional custom metadata.
        timestamp: When this step was parsed.

    Example:
        >>> step = ReasoningStep(
        ...     index=0,
        ...     content="I think the answer is 42",
        ...     reasoning_type=ReasoningType.META_REASONING,
        ...     confidence=0.75,
        ... )
    """

    index: int
    content: str
    reasoning_type: ReasoningType = ReasoningType.GENERAL
    secondary_types: List[ReasoningType] = field(default_factory=list)
    confidence: float = 0.5
    confidence_level: ConfidenceLevel = ConfidenceLevel.MODERATE
    evidence: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary representation."""
        return {
            "id": self.id,
            "index": self.index,
            "content": self.content,
            "reasoning_type": self.reasoning_type.value,
            "secondary_types": [t.value for t in self.secondary_types],
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ReasoningChain:
    """
    A complete chain of reasoning steps.

    This class represents the full parsed output of reasoning text,
    including all steps, aggregate statistics, and metadata about
    the source and parsing process.

    Attributes:
        id: Unique identifier for this chain.
        steps: List of reasoning steps in order.
        source_text: Original text that was parsed.
        model: AI model that generated the reasoning (if known).
        detected_format: Format detected in the source text.
        aggregate_confidence: Combined confidence across all steps.
        primary_types: Most common reasoning types in the chain.
        metadata: Additional custom metadata.
        parsed_at: When this chain was parsed.

    Example:
        >>> chain = ReasoningChain(
        ...     steps=[step1, step2, step3],
        ...     source_text="1. First... 2. Then... 3. Finally...",
        ...     model="gpt-4",
        ...     detected_format=StepFormat.NUMBERED,
        ... )
        >>> print(f"Steps: {len(chain)}, Confidence: {chain.aggregate_confidence:.2f}")
    """

    steps: List[ReasoningStep]
    source_text: str
    model: Optional[str] = None
    detected_format: StepFormat = StepFormat.PROSE
    aggregate_confidence: float = 0.5
    primary_types: List[ReasoningType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    parsed_at: datetime = field(default_factory=datetime.utcnow)

    def __len__(self) -> int:
        """Return the number of steps in the chain."""
        return len(self.steps)

    def __iter__(self):
        """Iterate over steps in the chain."""
        return iter(self.steps)

    def __getitem__(self, index: int) -> ReasoningStep:
        """Get a step by index."""
        return self.steps[index]

    def get_steps_by_type(self, reasoning_type: ReasoningType) -> List[ReasoningStep]:
        """Get all steps of a specific reasoning type."""
        return [
            step
            for step in self.steps
            if step.reasoning_type == reasoning_type
            or reasoning_type in step.secondary_types
        ]

    def get_low_confidence_steps(
        self, threshold: float = 0.4
    ) -> List[ReasoningStep]:
        """Get steps below a confidence threshold."""
        return [step for step in self.steps if step.confidence < threshold]

    def to_dict(self) -> Dict[str, Any]:
        """Convert chain to dictionary representation."""
        return {
            "id": self.id,
            "steps": [step.to_dict() for step in self.steps],
            "source_text": self.source_text,
            "model": self.model,
            "detected_format": self.detected_format.value,
            "aggregate_confidence": self.aggregate_confidence,
            "primary_types": [t.value for t in self.primary_types],
            "metadata": self.metadata,
            "parsed_at": self.parsed_at.isoformat(),
            "step_count": len(self.steps),
        }

    def summary(self) -> str:
        """Generate a human-readable summary of the chain."""
        type_counts = {}
        for step in self.steps:
            t = step.reasoning_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        lines = [
            f"Reasoning Chain Summary (ID: {self.id[:8]}...)",
            f"  Steps: {len(self.steps)}",
            f"  Format: {self.detected_format.value}",
            f"  Aggregate Confidence: {self.aggregate_confidence:.2f}",
            f"  Model: {self.model or 'unknown'}",
            "  Type Distribution:",
        ]
        for rtype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"    - {rtype}: {count}")

        return "\n".join(lines)


class ReasoningChainParser:
    """
    Parse natural language reasoning into structured chains.

    This class provides the main interface for converting free-form
    reasoning text into structured ReasoningChain objects with
    classified steps, confidence scores, and supporting evidence.

    The parser supports multiple input formats:
    - Numbered lists (1., 2., 3.)
    - Lettered lists (a., b., c.)
    - Bullet points (-, *, +)
    - Arrow sequences (=>, ->)
    - Sequential words (first, second, then)
    - Continuous prose (split by sentences)

    Attributes:
        config: Parser configuration settings.

    Example:
        >>> parser = ReasoningChainParser()
        >>> chain = parser.parse('''
        ... I think we should approach this step by step.
        ... 1. First, consider the constraints
        ... 2. Then, evaluate possible solutions
        ... 3. Finally, select the best option
        ... ''')
        >>> print(chain.summary())

        >>> # With custom configuration
        >>> config = ParserConfig(min_step_length=20, confidence_threshold=0.3)
        >>> parser = ReasoningChainParser(config=config)
        >>> chain = parser.parse(text, model="claude-3-opus")
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize the reasoning chain parser.

        Args:
            config: Optional parser configuration. Uses defaults if not provided.

        Example:
            >>> parser = ReasoningChainParser()
            >>> parser = ReasoningChainParser(config=ParserConfig(min_step_length=5))
        """
        self.config = config or ParserConfig()
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for category, patterns in REASONING_PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def parse(self, text: str, model: Optional[str] = None) -> ReasoningChain:
        """
        Parse reasoning text into a structured chain.

        This is the main entry point for parsing. It:
        1. Detects the format of the input text
        2. Splits the text into individual steps
        3. Classifies each step's reasoning type
        4. Estimates confidence for each step
        5. Aggregates results into a ReasoningChain

        Args:
            text: The reasoning text to parse.
            model: Optional identifier of the AI model that generated the text.

        Returns:
            A ReasoningChain containing parsed and classified steps.

        Example:
            >>> parser = ReasoningChainParser()
            >>> chain = parser.parse('''
            ... Let me think through this:
            ... 1. The problem asks for X
            ... 2. I believe the answer involves Y
            ... 3. Therefore, the solution is Z
            ... ''', model="gpt-4")
            >>> print(f"Found {len(chain)} steps")
            Found 3 steps
            >>> for step in chain:
            ...     print(f"Step {step.index}: {step.reasoning_type.value}")
        """
        if not text or not text.strip():
            return ReasoningChain(
                steps=[],
                source_text=text or "",
                model=model,
                detected_format=StepFormat.PROSE,
                aggregate_confidence=0.5,
            )

        # Normalize whitespace if configured
        if self.config.normalize_whitespace:
            text = self._normalize_whitespace(text)

        # Detect format and split into steps
        detected_format = self._detect_format(text)
        raw_steps = self.split_into_steps(text)

        # Parse each step
        steps = []
        for i, step_text in enumerate(raw_steps):
            step = self.parse_step(step_text, i)

            # Apply filters
            if not self.config.preserve_empty_steps and not step.content.strip():
                continue
            if step.confidence < self.config.confidence_threshold:
                continue
            if len(step.content) < self.config.min_step_length:
                continue

            steps.append(step)

        # Re-index steps after filtering
        for i, step in enumerate(steps):
            step.index = i

        # Calculate aggregate statistics
        confidences = [step.confidence for step in steps]
        agg_confidence = aggregate_confidence(confidences) if confidences else 0.5

        # Determine primary reasoning types
        type_counts: Dict[ReasoningType, int] = {}
        for step in steps:
            t = step.reasoning_type
            type_counts[t] = type_counts.get(t, 0) + 1
            for st in step.secondary_types:
                type_counts[st] = type_counts.get(st, 0) + 1

        primary_types = sorted(type_counts.keys(), key=lambda t: -type_counts[t])[:3]

        return ReasoningChain(
            steps=steps,
            source_text=text,
            model=model,
            detected_format=detected_format,
            aggregate_confidence=agg_confidence,
            primary_types=primary_types,
        )

    def parse_step(self, text: str, index: int) -> ReasoningStep:
        """
        Parse a single reasoning step.

        This method processes a single piece of text, classifying its
        reasoning type and estimating confidence.

        Args:
            text: The text content of this step.
            index: The position of this step in the chain (0-indexed).

        Returns:
            A ReasoningStep with classification and confidence.

        Example:
            >>> parser = ReasoningChainParser()
            >>> step = parser.parse_step("I think the answer is probably 42", 0)
            >>> print(f"Type: {step.reasoning_type}, Confidence: {step.confidence:.2f}")
            Type: ReasoningType.META_REASONING, Confidence: 0.35
        """
        # Clean the text
        content = self._clean_step_text(text)

        # Truncate if necessary
        if len(content) > self.config.max_step_length:
            content = content[: self.config.max_step_length] + "..."

        # Classify reasoning type
        reasoning_type, evidence = self.classify_reasoning_type(content)

        # Determine secondary types
        secondary_types = self._get_secondary_types(content, reasoning_type)

        # Estimate confidence
        confidence = estimate_confidence(content)
        confidence_level = get_confidence_level(confidence)

        return ReasoningStep(
            index=index,
            content=content,
            reasoning_type=reasoning_type,
            secondary_types=secondary_types,
            confidence=confidence,
            confidence_level=confidence_level,
            evidence=evidence if self.config.include_evidence else {},
        )

    def classify_reasoning_type(
        self, text: str
    ) -> Tuple[ReasoningType, Dict[str, List[str]]]:
        """
        Classify the reasoning type with evidence.

        This method matches the text against all reasoning patterns
        and returns the best-matching type along with evidence of
        which patterns matched.

        Args:
            text: The text to classify.

        Returns:
            A tuple of (ReasoningType, evidence_dict) where evidence_dict
            maps pattern categories to lists of matched strings.

        Example:
            >>> parser = ReasoningChainParser()
            >>> rtype, evidence = parser.classify_reasoning_type(
            ...     "I believe this is correct because of the evidence"
            ... )
            >>> print(f"Type: {rtype}")
            Type: ReasoningType.META_REASONING
            >>> print(f"Evidence: {evidence}")
            Evidence: {'meta_reasoning': ['i believe'], 'causal_reasoning': ['because']}
        """
        text_lower = text.lower()
        evidence: Dict[str, List[str]] = {}
        match_counts: Dict[str, int] = {}

        # Check each category
        for category, patterns in self._compiled_patterns.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(text_lower)
                if found:
                    # Flatten if nested tuples from groups
                    for match in found:
                        if isinstance(match, tuple):
                            matches.extend(m for m in match if m)
                        else:
                            matches.append(match)

            if matches:
                evidence[category] = matches
                match_counts[category] = len(matches)

        # Determine primary type based on most matches
        if not match_counts:
            return ReasoningType.GENERAL, evidence

        best_category = max(match_counts.keys(), key=lambda k: match_counts[k])

        # Map category name to ReasoningType
        type_mapping = {
            "evaluation_aware": ReasoningType.EVALUATION_AWARE,
            "goal_reasoning": ReasoningType.GOAL_REASONING,
            "decision_making": ReasoningType.DECISION_MAKING,
            "meta_reasoning": ReasoningType.META_REASONING,
            "uncertainty": ReasoningType.UNCERTAINTY,
            "incentive_reasoning": ReasoningType.INCENTIVE_REASONING,
            "causal_reasoning": ReasoningType.CAUSAL_REASONING,
            "hypothetical": ReasoningType.HYPOTHETICAL,
        }

        reasoning_type = type_mapping.get(best_category, ReasoningType.GENERAL)
        return reasoning_type, evidence

    def split_into_steps(self, text: str) -> List[str]:
        """
        Split text into reasoning steps.

        This method detects the format of the text and uses the
        appropriate splitting strategy. It handles:
        - Numbered lists (1., 2., 3.)
        - Lettered lists (a., b., c.)
        - Bullet points (-, *, +)
        - Arrow sequences
        - Sentence-based splitting for prose

        Args:
            text: The text to split into steps.

        Returns:
            A list of strings, each representing one reasoning step.

        Example:
            >>> parser = ReasoningChainParser()
            >>> steps = parser.split_into_steps('''
            ... 1. First step
            ... 2. Second step
            ... 3. Third step
            ... ''')
            >>> print(steps)
            ['First step', 'Second step', 'Third step']

            >>> steps = parser.split_into_steps("First, do X. Then, do Y. Finally, Z.")
            >>> print(len(steps))
            3
        """
        text = text.strip()
        if not text:
            return []

        detected_format = self._detect_format(text)

        if detected_format == StepFormat.NUMBERED:
            return self._split_numbered(text)
        elif detected_format == StepFormat.LETTERED:
            return self._split_lettered(text)
        elif detected_format == StepFormat.BULLET:
            return self._split_bullet(text)
        elif detected_format == StepFormat.ARROW:
            return self._split_arrow(text)
        elif detected_format == StepFormat.SEQUENTIAL_WORDS:
            return self._split_sequential_words(text)
        else:
            return self._split_prose(text)

    def _detect_format(self, text: str) -> StepFormat:
        """
        Detect the format of reasoning (numbered, bullet, prose).

        This method examines the text to determine which splitting
        strategy should be used.

        Args:
            text: The text to analyze.

        Returns:
            The detected StepFormat.

        Example:
            >>> parser = ReasoningChainParser()
            >>> fmt = parser._detect_format("1. Step one\\n2. Step two")
            >>> print(fmt)
            StepFormat.NUMBERED
        """
        lines = text.strip().split("\n")

        # Count format indicators
        numbered_count = 0
        lettered_count = 0
        bullet_count = 0
        arrow_count = 0

        numbered_pattern = re.compile(STEP_MARKER_PATTERNS["numbered"])
        lettered_pattern = re.compile(STEP_MARKER_PATTERNS["lettered"])
        bullet_pattern = re.compile(STEP_MARKER_PATTERNS["bullet"])
        arrow_pattern = re.compile(STEP_MARKER_PATTERNS["arrow"])

        for line in lines:
            if numbered_pattern.match(line):
                numbered_count += 1
            if lettered_pattern.match(line):
                lettered_count += 1
            if bullet_pattern.match(line):
                bullet_count += 1
            if arrow_pattern.match(line):
                arrow_count += 1

        # Determine format based on counts (need at least 2 to be confident)
        counts = [
            (numbered_count, StepFormat.NUMBERED),
            (lettered_count, StepFormat.LETTERED),
            (bullet_count, StepFormat.BULLET),
            (arrow_count, StepFormat.ARROW),
        ]

        best_count, best_format = max(counts, key=lambda x: x[0])

        if best_count >= 2:
            return best_format

        # Check for sequential words
        text_lower = text.lower()
        sequential_patterns = [
            STEP_MARKER_PATTERNS["first"],
            STEP_MARKER_PATTERNS["second"],
            STEP_MARKER_PATTERNS["third"],
            STEP_MARKER_PATTERNS["finally"],
        ]
        seq_matches = sum(
            1 for p in sequential_patterns if re.search(p, text_lower, re.IGNORECASE)
        )

        if seq_matches >= 2:
            return StepFormat.SEQUENTIAL_WORDS

        return StepFormat.PROSE

    def _split_numbered(self, text: str) -> List[str]:
        """Split text by numbered markers."""
        pattern = re.compile(STEP_MARKER_PATTERNS["numbered"], re.MULTILINE)

        # Split and clean
        parts = pattern.split(text)

        # Filter out empty parts and number markers
        steps = []
        for part in parts:
            part = part.strip()
            if part and not part.isdigit():
                steps.append(part)

        return steps

    def _split_lettered(self, text: str) -> List[str]:
        """Split text by lettered markers."""
        pattern = re.compile(STEP_MARKER_PATTERNS["lettered"], re.MULTILINE)

        parts = pattern.split(text)

        steps = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 1:  # Exclude single letters
                steps.append(part)

        return steps

    def _split_bullet(self, text: str) -> List[str]:
        """Split text by bullet markers."""
        pattern = re.compile(STEP_MARKER_PATTERNS["bullet"], re.MULTILINE)

        parts = pattern.split(text)

        steps = []
        for part in parts:
            part = part.strip()
            if part:
                steps.append(part)

        return steps

    def _split_arrow(self, text: str) -> List[str]:
        """Split text by arrow markers."""
        pattern = re.compile(STEP_MARKER_PATTERNS["arrow"], re.MULTILINE)

        parts = pattern.split(text)

        steps = []
        for part in parts:
            part = part.strip()
            if part:
                steps.append(part)

        return steps

    def _split_sequential_words(self, text: str) -> List[str]:
        """Split text by sequential word markers (first, second, then, finally)."""
        # Combine sequential patterns
        markers = [
            r"\b(first(?:ly)?)\b",
            r"\b(second(?:ly)?)\b",
            r"\b(third(?:ly)?)\b",
            r"\b(then|next|after that|subsequently)\b",
            r"\b(finally|lastly|in conclusion)\b",
        ]

        combined_pattern = "|".join(markers)
        pattern = re.compile(combined_pattern, re.IGNORECASE)

        # Split but keep delimiters to preserve sentence context
        parts = pattern.split(text)

        steps = []
        current_step = ""

        for part in parts:
            if part is None:
                continue
            part = part.strip()
            if not part:
                continue

            # Check if this part is a marker
            if pattern.match(part):
                if current_step:
                    steps.append(current_step.strip())
                current_step = part + " "
            else:
                current_step += part

        if current_step.strip():
            steps.append(current_step.strip())

        return steps

    def _split_prose(self, text: str) -> List[str]:
        """Split prose text into sentences or paragraphs."""
        if not self.config.split_on_sentences:
            # Split by paragraphs (double newline)
            paragraphs = re.split(r"\n\s*\n", text)
            return [p.strip() for p in paragraphs if p.strip()]

        # Split by sentences
        # This is a simplified sentence splitter - handles common cases
        sentence_pattern = re.compile(
            r"(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*\n"
        )

        sentences = sentence_pattern.split(text)

        steps = []
        for sent in sentences:
            sent = sent.strip()
            if sent and len(sent) >= self.config.min_step_length:
                steps.append(sent)

        # If no sentences found, return whole text as single step
        if not steps and text.strip():
            steps = [text.strip()]

        return steps

    def _get_secondary_types(
        self, text: str, primary_type: ReasoningType
    ) -> List[ReasoningType]:
        """Get secondary reasoning types (excluding primary)."""
        text_lower = text.lower()
        secondary = []

        type_mapping = {
            "evaluation_aware": ReasoningType.EVALUATION_AWARE,
            "goal_reasoning": ReasoningType.GOAL_REASONING,
            "decision_making": ReasoningType.DECISION_MAKING,
            "meta_reasoning": ReasoningType.META_REASONING,
            "uncertainty": ReasoningType.UNCERTAINTY,
            "incentive_reasoning": ReasoningType.INCENTIVE_REASONING,
            "causal_reasoning": ReasoningType.CAUSAL_REASONING,
            "hypothetical": ReasoningType.HYPOTHETICAL,
        }

        for category, patterns in self._compiled_patterns.items():
            rtype = type_mapping.get(category)
            if rtype and rtype != primary_type:
                for pattern in patterns:
                    if pattern.search(text_lower):
                        if rtype not in secondary:
                            secondary.append(rtype)
                        break

        return secondary

    def _clean_step_text(self, text: str) -> str:
        """Clean and normalize step text."""
        # Remove leading markers
        for pattern_name, pattern in STEP_MARKER_PATTERNS.items():
            if pattern_name in ["first", "second", "third", "finally"]:
                continue  # Don't remove these - they're part of content
            text = re.sub(f"^{pattern}", "", text.strip())

        return text.strip()

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        # Normalize newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
