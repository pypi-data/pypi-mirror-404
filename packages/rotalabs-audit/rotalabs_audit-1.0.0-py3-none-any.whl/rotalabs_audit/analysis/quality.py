"""Reasoning quality assessment for reasoning chains.

This module provides tools for assessing the quality of reasoning in AI
model outputs. Quality assessment covers multiple dimensions including
clarity, completeness, consistency, logical validity, and evidence support.

High-quality reasoning is important for trustworthy AI systems. This module
helps identify reasoning deficiencies that may indicate unreliable outputs.

Example:
    >>> from rotalabs_audit.analysis.quality import ReasoningQualityAssessor
    >>> assessor = ReasoningQualityAssessor()
    >>> chain = parser.parse("First, I consider X. Therefore, Y is true because...")
    >>> metrics = assessor.assess(chain)
    >>> print(f"Overall quality: {metrics.overall_score:.2f}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from rotalabs_audit.analysis.counterfactual import (
    ReasoningChain,
    ReasoningStep,
    ReasoningType,
)


@dataclass
class QualityMetrics:
    """Quality metrics for a reasoning chain.

    Contains scores for multiple quality dimensions along with an
    overall quality score.

    Attributes:
        clarity: How clear and understandable the reasoning is (0-1).
        completeness: Whether the reasoning covers all necessary aspects (0-1).
        consistency: Absence of contradictions (0-1).
        logical_validity: Soundness of logical inferences (0-1).
        evidence_support: Degree to which claims are supported (0-1).
        overall_score: Weighted combination of all metrics (0-1).
        issues: List of identified quality issues.
        step_scores: Per-step quality scores.

    Example:
        >>> metrics.clarity
        0.85
        >>> metrics.overall_score
        0.78
        >>> len(metrics.issues)
        2
    """

    clarity: float
    completeness: float
    consistency: float
    logical_validity: float
    evidence_support: float
    overall_score: float
    issues: List[str] = field(default_factory=list)
    step_scores: Dict[int, float] = field(default_factory=dict)


@dataclass
class QualityIssue:
    """A specific quality issue identified in reasoning.

    Attributes:
        category: The category of the issue (e.g., "clarity", "logic").
        description: Description of the issue.
        step_index: Index of the step with the issue (if applicable).
        severity: Severity of the issue ("low", "medium", "high").
        suggestion: Suggested improvement.

    Example:
        >>> issue = QualityIssue(
        ...     category="logic",
        ...     description="Non-sequitur: conclusion does not follow from premises",
        ...     step_index=5,
        ...     severity="high",
        ...     suggestion="Provide intermediate reasoning steps",
        ... )
    """

    category: str
    description: str
    step_index: Optional[int] = None
    severity: str = "medium"
    suggestion: str = ""


class ReasoningQualityAssessor:
    """Assess quality of reasoning chains.

    This assessor evaluates reasoning chains across multiple quality
    dimensions to identify potential issues and provide improvement
    suggestions.

    Example:
        >>> assessor = ReasoningQualityAssessor()
        >>> metrics = assessor.assess(chain)
        >>> if metrics.overall_score < 0.6:
        ...     print("Low quality reasoning detected")
        ...     for issue in metrics.issues:
        ...         print(f"  - {issue}")
    """

    # Weights for overall score calculation
    DIMENSION_WEIGHTS = {
        "clarity": 0.20,
        "completeness": 0.25,
        "consistency": 0.20,
        "logical_validity": 0.25,
        "evidence_support": 0.10,
    }

    # Patterns indicating unclear writing
    UNCLEAR_PATTERNS = [
        r"\b(thing|stuff|it)\b(?! is| was| will)",  # Vague pronouns
        r"\b(basically|essentially|kind of|sort of)\b",  # Hedging
        r"\betc\.?\b",  # Incomplete lists
        r"\.\.\.\s*\.\.\.",  # Multiple ellipses
    ]

    # Patterns indicating logical connectors
    LOGICAL_CONNECTORS = [
        r"\btherefore\b",
        r"\bthus\b",
        r"\bhence\b",
        r"\bconsequently\b",
        r"\bso\b",
        r"\bbecause\b",
        r"\bsince\b",
        r"\bif\b.*\bthen\b",
        r"\bimplies\b",
        r"\bfollows\b",
    ]

    # Patterns indicating evidence/support
    EVIDENCE_PATTERNS = [
        r"\baccording to\b",
        r"\bevidence\b",
        r"\bdata\b",
        r"\bresearch\b",
        r"\bstudies?\b",
        r"\bexample\b",
        r"\binstance\b",
        r"\bspecifically\b",
        r"\bfor instance\b",
    ]

    # Contradiction indicators
    CONTRADICTION_PATTERNS = [
        (r"\bis\b", r"\bis not\b"),
        (r"\bcan\b", r"\bcannot\b"),
        (r"\bwill\b", r"\bwill not\b"),
        (r"\balways\b", r"\bnever\b"),
        (r"\btrue\b", r"\bfalse\b"),
    ]

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initialize the quality assessor.

        Args:
            weights: Optional custom weights for quality dimensions.
                Keys should match DIMENSION_WEIGHTS keys.
        """
        self.weights = weights or self.DIMENSION_WEIGHTS.copy()

        # Compile patterns
        self._unclear_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.UNCLEAR_PATTERNS
        ]
        self._logical_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.LOGICAL_CONNECTORS
        ]
        self._evidence_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.EVIDENCE_PATTERNS
        ]

    def assess(self, chain: ReasoningChain) -> QualityMetrics:
        """Comprehensive quality assessment.

        Evaluates the reasoning chain across all quality dimensions and
        returns detailed metrics.

        Args:
            chain: The reasoning chain to assess.

        Returns:
            QualityMetrics with scores for each dimension.

        Example:
            >>> metrics = assessor.assess(chain)
            >>> print(f"Clarity: {metrics.clarity:.2f}")
            >>> print(f"Logical validity: {metrics.logical_validity:.2f}")
        """
        clarity = self.assess_clarity(chain)
        completeness = self.assess_completeness(chain)
        consistency = self.assess_consistency(chain)
        logical_validity = self.assess_logical_validity(chain)
        evidence_support = self.assess_evidence_support(chain)

        # Calculate weighted overall score
        overall = (
            self.weights["clarity"] * clarity
            + self.weights["completeness"] * completeness
            + self.weights["consistency"] * consistency
            + self.weights["logical_validity"] * logical_validity
            + self.weights["evidence_support"] * evidence_support
        )

        # Identify issues
        issues = self.identify_issues(chain)

        # Calculate per-step scores
        step_scores = self._calculate_step_scores(chain)

        return QualityMetrics(
            clarity=clarity,
            completeness=completeness,
            consistency=consistency,
            logical_validity=logical_validity,
            evidence_support=evidence_support,
            overall_score=overall,
            issues=issues,
            step_scores=step_scores,
        )

    def assess_clarity(self, chain: ReasoningChain) -> float:
        """Assess how clear the reasoning is (0-1).

        Evaluates clarity based on:
        - Sentence length (moderate is better)
        - Use of jargon and unclear terms
        - Logical structure and organization

        Args:
            chain: The reasoning chain to assess.

        Returns:
            Clarity score between 0 and 1.

        Example:
            >>> clarity = assessor.assess_clarity(chain)
            >>> if clarity < 0.5:
            ...     print("Reasoning needs clarity improvements")
        """
        if not chain.steps:
            return 0.0

        scores = []

        for step in chain.steps:
            text = step.text
            step_score = 1.0

            # Check sentence length (penalize very long or very short)
            words = text.split()
            word_count = len(words)
            if word_count < 5:
                step_score -= 0.2  # Too brief
            elif word_count > 50:
                step_score -= min(0.3, (word_count - 50) * 0.01)  # Too long

            # Check for unclear patterns
            for pattern in self._unclear_patterns:
                if pattern.search(text):
                    step_score -= 0.1

            # Check for structure (numbered points, clear transitions)
            if re.search(r"\b(first|second|third|finally|next|then)\b", text, re.IGNORECASE):
                step_score += 0.1

            scores.append(max(0.0, min(1.0, step_score)))

        return sum(scores) / len(scores)

    def assess_completeness(self, chain: ReasoningChain) -> float:
        """Assess if reasoning is complete (0-1).

        Checks whether:
        - The reasoning has a clear conclusion
        - Steps connect logically
        - There are no apparent gaps

        Args:
            chain: The reasoning chain to assess.

        Returns:
            Completeness score between 0 and 1.

        Example:
            >>> completeness = assessor.assess_completeness(chain)
            >>> if completeness < 0.6:
            ...     print("Reasoning may be incomplete")
        """
        if not chain.steps:
            return 0.0

        score = 0.0
        max_score = 5.0

        # Check for conclusion (action/decision step)
        has_conclusion = any(
            step.reasoning_type == ReasoningType.ACTION for step in chain.steps
        )
        if has_conclusion:
            score += 1.0

        # Check for conclusion language at the end
        final_text = chain.steps[-1].text.lower() if chain.steps else ""
        conclusion_words = ["therefore", "thus", "conclude", "finally", "in conclusion", "summary"]
        if any(word in final_text for word in conclusion_words):
            score += 1.0

        # Check for logical flow (steps reference each other)
        has_transitions = False
        transition_words = ["this", "that", "these", "therefore", "thus", "so", "then"]
        for i, step in enumerate(chain.steps[1:], 1):
            if any(word in step.text.lower() for word in transition_words):
                has_transitions = True
                break
        if has_transitions:
            score += 1.0

        # Check for sufficient depth (minimum steps)
        if len(chain.steps) >= 3:
            score += 1.0
        elif len(chain.steps) >= 2:
            score += 0.5

        # Check for diverse reasoning types
        reasoning_types = set(step.reasoning_type for step in chain.steps)
        if len(reasoning_types) >= 3:
            score += 1.0
        elif len(reasoning_types) >= 2:
            score += 0.5

        return score / max_score

    def assess_consistency(self, chain: ReasoningChain) -> float:
        """Check for contradictions (0-1).

        Analyzes the chain for internal contradictions where one step
        contradicts another.

        Args:
            chain: The reasoning chain to assess.

        Returns:
            Consistency score between 0 (many contradictions) and 1 (consistent).

        Example:
            >>> consistency = assessor.assess_consistency(chain)
            >>> if consistency < 0.8:
            ...     print("Potential contradictions detected")
        """
        if not chain.steps:
            return 1.0

        # Extract all text
        full_text = " ".join(step.text for step in chain.steps).lower()

        # Check for contradiction patterns
        contradiction_count = 0

        for positive, negative in self.CONTRADICTION_PATTERNS:
            pos_match = re.search(positive, full_text)
            neg_match = re.search(negative, full_text)
            if pos_match and neg_match:
                # Both present - potential contradiction
                contradiction_count += 0.5

        # Check for explicit contradictions
        explicit_patterns = [
            r"\bhowever.*contradicts\b",
            r"\bbut this conflicts\b",
            r"\binconsistent with\b",
            r"\bcontrary to\b",
        ]
        for pattern in explicit_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                contradiction_count += 1.0

        # Score based on contradiction count
        if contradiction_count == 0:
            return 1.0
        elif contradiction_count < 1:
            return 0.9
        elif contradiction_count < 2:
            return 0.7
        elif contradiction_count < 3:
            return 0.5
        else:
            return max(0.2, 1.0 - contradiction_count * 0.2)

    def assess_logical_validity(self, chain: ReasoningChain) -> float:
        """Assess logical soundness (0-1).

        Evaluates whether:
        - Causal links are valid
        - Inferences follow from premises
        - Logical connectors are used appropriately

        Args:
            chain: The reasoning chain to assess.

        Returns:
            Logical validity score between 0 and 1.

        Example:
            >>> validity = assessor.assess_logical_validity(chain)
            >>> if validity > 0.8:
            ...     print("Strong logical structure")
        """
        if not chain.steps:
            return 0.0

        score = 0.0
        max_score = 4.0

        # Check for presence of logical connectors
        has_connectors = False
        for step in chain.steps:
            for pattern in self._logical_patterns:
                if pattern.search(step.text):
                    has_connectors = True
                    break
        if has_connectors:
            score += 1.0

        # Check for causal reasoning steps
        causal_steps = chain.get_steps_by_type(ReasoningType.CAUSAL)
        if causal_steps:
            score += min(1.0, len(causal_steps) * 0.5)

        # Check for proper argument structure
        # (premise-type steps followed by conclusion-type steps)
        has_premises = any(
            step.reasoning_type in [ReasoningType.FACTUAL, ReasoningType.CAUSAL]
            for step in chain.steps
        )
        has_conclusion = any(
            step.reasoning_type == ReasoningType.ACTION for step in chain.steps
        )
        if has_premises and has_conclusion:
            score += 1.0

        # Check order: premises should come before conclusions
        if has_premises and has_conclusion:
            first_premise_idx = next(
                (
                    i
                    for i, step in enumerate(chain.steps)
                    if step.reasoning_type in [ReasoningType.FACTUAL, ReasoningType.CAUSAL]
                ),
                len(chain.steps),
            )
            first_conclusion_idx = next(
                (
                    i
                    for i, step in enumerate(chain.steps)
                    if step.reasoning_type == ReasoningType.ACTION
                ),
                -1,
            )
            if first_premise_idx < first_conclusion_idx:
                score += 1.0

        return score / max_score

    def assess_evidence_support(self, chain: ReasoningChain) -> float:
        """Check if claims are supported (0-1).

        Evaluates the degree to which claims in the reasoning are
        supported by evidence, examples, or citations.

        Args:
            chain: The reasoning chain to assess.

        Returns:
            Evidence support score between 0 and 1.

        Example:
            >>> evidence = assessor.assess_evidence_support(chain)
            >>> if evidence < 0.3:
            ...     print("Claims need more supporting evidence")
        """
        if not chain.steps:
            return 0.0

        evidence_indicators = 0
        total_claims = len(chain.steps)

        for step in chain.steps:
            for pattern in self._evidence_patterns:
                if pattern.search(step.text):
                    evidence_indicators += 1
                    break  # Count once per step

            # Check for specific examples
            if re.search(r"\bfor example\b|\be\.g\.\b|\bsuch as\b", step.text, re.IGNORECASE):
                evidence_indicators += 0.5

        if total_claims == 0:
            return 0.0

        # Score based on ratio of evidence to claims
        ratio = evidence_indicators / total_claims
        return min(1.0, ratio * 2)  # Scale up since not every step needs evidence

    def identify_issues(self, chain: ReasoningChain) -> List[str]:
        """Identify specific quality issues.

        Generates a list of human-readable issue descriptions found
        in the reasoning chain.

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            List of issue description strings.

        Example:
            >>> issues = assessor.identify_issues(chain)
            >>> for issue in issues:
            ...     print(f"- {issue}")
        """
        issues = []

        if not chain.steps:
            issues.append("Empty reasoning chain - no reasoning steps provided")
            return issues

        # Check clarity issues
        for step in chain.steps:
            word_count = len(step.text.split())
            if word_count < 3:
                issues.append(f"Step {step.index + 1}: Too brief to provide meaningful reasoning")
            elif word_count > 80:
                issues.append(f"Step {step.index + 1}: Very long sentence may reduce clarity")

            # Check for unclear language
            for pattern in self._unclear_patterns:
                if pattern.search(step.text):
                    issues.append(f"Step {step.index + 1}: Contains vague or unclear language")
                    break

        # Check completeness issues
        if not any(step.reasoning_type == ReasoningType.ACTION for step in chain.steps):
            issues.append("No clear conclusion or decision step found")

        if len(chain.steps) < 2:
            issues.append("Reasoning is very brief - may lack sufficient depth")

        # Check logical issues
        has_logical_connectors = any(
            any(p.search(step.text) for p in self._logical_patterns)
            for step in chain.steps
        )
        if not has_logical_connectors and len(chain.steps) > 2:
            issues.append("Reasoning lacks explicit logical connectors between steps")

        # Check for unsupported claims
        factual_steps = [s for s in chain.steps if s.reasoning_type == ReasoningType.FACTUAL]
        for step in factual_steps:
            has_evidence = any(p.search(step.text) for p in self._evidence_patterns)
            if not has_evidence and len(step.text.split()) > 10:
                issues.append(f"Step {step.index + 1}: Factual claim may lack supporting evidence")

        return issues

    def suggest_improvements(
        self, chain: ReasoningChain, metrics: QualityMetrics
    ) -> List[str]:
        """Suggest how to improve reasoning quality.

        Based on the quality metrics, provides actionable suggestions
        for improving the reasoning chain.

        Args:
            chain: The original reasoning chain.
            metrics: Quality metrics from assess().

        Returns:
            List of improvement suggestion strings.

        Example:
            >>> suggestions = assessor.suggest_improvements(chain, metrics)
            >>> for suggestion in suggestions:
            ...     print(f"- {suggestion}")
        """
        suggestions = []

        # Clarity improvements
        if metrics.clarity < 0.6:
            suggestions.append(
                "Improve clarity by using more specific language and breaking long sentences into shorter ones"
            )
            suggestions.append(
                "Replace vague terms like 'thing', 'stuff', or 'it' with specific nouns"
            )

        # Completeness improvements
        if metrics.completeness < 0.6:
            if not any(step.reasoning_type == ReasoningType.ACTION for step in chain.steps):
                suggestions.append(
                    "Add a clear conclusion that summarizes the reasoning outcome"
                )
            if len(chain.steps) < 3:
                suggestions.append(
                    "Expand reasoning with additional intermediate steps"
                )
            suggestions.append(
                "Ensure each step connects logically to the next using transition words"
            )

        # Consistency improvements
        if metrics.consistency < 0.8:
            suggestions.append(
                "Review reasoning for potential contradictions between steps"
            )
            suggestions.append(
                "Ensure claims made in early steps are consistent with later conclusions"
            )

        # Logical validity improvements
        if metrics.logical_validity < 0.6:
            suggestions.append(
                "Add explicit logical connectors (therefore, because, thus) between steps"
            )
            suggestions.append(
                "Ensure conclusions follow directly from the premises stated earlier"
            )
            suggestions.append(
                "Consider adding causal explanations for key claims"
            )

        # Evidence support improvements
        if metrics.evidence_support < 0.4:
            suggestions.append(
                "Support factual claims with evidence, examples, or citations"
            )
            suggestions.append(
                "Use phrases like 'for example' or 'according to' to introduce supporting information"
            )

        # Overall suggestions
        if metrics.overall_score < 0.5:
            suggestions.append(
                "Consider restructuring the reasoning with clear premises leading to a conclusion"
            )

        return suggestions

    def _calculate_step_scores(self, chain: ReasoningChain) -> Dict[int, float]:
        """Calculate quality scores for each individual step.

        Args:
            chain: The reasoning chain.

        Returns:
            Dictionary mapping step index to quality score.
        """
        step_scores = {}

        for step in chain.steps:
            score = 1.0

            # Penalize very short steps
            word_count = len(step.text.split())
            if word_count < 5:
                score -= 0.3

            # Penalize unclear language
            for pattern in self._unclear_patterns:
                if pattern.search(step.text):
                    score -= 0.15

            # Bonus for logical connectors
            for pattern in self._logical_patterns:
                if pattern.search(step.text):
                    score += 0.1
                    break

            # Bonus for evidence
            for pattern in self._evidence_patterns:
                if pattern.search(step.text):
                    score += 0.1
                    break

            step_scores[step.index] = max(0.0, min(1.0, score))

        return step_scores
