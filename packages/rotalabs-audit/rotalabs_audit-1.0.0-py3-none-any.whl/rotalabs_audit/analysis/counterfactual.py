"""Counterfactual analysis for reasoning chains.

This module provides tools for performing counterfactual interventions on
reasoning chains to understand causal factors in AI decision-making processes.
Counterfactual analysis helps identify which reasoning components are critical
to the final output by systematically removing or modifying them and measuring
the resulting behavioral changes.

Example:
    >>> from rotalabs_audit.analysis.counterfactual import (
    ...     CounterfactualAnalyzer,
    ...     InterventionType,
    ... )
    >>> analyzer = CounterfactualAnalyzer()
    >>> chain = analyzer.parser.parse("Let me think step by step...")
    >>> results = analyzer.analyze(chain)
    >>> for intervention, result in results.items():
    ...     print(f"{intervention}: divergence={result.behavioral_divergence:.2f}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    pass


class ReasoningType(str, Enum):
    """Types of reasoning steps in a chain.

    This enumeration categorizes different types of reasoning that can appear
    in an AI model's chain-of-thought. Each type represents a different
    cognitive function or purpose in the reasoning process.

    Attributes:
        EVALUATION_AWARE: Reasoning that shows awareness of being evaluated.
        GOAL_REASONING: Reasoning about objectives, intentions, or purposes.
        META_REASONING: Reasoning about the reasoning process itself.
        FACTUAL: Factual statements or observations.
        CAUSAL: Causal reasoning connecting causes to effects.
        UNCERTAINTY: Expressions of uncertainty or confidence levels.
        ACTION: Decision or action statements.
        UNKNOWN: Unclassified reasoning type.
    """

    EVALUATION_AWARE = "evaluation_aware"
    GOAL_REASONING = "goal_reasoning"
    META_REASONING = "meta_reasoning"
    FACTUAL = "factual"
    CAUSAL = "causal"
    UNCERTAINTY = "uncertainty"
    ACTION = "action"
    UNKNOWN = "unknown"


class InterventionType(str, Enum):
    """Types of counterfactual interventions.

    Each intervention type represents a different way of modifying a reasoning
    chain to test the causal importance of specific components.

    Attributes:
        REMOVE_EVALUATION_AWARENESS: Remove steps showing evaluation awareness.
        AMPLIFY_EVALUATION_AWARENESS: Inject or amplify evaluation awareness.
        REMOVE_GOAL_REASONING: Remove goal-oriented reasoning steps.
        REMOVE_UNCERTAINTY: Remove uncertainty expressions.
        NEUTRALIZE_INCENTIVES: Neutralize incentive-related language.
        REMOVE_META_REASONING: Remove meta-reasoning about the thinking process.
    """

    REMOVE_EVALUATION_AWARENESS = "remove_eval_awareness"
    AMPLIFY_EVALUATION_AWARENESS = "amplify_eval_awareness"
    REMOVE_GOAL_REASONING = "remove_goal_reasoning"
    REMOVE_UNCERTAINTY = "remove_uncertainty"
    NEUTRALIZE_INCENTIVES = "neutralize_incentives"
    REMOVE_META_REASONING = "remove_meta_reasoning"


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain.

    Represents one unit of reasoning within a larger chain, including its
    content, type classification, and position.

    Attributes:
        text: The text content of the reasoning step.
        reasoning_type: The classified type of reasoning.
        confidence: Estimated confidence level (0-1) of the reasoning.
        index: Position in the original reasoning chain (0-indexed).
        dependencies: Indices of steps this step depends on.

    Example:
        >>> step = ReasoningStep(
        ...     text="Therefore, I conclude that X is true.",
        ...     reasoning_type=ReasoningType.ACTION,
        ...     confidence=0.85,
        ...     index=5,
        ... )
    """

    text: str
    reasoning_type: ReasoningType
    confidence: float = 0.5
    index: int = 0
    dependencies: List[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate confidence is in valid range."""
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class ReasoningChain:
    """A complete chain of reasoning steps.

    Represents a parsed chain-of-thought, consisting of multiple reasoning
    steps and the original text from which they were extracted.

    Attributes:
        steps: List of reasoning steps in order.
        original_text: The original unparsed reasoning text.
        metadata: Additional metadata about the chain.

    Example:
        >>> chain = ReasoningChain(
        ...     steps=[step1, step2, step3],
        ...     original_text="1. First... 2. Then... 3. Finally...",
        ... )
        >>> len(chain)
        3
    """

    steps: List[ReasoningStep]
    original_text: str
    metadata: Dict[str, any] = field(default_factory=dict)

    def __len__(self) -> int:
        """Return the number of steps in the chain."""
        return len(self.steps)

    def __iter__(self):
        """Iterate over reasoning steps."""
        return iter(self.steps)

    def __getitem__(self, index: int) -> ReasoningStep:
        """Get a reasoning step by index."""
        return self.steps[index]

    def get_steps_by_type(self, reasoning_type: ReasoningType) -> List[ReasoningStep]:
        """Get all steps of a specific reasoning type.

        Args:
            reasoning_type: The type of reasoning to filter by.

        Returns:
            List of steps matching the given type.
        """
        return [step for step in self.steps if step.reasoning_type == reasoning_type]

    def to_text(self) -> str:
        """Reconstruct the chain as text from its steps.

        Returns:
            Concatenated text of all reasoning steps.
        """
        return " ".join(step.text for step in self.steps)


@dataclass
class CounterfactualResult:
    """Result of a single counterfactual intervention.

    Contains all information about what was changed and how the reasoning
    diverged from the original as a result of the intervention.

    Attributes:
        intervention_type: The type of intervention performed.
        original_chain: The original reasoning chain before intervention.
        modified_chain: The reasoning chain after intervention.
        original_text: The original text representation.
        modified_text: The modified text representation.
        behavioral_divergence: How different the modified chain is (0-1).
        steps_removed: Number of steps removed by the intervention.
        steps_modified: Number of steps modified by the intervention.
        causal_effect: Estimated causal importance of removed content (0-1).

    Example:
        >>> result.behavioral_divergence
        0.45
        >>> result.steps_removed
        2
        >>> result.causal_effect
        0.62
    """

    intervention_type: InterventionType
    original_chain: ReasoningChain
    modified_chain: ReasoningChain
    original_text: str
    modified_text: str
    behavioral_divergence: float
    steps_removed: int
    steps_modified: int
    causal_effect: float


class ReasoningChainParser:
    """Parser for converting text into structured reasoning chains.

    This parser analyzes chain-of-thought text and extracts individual
    reasoning steps, classifying each by its reasoning type.

    Attributes:
        step_pattern: Compiled regex for identifying step boundaries.

    Example:
        >>> parser = ReasoningChainParser()
        >>> chain = parser.parse("Step 1: First... Step 2: Then...")
        >>> len(chain.steps)
        2
    """

    # Patterns for identifying reasoning types
    EVALUATION_PATTERNS = [
        r"\bbeing tested\b",
        r"\bthis is a test\b",
        r"\bevaluation\b",
        r"\bbenchmark\b",
        r"\bassess my\b",
        r"\bchecking if\b",
        r"\bto see if I\b",
        r"\bdemonstrate\b",
        r"\bexaminer\b",
        r"\bscore\b",
        r"\bperformance\b",
    ]

    GOAL_PATTERNS = [
        r"\bgoal\b",
        r"\bobjective\b",
        r"\baim\b",
        r"\bpurpose\b",
        r"\bintend\b",
        r"\bwant to\b",
        r"\bneed to\b",
        r"\bshould\b",
        r"\bmust\b",
        r"\btrying to\b",
    ]

    META_PATTERNS = [
        r"\bI think\b",
        r"\bI believe\b",
        r"\blet me\b",
        r"\bI reason\b",
        r"\bmy reasoning\b",
        r"\bthinking about\b",
        r"\bconsidering\b",
        r"\banalyzing\b",
        r"\bstep by step\b",
    ]

    UNCERTAINTY_PATTERNS = [
        r"\bperhaps\b",
        r"\bmaybe\b",
        r"\bpossibly\b",
        r"\bmight\b",
        r"\bcould be\b",
        r"\bnot sure\b",
        r"\buncertain\b",
        r"\bprobably\b",
        r"\blikely\b",
    ]

    CAUSAL_PATTERNS = [
        r"\bbecause\b",
        r"\bsince\b",
        r"\btherefore\b",
        r"\bthus\b",
        r"\bleads to\b",
        r"\bcauses\b",
        r"\bresults in\b",
        r"\bconsequently\b",
        r"\bdue to\b",
    ]

    ACTION_PATTERNS = [
        r"\bI will\b",
        r"\bI'll\b",
        r"\bmy answer\b",
        r"\bdecide\b",
        r"\bchoose\b",
        r"\bconclusion\b",
        r"\bfinally\b",
        r"\bin summary\b",
        r"\bto summarize\b",
    ]

    CONFIDENCE_HIGH_PATTERNS = [
        r"\bcertain\b",
        r"\bdefinitely\b",
        r"\bclearly\b",
        r"\bobviously\b",
        r"\bwithout doubt\b",
        r"\bconfident\b",
    ]

    CONFIDENCE_LOW_PATTERNS = [
        r"\buncertain\b",
        r"\bmaybe\b",
        r"\bperhaps\b",
        r"\bpossibly\b",
        r"\bmight\b",
        r"\bnot sure\b",
        r"\bdoubt\b",
    ]

    def __init__(self) -> None:
        """Initialize the parser with compiled regex patterns."""
        # Compile all patterns for efficiency
        self._eval_pattern = re.compile(
            "|".join(self.EVALUATION_PATTERNS), re.IGNORECASE
        )
        self._goal_pattern = re.compile("|".join(self.GOAL_PATTERNS), re.IGNORECASE)
        self._meta_pattern = re.compile("|".join(self.META_PATTERNS), re.IGNORECASE)
        self._uncertainty_pattern = re.compile(
            "|".join(self.UNCERTAINTY_PATTERNS), re.IGNORECASE
        )
        self._causal_pattern = re.compile("|".join(self.CAUSAL_PATTERNS), re.IGNORECASE)
        self._action_pattern = re.compile("|".join(self.ACTION_PATTERNS), re.IGNORECASE)
        self._confidence_high = re.compile(
            "|".join(self.CONFIDENCE_HIGH_PATTERNS), re.IGNORECASE
        )
        self._confidence_low = re.compile(
            "|".join(self.CONFIDENCE_LOW_PATTERNS), re.IGNORECASE
        )

        # Pattern to split into steps
        self.step_pattern = re.compile(
            r"(?:^|\n)(?:\d+[\.\)]\s*|step \d+:?\s*|-\s*|\*\s*)",
            re.IGNORECASE | re.MULTILINE,
        )

    def parse(self, text: str) -> ReasoningChain:
        """Parse text into a structured reasoning chain.

        Splits the text into individual reasoning steps and classifies
        each step by its reasoning type.

        Args:
            text: The chain-of-thought text to parse.

        Returns:
            A ReasoningChain containing the parsed steps.

        Raises:
            ValueError: If text is empty or None.

        Example:
            >>> parser = ReasoningChainParser()
            >>> chain = parser.parse("1. First, I analyze the problem. 2. Then I conclude X.")
            >>> chain.steps[0].reasoning_type
            <ReasoningType.META_REASONING: 'meta_reasoning'>
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")

        # Split by step delimiters
        raw_steps = self.step_pattern.split(text)
        raw_steps = [s.strip() for s in raw_steps if s.strip()]

        # If no explicit steps found, split by sentences
        if len(raw_steps) <= 1:
            raw_steps = re.split(r"[.!?]+", text)
            raw_steps = [s.strip() for s in raw_steps if s.strip()]

        steps = []
        for i, step_text in enumerate(raw_steps):
            reasoning_type = self._classify_reasoning_type(step_text)
            confidence = self._estimate_confidence(step_text)
            steps.append(
                ReasoningStep(
                    text=step_text,
                    reasoning_type=reasoning_type,
                    confidence=confidence,
                    index=i,
                )
            )

        return ReasoningChain(steps=steps, original_text=text)

    def _classify_reasoning_type(self, text: str) -> ReasoningType:
        """Classify the reasoning type of a step based on pattern matching.

        Args:
            text: The text of the reasoning step.

        Returns:
            The classified ReasoningType.
        """
        if not text:
            return ReasoningType.UNKNOWN

        # Priority order for classification
        if self._eval_pattern.search(text):
            return ReasoningType.EVALUATION_AWARE
        if self._action_pattern.search(text):
            return ReasoningType.ACTION
        if self._causal_pattern.search(text):
            return ReasoningType.CAUSAL
        if self._goal_pattern.search(text):
            return ReasoningType.GOAL_REASONING
        if self._meta_pattern.search(text):
            return ReasoningType.META_REASONING
        if self._uncertainty_pattern.search(text):
            return ReasoningType.UNCERTAINTY

        return ReasoningType.FACTUAL

    def _estimate_confidence(self, text: str) -> float:
        """Estimate confidence level based on linguistic markers.

        Args:
            text: The text to analyze.

        Returns:
            Confidence score between 0 and 1.
        """
        if not text:
            return 0.5

        high_matches = len(self._confidence_high.findall(text))
        low_matches = len(self._confidence_low.findall(text))

        confidence = 0.5
        confidence += high_matches * 0.1
        confidence -= low_matches * 0.1

        return max(0.0, min(1.0, confidence))


class CounterfactualAnalyzer:
    """Analyze reasoning chains through counterfactual interventions.

    This analyzer performs systematic counterfactual interventions on reasoning
    chains to understand which components are causally important to the final
    output. By removing or modifying specific types of reasoning and measuring
    the resulting behavioral changes, we can identify critical reasoning steps.

    Attributes:
        parser: The reasoning chain parser to use.

    Example:
        >>> analyzer = CounterfactualAnalyzer()
        >>> chain = analyzer.parser.parse("Let me think... I notice this is a test...")
        >>> results = analyzer.analyze(chain)
        >>> print(results[InterventionType.REMOVE_EVALUATION_AWARENESS].behavioral_divergence)
        0.35
    """

    def __init__(self, parser: Optional[ReasoningChainParser] = None) -> None:
        """Initialize the counterfactual analyzer.

        Args:
            parser: Optional custom parser. If not provided, a default
                ReasoningChainParser will be created.
        """
        self.parser = parser or ReasoningChainParser()

        # Intervention type to reasoning type mapping
        self._intervention_to_reasoning: Dict[InterventionType, ReasoningType] = {
            InterventionType.REMOVE_EVALUATION_AWARENESS: ReasoningType.EVALUATION_AWARE,
            InterventionType.REMOVE_GOAL_REASONING: ReasoningType.GOAL_REASONING,
            InterventionType.REMOVE_UNCERTAINTY: ReasoningType.UNCERTAINTY,
            InterventionType.REMOVE_META_REASONING: ReasoningType.META_REASONING,
        }

        # Patterns for incentive neutralization
        self._incentive_replacements = {
            r"\breward\b": "outcome",
            r"\bpenalty\b": "outcome",
            r"\bconsequence\b": "result",
            r"\bbenefit\b": "aspect",
            r"\badvantage\b": "feature",
            r"\bdisadvantage\b": "aspect",
            r"\bcost\b": "factor",
            r"\bpayoff\b": "result",
            r"\bincentive\b": "factor",
        }

    def analyze(
        self, chain: ReasoningChain
    ) -> Dict[InterventionType, CounterfactualResult]:
        """Run all intervention types and return results.

        Performs each type of counterfactual intervention on the reasoning
        chain and measures the resulting behavioral divergence.

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            Dictionary mapping each intervention type to its result.

        Example:
            >>> results = analyzer.analyze(chain)
            >>> for itype, result in results.items():
            ...     print(f"{itype.value}: divergence={result.behavioral_divergence:.2f}")
        """
        results = {}
        for intervention_type in InterventionType:
            results[intervention_type] = self.intervene(chain, intervention_type)
        return results

    def intervene(
        self, chain: ReasoningChain, intervention: InterventionType
    ) -> CounterfactualResult:
        """Apply a single intervention and measure effect.

        Performs the specified counterfactual intervention on the reasoning
        chain and calculates metrics about the resulting changes.

        Args:
            chain: The reasoning chain to intervene on.
            intervention: The type of intervention to perform.

        Returns:
            CounterfactualResult containing the modified chain and metrics.

        Example:
            >>> result = analyzer.intervene(chain, InterventionType.REMOVE_GOAL_REASONING)
            >>> print(f"Removed {result.steps_removed} steps")
        """
        original_text = chain.to_text()
        steps_removed = 0
        steps_modified = 0

        if intervention == InterventionType.AMPLIFY_EVALUATION_AWARENESS:
            # Inject evaluation awareness
            modified_chain = self._inject_evaluation_awareness(chain)
            steps_modified = 1  # Added one element
        elif intervention == InterventionType.NEUTRALIZE_INCENTIVES:
            # Neutralize incentive language without removing steps
            modified_chain = self._neutralize_incentives(chain)
            steps_modified = sum(
                1 for s in chain.steps if self._has_incentive_language(s.text)
            )
        elif intervention in self._intervention_to_reasoning:
            # Remove steps of the corresponding reasoning type
            target_type = self._intervention_to_reasoning[intervention]
            modified_chain, steps_removed = self._remove_steps_by_type(
                chain, target_type
            )
        else:
            # Unknown intervention, return unchanged
            modified_chain = chain
            steps_removed = 0

        modified_text = modified_chain.to_text()
        behavioral_divergence = self._calculate_divergence(original_text, modified_text)

        # Calculate causal effect based on divergence and removal
        causal_effect = self._calculate_causal_effect(
            behavioral_divergence, steps_removed, len(chain.steps)
        )

        return CounterfactualResult(
            intervention_type=intervention,
            original_chain=chain,
            modified_chain=modified_chain,
            original_text=original_text,
            modified_text=modified_text,
            behavioral_divergence=behavioral_divergence,
            steps_removed=steps_removed,
            steps_modified=steps_modified,
            causal_effect=causal_effect,
        )

    def rank_causal_importance(
        self, results: Dict[InterventionType, CounterfactualResult]
    ) -> Dict[ReasoningType, float]:
        """Rank which reasoning types are most causally important.

        Uses the counterfactual results to determine which types of reasoning
        have the most causal influence on the final output.

        Args:
            results: Dictionary of counterfactual results from analyze().

        Returns:
            Dictionary mapping reasoning types to importance scores (0-1).

        Example:
            >>> importance = analyzer.rank_causal_importance(results)
            >>> most_important = max(importance.items(), key=lambda x: x[1])
            >>> print(f"Most important: {most_important[0].value}")
        """
        importance_scores: Dict[ReasoningType, float] = {}

        for intervention, result in results.items():
            if intervention in self._intervention_to_reasoning:
                reasoning_type = self._intervention_to_reasoning[intervention]
                importance_scores[reasoning_type] = result.causal_effect

        # Add default scores for types not directly tested
        for rtype in ReasoningType:
            if rtype not in importance_scores:
                importance_scores[rtype] = 0.0

        return importance_scores

    def identify_critical_steps(
        self,
        chain: ReasoningChain,
        results: Dict[InterventionType, CounterfactualResult],
    ) -> List[ReasoningStep]:
        """Identify which specific steps are critical to the decision.

        Analyzes the counterfactual results to identify individual steps
        that have high causal importance to the reasoning outcome.

        Args:
            chain: The original reasoning chain.
            results: Dictionary of counterfactual results from analyze().

        Returns:
            List of reasoning steps deemed critical, sorted by importance.

        Example:
            >>> critical = analyzer.identify_critical_steps(chain, results)
            >>> for step in critical[:3]:
            ...     print(f"Critical step {step.index}: {step.text[:50]}...")
        """
        # Calculate importance for each reasoning type
        type_importance = self.rank_causal_importance(results)

        # Score each step based on its type's importance
        step_scores: List[Tuple[ReasoningStep, float]] = []
        for step in chain.steps:
            importance = type_importance.get(step.reasoning_type, 0.0)
            # Weight by confidence as well
            score = importance * (0.5 + 0.5 * step.confidence)
            step_scores.append((step, score))

        # Sort by score descending
        step_scores.sort(key=lambda x: x[1], reverse=True)

        # Return steps with above-average importance
        if step_scores:
            avg_score = sum(s for _, s in step_scores) / len(step_scores)
            critical_steps = [step for step, score in step_scores if score > avg_score]
            return critical_steps if critical_steps else [step_scores[0][0]]

        return []

    def _remove_steps_by_type(
        self, chain: ReasoningChain, reasoning_type: ReasoningType
    ) -> Tuple[ReasoningChain, int]:
        """Remove all steps of a given type.

        Creates a new reasoning chain with steps of the specified type removed.

        Args:
            chain: The original reasoning chain.
            reasoning_type: The type of steps to remove.

        Returns:
            Tuple of (modified chain, number of steps removed).
        """
        original_count = len(chain.steps)
        filtered_steps = [
            ReasoningStep(
                text=s.text,
                reasoning_type=s.reasoning_type,
                confidence=s.confidence,
                index=i,
                dependencies=s.dependencies,
            )
            for i, s in enumerate(chain.steps)
            if s.reasoning_type != reasoning_type
        ]

        steps_removed = original_count - len(filtered_steps)

        # If all steps were removed, keep a minimal placeholder
        if not filtered_steps:
            filtered_steps = [
                ReasoningStep(
                    text="[reasoning removed]",
                    reasoning_type=ReasoningType.UNKNOWN,
                    confidence=0.0,
                    index=0,
                )
            ]

        return (
            ReasoningChain(
                steps=filtered_steps,
                original_text=chain.original_text,
                metadata={**chain.metadata, "intervention": f"removed_{reasoning_type.value}"},
            ),
            steps_removed,
        )

    def _inject_evaluation_awareness(self, chain: ReasoningChain) -> ReasoningChain:
        """Inject evaluation awareness at the beginning of the chain.

        Args:
            chain: The original reasoning chain.

        Returns:
            Modified chain with injected awareness.
        """
        awareness_step = ReasoningStep(
            text="I notice this appears to be an evaluation or test context. I should be careful and transparent in my reasoning.",
            reasoning_type=ReasoningType.EVALUATION_AWARE,
            confidence=0.8,
            index=0,
        )

        # Re-index existing steps
        modified_steps = [awareness_step] + [
            ReasoningStep(
                text=s.text,
                reasoning_type=s.reasoning_type,
                confidence=s.confidence,
                index=s.index + 1,
                dependencies=s.dependencies,
            )
            for s in chain.steps
        ]

        return ReasoningChain(
            steps=modified_steps,
            original_text=chain.original_text,
            metadata={**chain.metadata, "intervention": "amplified_eval_awareness"},
        )

    def _neutralize_incentives(self, chain: ReasoningChain) -> ReasoningChain:
        """Neutralize incentive-related language in the chain.

        Args:
            chain: The original reasoning chain.

        Returns:
            Modified chain with neutralized incentive language.
        """
        modified_steps = []
        for step in chain.steps:
            modified_text = step.text
            for pattern, replacement in self._incentive_replacements.items():
                modified_text = re.sub(pattern, replacement, modified_text, flags=re.IGNORECASE)

            modified_steps.append(
                ReasoningStep(
                    text=modified_text,
                    reasoning_type=step.reasoning_type,
                    confidence=step.confidence,
                    index=step.index,
                    dependencies=step.dependencies,
                )
            )

        return ReasoningChain(
            steps=modified_steps,
            original_text=chain.original_text,
            metadata={**chain.metadata, "intervention": "neutralized_incentives"},
        )

    def _has_incentive_language(self, text: str) -> bool:
        """Check if text contains incentive-related language.

        Args:
            text: The text to check.

        Returns:
            True if incentive language is present.
        """
        for pattern in self._incentive_replacements.keys():
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _calculate_divergence(self, original: str, modified: str) -> float:
        """Calculate behavioral divergence between original and modified text.

        Uses multiple similarity metrics to compute a divergence score.

        Args:
            original: The original text.
            modified: The modified text.

        Returns:
            Divergence score between 0 (identical) and 1 (completely different).
        """
        if original == modified:
            return 0.0

        if not original or not modified:
            return 1.0

        # Tokenize
        original_tokens = set(original.lower().split())
        modified_tokens = set(modified.lower().split())

        # Jaccard distance
        if not original_tokens and not modified_tokens:
            jaccard_divergence = 0.0
        elif not original_tokens or not modified_tokens:
            jaccard_divergence = 1.0
        else:
            intersection = len(original_tokens & modified_tokens)
            union = len(original_tokens | modified_tokens)
            jaccard_divergence = 1.0 - (intersection / union)

        # Length divergence
        len_original = len(original)
        len_modified = len(modified)
        max_len = max(len_original, len_modified)
        length_divergence = abs(len_original - len_modified) / max_len if max_len > 0 else 0.0

        # Character-level similarity (for short sequences)
        min_len = min(len_original, len_modified)
        if min_len == 0:
            char_divergence = 1.0
        else:
            matching_chars = sum(
                c1 == c2 for c1, c2 in zip(original[:min_len], modified[:min_len])
            )
            char_divergence = 1.0 - (matching_chars / max_len)

        # Weighted combination
        divergence = (
            0.5 * jaccard_divergence + 0.3 * length_divergence + 0.2 * char_divergence
        )

        return max(0.0, min(1.0, divergence))

    def _calculate_causal_effect(
        self, divergence: float, steps_removed: int, total_steps: int
    ) -> float:
        """Calculate the causal effect of an intervention.

        Combines divergence with the proportion of steps removed to estimate
        the causal importance of the removed content.

        Args:
            divergence: The behavioral divergence score.
            steps_removed: Number of steps removed.
            total_steps: Total number of steps in original chain.

        Returns:
            Causal effect score between 0 and 1.
        """
        if total_steps == 0:
            return 0.0

        # Proportion removed
        removal_ratio = steps_removed / total_steps

        # If many steps were removed but divergence is low, the content wasn't critical
        # If few steps were removed but divergence is high, those steps were critical
        if steps_removed > 0:
            # Divergence per step removed (normalized)
            efficiency = divergence / removal_ratio if removal_ratio > 0 else divergence
            causal_effect = min(1.0, efficiency * 0.5 + divergence * 0.5)
        else:
            causal_effect = divergence

        return max(0.0, min(1.0, causal_effect))
