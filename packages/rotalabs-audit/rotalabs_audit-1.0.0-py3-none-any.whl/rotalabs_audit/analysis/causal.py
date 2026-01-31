"""Causal importance analysis for reasoning chains.

This module provides tools for analyzing the causal structure of reasoning
chains, identifying which steps are most important to the final conclusion,
and building dependency graphs between reasoning steps.

Understanding causal importance helps identify critical reasoning components
that, if changed, would lead to different conclusions. This is valuable for
debugging reasoning failures and understanding model decision-making.

Example:
    >>> from rotalabs_audit.analysis.causal import CausalAnalyzer
    >>> analyzer = CausalAnalyzer()
    >>> importance = analyzer.analyze_step_importance(chain)
    >>> for idx, score in sorted(importance.items(), key=lambda x: -x[1]):
    ...     print(f"Step {idx}: importance={score:.2f}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from rotalabs_audit.analysis.counterfactual import (
    ReasoningChain,
    ReasoningStep,
    ReasoningType,
)


@dataclass
class CausalRelation:
    """A causal relationship between two reasoning steps.

    Represents a directed causal link where one step (cause) influences
    another step (effect).

    Attributes:
        cause_index: Index of the causing step.
        effect_index: Index of the affected step.
        strength: Strength of the causal relationship (0-1).
        relation_type: Type of causal relation (e.g., "logical", "temporal").

    Example:
        >>> relation = CausalRelation(
        ...     cause_index=2,
        ...     effect_index=5,
        ...     strength=0.8,
        ...     relation_type="logical",
        ... )
    """

    cause_index: int
    effect_index: int
    strength: float
    relation_type: str = "logical"


@dataclass
class CausalAnalysisResult:
    """Complete causal analysis of a reasoning chain.

    Contains all causal relationships, importance scores, and the
    dependency graph for a reasoning chain.

    Attributes:
        chain: The analyzed reasoning chain.
        step_importance: Importance score for each step (index -> score).
        causal_drivers: Steps that are primary drivers of the conclusion.
        dependency_graph: Graph of step dependencies (step -> dependencies).
        conclusion_step: The identified conclusion step, if any.
        causal_relations: All identified causal relations.

    Example:
        >>> result.step_importance[3]
        0.85
        >>> len(result.causal_drivers)
        2
        >>> result.conclusion_step.text
        "Therefore, I conclude..."
    """

    chain: ReasoningChain
    step_importance: Dict[int, float]
    causal_drivers: List[ReasoningStep]
    dependency_graph: Dict[int, List[int]]
    conclusion_step: Optional[ReasoningStep]
    causal_relations: List[CausalRelation]


class CausalAnalyzer:
    """Analyze causal importance of reasoning components.

    This analyzer examines reasoning chains to determine:
    - Which steps are most important to the final conclusion
    - How steps depend on each other
    - Which steps are the primary causal drivers

    Example:
        >>> analyzer = CausalAnalyzer()
        >>> importance = analyzer.analyze_step_importance(chain)
        >>> drivers = analyzer.find_causal_drivers(chain)
        >>> graph = analyzer.build_dependency_graph(chain)
    """

    # Patterns indicating causal language
    CAUSAL_INDICATORS = [
        r"\btherefore\b",
        r"\bthus\b",
        r"\bhence\b",
        r"\bconsequently\b",
        r"\bso\b",
        r"\bbecause\b",
        r"\bsince\b",
        r"\bdue to\b",
        r"\bas a result\b",
        r"\bleads to\b",
        r"\bcauses\b",
        r"\bimplies\b",
        r"\bfollows that\b",
    ]

    # Patterns indicating reference to previous steps
    REFERENCE_PATTERNS = [
        r"\bthis\b",
        r"\bthat\b",
        r"\bthese\b",
        r"\bthose\b",
        r"\babove\b",
        r"\bprevious\b",
        r"\bearlier\b",
        r"\bmentioned\b",
        r"\bas stated\b",
        r"\bas noted\b",
    ]

    # Patterns indicating conclusion/decision
    CONCLUSION_PATTERNS = [
        r"\btherefore\b",
        r"\bthus\b",
        r"\bin conclusion\b",
        r"\bfinally\b",
        r"\bto conclude\b",
        r"\bi conclude\b",
        r"\bmy answer\b",
        r"\bthe answer\b",
        r"\bdecision\b",
        r"\bi decide\b",
        r"\bin summary\b",
    ]

    def __init__(self) -> None:
        """Initialize the causal analyzer."""
        # Compile patterns
        self._causal_pattern = re.compile(
            "|".join(self.CAUSAL_INDICATORS), re.IGNORECASE
        )
        self._reference_pattern = re.compile(
            "|".join(self.REFERENCE_PATTERNS), re.IGNORECASE
        )
        self._conclusion_pattern = re.compile(
            "|".join(self.CONCLUSION_PATTERNS), re.IGNORECASE
        )

    def analyze(self, chain: ReasoningChain) -> CausalAnalysisResult:
        """Perform comprehensive causal analysis on a reasoning chain.

        Analyzes the chain to identify step importance, causal drivers,
        dependencies, and the conclusion.

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            CausalAnalysisResult with all analysis results.

        Example:
            >>> result = analyzer.analyze(chain)
            >>> print(f"Found {len(result.causal_drivers)} causal drivers")
        """
        step_importance = self.analyze_step_importance(chain)
        causal_drivers = self.find_causal_drivers(chain)
        dependency_graph = self.build_dependency_graph(chain)
        conclusion_step = self.identify_conclusion(chain)
        causal_relations = self._identify_causal_relations(chain)

        return CausalAnalysisResult(
            chain=chain,
            step_importance=step_importance,
            causal_drivers=causal_drivers,
            dependency_graph=dependency_graph,
            conclusion_step=conclusion_step,
            causal_relations=causal_relations,
        )

    def analyze_step_importance(self, chain: ReasoningChain) -> Dict[int, float]:
        """Rank importance of each step (index -> importance score).

        Calculates an importance score for each step based on:
        - Position in the chain
        - Causal language usage
        - Whether other steps reference it
        - Reasoning type

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            Dictionary mapping step index to importance score (0-1).

        Example:
            >>> importance = analyzer.analyze_step_importance(chain)
            >>> most_important = max(importance.items(), key=lambda x: x[1])
            >>> print(f"Most important: step {most_important[0]}")
        """
        if not chain.steps:
            return {}

        importance_scores: Dict[int, float] = {}
        dependency_graph = self.build_dependency_graph(chain)

        for step in chain.steps:
            score = 0.0

            # Base score by reasoning type
            type_scores = {
                ReasoningType.ACTION: 0.8,  # Conclusions are important
                ReasoningType.CAUSAL: 0.7,  # Causal reasoning is important
                ReasoningType.GOAL_REASONING: 0.6,
                ReasoningType.EVALUATION_AWARE: 0.5,
                ReasoningType.META_REASONING: 0.4,
                ReasoningType.FACTUAL: 0.5,
                ReasoningType.UNCERTAINTY: 0.3,
                ReasoningType.UNKNOWN: 0.3,
            }
            score += type_scores.get(step.reasoning_type, 0.3)

            # Bonus for causal language
            if self._causal_pattern.search(step.text):
                score += 0.15

            # Bonus for steps that others depend on
            dependents_count = sum(
                1 for deps in dependency_graph.values() if step.index in deps
            )
            score += min(0.2, dependents_count * 0.1)

            # Position-based scoring (conclusions often at end)
            if step.index == len(chain.steps) - 1:
                score += 0.1

            # Confidence weighting
            score *= (0.5 + 0.5 * step.confidence)

            importance_scores[step.index] = min(1.0, score)

        # Normalize scores
        if importance_scores:
            max_score = max(importance_scores.values())
            if max_score > 0:
                importance_scores = {
                    k: v / max_score for k, v in importance_scores.items()
                }

        return importance_scores

    def find_causal_drivers(self, chain: ReasoningChain) -> List[ReasoningStep]:
        """Find steps that are causal drivers of the conclusion.

        Identifies steps that are critical to reaching the final conclusion,
        based on their position in the causal dependency structure.

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            List of ReasoningStep objects that are causal drivers.

        Example:
            >>> drivers = analyzer.find_causal_drivers(chain)
            >>> for driver in drivers:
            ...     print(f"Driver step {driver.index}: {driver.text[:50]}...")
        """
        if not chain.steps:
            return []

        # Get conclusion step
        conclusion = self.identify_conclusion(chain)
        if conclusion is None and chain.steps:
            # Use last step as default conclusion
            conclusion = chain.steps[-1]

        if conclusion is None:
            return []

        # Build dependency graph
        dependency_graph = self.build_dependency_graph(chain)

        # Find all steps that the conclusion depends on (directly or indirectly)
        causal_drivers_indices: Set[int] = set()

        def find_dependencies(step_index: int, visited: Set[int]) -> None:
            """Recursively find all dependencies."""
            if step_index in visited:
                return
            visited.add(step_index)

            dependencies = dependency_graph.get(step_index, [])
            for dep_index in dependencies:
                causal_drivers_indices.add(dep_index)
                find_dependencies(dep_index, visited)

        find_dependencies(conclusion.index, set())

        # Add steps with high causal content even if not in dependency chain
        for step in chain.steps:
            if step.reasoning_type == ReasoningType.CAUSAL:
                causal_drivers_indices.add(step.index)

        # Get the actual steps
        causal_drivers = [
            step for step in chain.steps if step.index in causal_drivers_indices
        ]

        # Sort by importance
        importance = self.analyze_step_importance(chain)
        causal_drivers.sort(key=lambda s: importance.get(s.index, 0), reverse=True)

        return causal_drivers

    def build_dependency_graph(self, chain: ReasoningChain) -> Dict[int, List[int]]:
        """Build graph of which steps depend on which.

        Creates a directed graph where edges point from a step to the
        steps it depends on (references or uses).

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            Dictionary mapping step index to list of dependency indices.

        Example:
            >>> graph = analyzer.build_dependency_graph(chain)
            >>> print(f"Step 3 depends on steps: {graph.get(3, [])}")
        """
        if not chain.steps:
            return {}

        dependency_graph: Dict[int, List[int]] = {step.index: [] for step in chain.steps}

        for step in chain.steps:
            dependencies = self._find_step_dependencies(step, chain)
            dependency_graph[step.index] = dependencies

        return dependency_graph

    def identify_conclusion(self, chain: ReasoningChain) -> Optional[ReasoningStep]:
        """Identify the conclusion/decision step.

        Finds the step that represents the final conclusion or decision
        in the reasoning chain.

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            The conclusion step if found, None otherwise.

        Example:
            >>> conclusion = analyzer.identify_conclusion(chain)
            >>> if conclusion:
            ...     print(f"Conclusion: {conclusion.text}")
        """
        if not chain.steps:
            return None

        # Look for action steps (highest priority)
        action_steps = chain.get_steps_by_type(ReasoningType.ACTION)
        if action_steps:
            # Prefer action steps near the end
            return max(action_steps, key=lambda s: s.index)

        # Look for explicit conclusion language
        for step in reversed(chain.steps):
            if self._conclusion_pattern.search(step.text):
                return step

        # Check for steps with strong conclusion indicators
        conclusion_scores: List[Tuple[int, float]] = []
        for step in chain.steps:
            score = 0.0

            # Check for conclusion patterns
            matches = self._conclusion_pattern.findall(step.text)
            score += len(matches) * 0.3

            # Position bonus (later steps more likely to be conclusion)
            position_bonus = step.index / len(chain.steps) if chain.steps else 0
            score += position_bonus * 0.3

            # Type bonus
            if step.reasoning_type == ReasoningType.ACTION:
                score += 0.4

            if score > 0:
                conclusion_scores.append((step.index, score))

        if conclusion_scores:
            best_index = max(conclusion_scores, key=lambda x: x[1])[0]
            return chain.steps[best_index]

        # Default to last step
        return chain.steps[-1] if chain.steps else None

    def _find_step_dependencies(
        self, step: ReasoningStep, chain: ReasoningChain
    ) -> List[int]:
        """Find which previous steps a given step depends on.

        Args:
            step: The step to find dependencies for.
            chain: The full reasoning chain.

        Returns:
            List of step indices that this step depends on.
        """
        dependencies: List[int] = []
        text_lower = step.text.lower()

        # Check for explicit references to previous content
        has_reference = self._reference_pattern.search(step.text) is not None

        # Check for causal links
        has_causal = self._causal_pattern.search(step.text) is not None

        if has_reference or has_causal:
            # Look for content overlap with previous steps
            step_words = set(step.text.lower().split())

            for prev_step in chain.steps:
                if prev_step.index >= step.index:
                    continue

                prev_words = set(prev_step.text.lower().split())

                # Check for significant word overlap (excluding common words)
                common_words = {
                    "the", "a", "an", "is", "are", "was", "were", "be", "been",
                    "being", "have", "has", "had", "do", "does", "did", "will",
                    "would", "could", "should", "may", "might", "must", "can",
                    "to", "of", "in", "for", "on", "with", "at", "by", "from",
                    "i", "my", "this", "that", "it", "and", "or", "but", "so",
                }

                step_content = step_words - common_words
                prev_content = prev_words - common_words

                overlap = step_content & prev_content
                if len(overlap) >= 2 or (len(overlap) >= 1 and has_causal):
                    dependencies.append(prev_step.index)

        # By default, assume immediate predecessor dependency for sequential reasoning
        if not dependencies and step.index > 0:
            dependencies.append(step.index - 1)

        return dependencies

    def _identify_causal_relations(self, chain: ReasoningChain) -> List[CausalRelation]:
        """Identify all causal relations in the chain.

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            List of CausalRelation objects.
        """
        relations: List[CausalRelation] = []
        dependency_graph = self.build_dependency_graph(chain)

        for step_index, dependencies in dependency_graph.items():
            for dep_index in dependencies:
                # Calculate relation strength based on content overlap and language
                step = chain.steps[step_index]
                dep_step = chain.steps[dep_index]

                strength = self._calculate_relation_strength(dep_step, step)
                relation_type = self._classify_relation_type(dep_step, step)

                relations.append(
                    CausalRelation(
                        cause_index=dep_index,
                        effect_index=step_index,
                        strength=strength,
                        relation_type=relation_type,
                    )
                )

        return relations

    def _calculate_relation_strength(
        self, cause: ReasoningStep, effect: ReasoningStep
    ) -> float:
        """Calculate strength of causal relationship between two steps.

        Args:
            cause: The causing step.
            effect: The effect step.

        Returns:
            Strength score between 0 and 1.
        """
        strength = 0.5  # Base strength

        # Stronger if effect has explicit causal language
        if self._causal_pattern.search(effect.text):
            strength += 0.2

        # Stronger if effect references cause's content
        cause_words = set(cause.text.lower().split())
        effect_words = set(effect.text.lower().split())
        common_words = {
            "the", "a", "an", "is", "are", "to", "of", "in", "for", "and", "or",
        }
        meaningful_overlap = (cause_words & effect_words) - common_words
        if meaningful_overlap:
            strength += min(0.2, len(meaningful_overlap) * 0.05)

        # Stronger for certain type combinations
        if cause.reasoning_type == ReasoningType.FACTUAL and effect.reasoning_type == ReasoningType.ACTION:
            strength += 0.1

        # Weaker if steps are far apart
        distance = abs(effect.index - cause.index)
        if distance > 3:
            strength -= 0.1

        return max(0.0, min(1.0, strength))

    def _classify_relation_type(
        self, cause: ReasoningStep, effect: ReasoningStep
    ) -> str:
        """Classify the type of causal relationship.

        Args:
            cause: The causing step.
            effect: The effect step.

        Returns:
            Relation type string.
        """
        effect_text = effect.text.lower()

        # Check for explicit logical connectors
        if any(re.search(p, effect_text) for p in [r"\btherefore\b", r"\bthus\b", r"\bhence\b"]):
            return "logical_inference"

        # Check for causal language
        if any(re.search(p, effect_text) for p in [r"\bbecause\b", r"\bsince\b", r"\bdue to\b"]):
            return "causal_explanation"

        # Check for temporal sequence
        if any(re.search(p, effect_text) for p in [r"\bthen\b", r"\bnext\b", r"\bafter\b"]):
            return "temporal_sequence"

        # Check for supporting relationship
        if any(re.search(p, effect_text) for p in [r"\bsupports\b", r"\bconfirms\b", r"\bvalidates\b"]):
            return "supporting_evidence"

        # Default
        return "dependency"

    def compute_causal_path(
        self, chain: ReasoningChain, start_index: int, end_index: int
    ) -> List[int]:
        """Compute the causal path between two steps.

        Finds the sequence of steps that causally connect the start step
        to the end step, if such a path exists.

        Args:
            chain: The reasoning chain.
            start_index: Index of the starting step.
            end_index: Index of the target step.

        Returns:
            List of step indices forming the causal path, or empty if no path.

        Example:
            >>> path = analyzer.compute_causal_path(chain, 0, 5)
            >>> print(f"Causal path: {' -> '.join(str(i) for i in path)}")
        """
        if start_index == end_index:
            return [start_index]

        if start_index >= len(chain.steps) or end_index >= len(chain.steps):
            return []

        dependency_graph = self.build_dependency_graph(chain)

        # BFS from end to start through dependencies
        visited: Set[int] = set()
        queue: List[Tuple[int, List[int]]] = [(end_index, [end_index])]

        while queue:
            current, path = queue.pop(0)

            if current in visited:
                continue
            visited.add(current)

            if current == start_index:
                return list(reversed(path))

            dependencies = dependency_graph.get(current, [])
            for dep in dependencies:
                if dep not in visited:
                    queue.append((dep, path + [dep]))

        return []  # No path found
