"""
Decision path analysis for understanding sequences of decisions.

This module provides the DecisionPathAnalyzer class for analyzing
complete decision paths, finding critical decisions, and identifying
failure points.
"""

from typing import Any, Dict, List, Optional

from rotalabs_audit.core.types import (
    ConfidenceLevel,
    DecisionPath,
    DecisionTrace,
)


class DecisionPathAnalyzer:
    """
    Analyze sequences of decisions in a decision path.

    Provides tools for analyzing complete decision paths, identifying
    critical decisions, finding failure points, and generating summaries.

    Example:
        >>> analyzer = DecisionPathAnalyzer()
        >>> analysis = analyzer.analyze_path(path)
        >>> print(f"Critical decisions: {len(analysis['critical_decisions'])}")
    """

    def __init__(self) -> None:
        """Initialize the decision path analyzer."""
        pass

    def analyze_path(self, path: DecisionPath) -> Dict[str, Any]:
        """
        Analyze a complete decision path.

        Performs comprehensive analysis of a decision path including
        statistics, critical decisions, and quality metrics.

        Args:
            path: The decision path to analyze.

        Returns:
            Dictionary containing analysis results:
                - decision_count: Number of decisions in the path
                - avg_confidence: Average confidence across decisions
                - min_confidence: Minimum confidence in any decision
                - max_confidence: Maximum confidence in any decision
                - critical_decisions: List of critical decision IDs
                - reversible_count: Number of reversible decisions
                - irreversible_count: Number of irreversible decisions
                - success: Whether the path was successful
                - failure_point_id: ID of the failure point (if applicable)
                - total_alternatives: Total alternatives considered across all decisions

        Example:
            >>> analysis = analyzer.analyze_path(path)
            >>> print(f"Success rate: {analysis['success']}")
            >>> print(f"Avg confidence: {analysis['avg_confidence']:.2f}")
        """
        if not path.decisions:
            return {
                "decision_count": 0,
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "critical_decisions": [],
                "reversible_count": 0,
                "irreversible_count": 0,
                "success": path.success,
                "failure_point_id": None,
                "total_alternatives": 0,
            }

        confidences = [d.confidence for d in path.decisions]
        critical = self.find_critical_decisions(path)
        failure = self.find_failure_point(path)

        reversible_count = sum(1 for d in path.decisions if d.reversible)
        irreversible_count = len(path.decisions) - reversible_count

        total_alternatives = sum(
            len(d.alternatives_considered) for d in path.decisions
        )

        return {
            "decision_count": len(path.decisions),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "critical_decisions": [d.id for d in critical],
            "reversible_count": reversible_count,
            "irreversible_count": irreversible_count,
            "success": path.success,
            "failure_point_id": failure.id if failure else None,
            "total_alternatives": total_alternatives,
        }

    def find_critical_decisions(self, path: DecisionPath) -> List[DecisionTrace]:
        """
        Find decisions that were critical to the outcome.

        Identifies decisions that significantly impacted the path's
        success or failure based on various criteria.

        Args:
            path: The decision path to analyze.

        Returns:
            List of critical DecisionTrace objects.

        Criteria for critical decisions:
            - Irreversible decisions (cannot be undone)
            - Low confidence decisions (uncertainty)
            - Decisions with multiple alternatives
            - First and last decisions in the path

        Example:
            >>> critical = analyzer.find_critical_decisions(path)
            >>> for decision in critical:
            ...     print(f"Critical: {decision.decision[:50]}...")
        """
        critical: List[DecisionTrace] = []

        if not path.decisions:
            return critical

        for i, decision in enumerate(path.decisions):
            is_critical = False
            reasons: List[str] = []

            # Irreversible decisions are critical
            if not decision.reversible:
                is_critical = True
                reasons.append("irreversible")

            # Low confidence decisions are critical
            if decision.confidence < 0.5:
                is_critical = True
                reasons.append("low_confidence")

            # Decisions with many alternatives suggest complexity
            if len(decision.alternatives_considered) >= 3:
                is_critical = True
                reasons.append("many_alternatives")

            # First decision sets the trajectory
            if i == 0:
                is_critical = True
                reasons.append("initial_decision")

            # Last decision is critical for outcome
            if i == len(path.decisions) - 1:
                is_critical = True
                reasons.append("final_decision")

            if is_critical:
                # Store reasons in metadata (create a copy to avoid mutation)
                decision_copy = decision
                decision_copy.metadata["critical_reasons"] = reasons
                critical.append(decision_copy)

        return critical

    def find_failure_point(self, path: DecisionPath) -> Optional[DecisionTrace]:
        """
        If path failed, find where it went wrong.

        Analyzes a failed decision path to identify the decision most
        likely responsible for the failure.

        Args:
            path: The decision path to analyze.

        Returns:
            The DecisionTrace that likely caused failure, or None if
            the path succeeded or has no decisions.

        Heuristics for finding failure point:
            - Check if path already has a failure_point set
            - Last irreversible decision before failure
            - Decision with lowest confidence
            - Decision with most alternatives (indecision)

        Example:
            >>> if not path.success:
            ...     failure = analyzer.find_failure_point(path)
            ...     if failure:
            ...         print(f"Failed at: {failure.decision}")
        """
        # If path succeeded or has no decisions, no failure point
        if path.success or not path.decisions:
            return None

        # Check if path already has a failure point identified
        if path.failure_point is not None:
            return path.failure_point

        # Find the last irreversible decision
        last_irreversible: Optional[DecisionTrace] = None
        for decision in path.decisions:
            if not decision.reversible:
                last_irreversible = decision

        # If there was an irreversible decision, it's likely the failure point
        if last_irreversible:
            return last_irreversible

        # Otherwise, find the decision with lowest confidence
        min_confidence = float("inf")
        lowest_confidence_decision: Optional[DecisionTrace] = None

        for decision in path.decisions:
            if decision.confidence < min_confidence:
                min_confidence = decision.confidence
                lowest_confidence_decision = decision

        # If there's a very low confidence decision, it's suspect
        if lowest_confidence_decision and min_confidence < 0.4:
            return lowest_confidence_decision

        # Default to the last decision
        return path.decisions[-1]

    def calculate_path_confidence(self, path: DecisionPath) -> float:
        """
        Calculate overall confidence in the decision path.

        Computes a weighted confidence score based on individual
        decision confidences, with emphasis on critical decisions.

        Args:
            path: The decision path to analyze.

        Returns:
            Overall confidence score between 0.0 and 1.0.

        The calculation:
            - Base: weighted average of all decision confidences
            - Penalty for irreversible low-confidence decisions
            - Penalty for having many alternatives (indecision)

        Example:
            >>> confidence = analyzer.calculate_path_confidence(path)
            >>> if confidence < 0.5:
            ...     print("Warning: Low confidence path")
        """
        if not path.decisions:
            return 0.0

        # Calculate weighted confidence
        total_weight = 0.0
        weighted_confidence = 0.0

        for i, decision in enumerate(path.decisions):
            # Weight: more weight for irreversible and early decisions
            weight = 1.0

            if not decision.reversible:
                weight *= 2.0  # Irreversible decisions count double

            if i == 0:
                weight *= 1.5  # Initial decisions are important

            if i == len(path.decisions) - 1:
                weight *= 1.5  # Final decisions are important

            weighted_confidence += decision.confidence * weight
            total_weight += weight

        base_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0

        # Penalty for low-confidence irreversible decisions
        for decision in path.decisions:
            if not decision.reversible and decision.confidence < 0.5:
                base_confidence -= 0.1

        # Penalty for many alternatives (suggests uncertainty)
        avg_alternatives = (
            sum(len(d.alternatives_considered) for d in path.decisions)
            / len(path.decisions)
        )
        if avg_alternatives > 2:
            base_confidence -= 0.05 * (avg_alternatives - 2)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, base_confidence))

    def summarize_path(self, path: DecisionPath) -> str:
        """
        Generate a human-readable summary of the decision path.

        Creates a text summary describing the path's goal, key decisions,
        outcome, and any notable observations.

        Args:
            path: The decision path to summarize.

        Returns:
            Human-readable summary string.

        Example:
            >>> summary = analyzer.summarize_path(path)
            >>> print(summary)
        """
        if not path.decisions:
            return f"Empty decision path for goal: {path.goal or 'No goal specified'}"

        lines = []

        # Header with goal
        lines.append("Decision Path Summary")
        lines.append("=" * 40)
        lines.append(f"Goal: {path.goal or 'Not specified'}")

        if path.success is not None:
            lines.append(f"Outcome: {'Success' if path.success else 'Failed'}")
        else:
            lines.append("Outcome: In Progress")

        lines.append(f"Total Decisions: {len(path.decisions)}")
        lines.append("")

        # Path confidence
        confidence = self.calculate_path_confidence(path)
        confidence_level = ConfidenceLevel.from_score(confidence)
        lines.append(f"Overall Confidence: {confidence:.1%} ({confidence_level.value})")
        lines.append("")

        # Key decisions
        lines.append("Key Decisions:")
        lines.append("-" * 20)

        for i, decision in enumerate(path.decisions, 1):
            # Truncate long decisions
            decision_text = decision.decision[:60]
            if len(decision.decision) > 60:
                decision_text += "..."

            conf_level = decision.confidence_level.value.upper()
            reversible_indicator = "" if decision.reversible else " [IRREVERSIBLE]"

            lines.append(
                f"{i}. [{conf_level}] {decision_text}{reversible_indicator}"
            )

        lines.append("")

        # Critical decisions
        critical = self.find_critical_decisions(path)
        if critical:
            lines.append(f"Critical Decisions: {len(critical)}")
            for decision in critical[:3]:  # Show top 3
                reasons = decision.metadata.get("critical_reasons", [])
                lines.append(
                    f"  - {decision.decision[:40]}... ({', '.join(reasons)})"
                )

        # Failure analysis if failed
        if path.success is False:
            lines.append("")
            lines.append("Failure Analysis:")
            failure = self.find_failure_point(path)
            if failure:
                lines.append(f"  Likely failure point: {failure.decision[:50]}...")
                lines.append(f"  Confidence at failure: {failure.confidence:.1%}")
            else:
                lines.append("  Unable to identify specific failure point")

        return "\n".join(lines)

    def compare_paths(
        self,
        path1: DecisionPath,
        path2: DecisionPath,
    ) -> Dict[str, Any]:
        """
        Compare two decision paths.

        Analyzes differences between two decision paths including
        confidence, decision count, and outcome.

        Args:
            path1: First decision path.
            path2: Second decision path.

        Returns:
            Dictionary with comparison results.

        Example:
            >>> comparison = analyzer.compare_paths(path_a, path_b)
            >>> print(f"Better path: {comparison['better_path']}")
        """
        analysis1 = self.analyze_path(path1)
        analysis2 = self.analyze_path(path2)

        conf1 = self.calculate_path_confidence(path1)
        conf2 = self.calculate_path_confidence(path2)

        # Determine which path is "better"
        score1 = conf1 + (0.2 if path1.success else 0)
        score2 = conf2 + (0.2 if path2.success else 0)

        if score1 > score2:
            better_path = "path1"
        elif score2 > score1:
            better_path = "path2"
        else:
            better_path = "equal"

        return {
            "path1": {
                "id": path1.id,
                "decision_count": analysis1["decision_count"],
                "avg_confidence": analysis1["avg_confidence"],
                "success": path1.success,
                "path_confidence": conf1,
            },
            "path2": {
                "id": path2.id,
                "decision_count": analysis2["decision_count"],
                "avg_confidence": analysis2["avg_confidence"],
                "success": path2.success,
                "path_confidence": conf2,
            },
            "better_path": better_path,
            "confidence_difference": abs(conf1 - conf2),
            "decision_count_difference": abs(
                analysis1["decision_count"] - analysis2["decision_count"]
            ),
        }

    def find_divergence_point(
        self,
        path1: DecisionPath,
        path2: DecisionPath,
    ) -> Optional[int]:
        """
        Find where two decision paths diverge.

        Compares decisions in order to find the first point where
        the paths made different decisions.

        Args:
            path1: First decision path.
            path2: Second decision path.

        Returns:
            Index of the first divergent decision, or None if paths
            don't diverge or one is a prefix of the other.

        Example:
            >>> divergence = analyzer.find_divergence_point(path_a, path_b)
            >>> if divergence is not None:
            ...     print(f"Paths diverged at decision {divergence}")
        """
        min_len = min(len(path1.decisions), len(path2.decisions))

        for i in range(min_len):
            d1 = path1.decisions[i]
            d2 = path2.decisions[i]

            # Compare decisions (simple string comparison)
            if d1.decision.lower().strip() != d2.decision.lower().strip():
                return i

        # If we got here, one path is a prefix of the other
        if len(path1.decisions) != len(path2.decisions):
            return min_len

        return None

    def get_confidence_trend(self, path: DecisionPath) -> List[float]:
        """
        Get the confidence trend across decisions.

        Returns the sequence of confidence values to identify
        patterns like declining confidence.

        Args:
            path: The decision path to analyze.

        Returns:
            List of confidence values in decision order.

        Example:
            >>> trend = analyzer.get_confidence_trend(path)
            >>> if trend[-1] < trend[0]:
            ...     print("Confidence declined over the path")
        """
        return [d.confidence for d in path.decisions]

    def detect_confidence_decline(
        self,
        path: DecisionPath,
        threshold: float = 0.2,
    ) -> bool:
        """
        Detect if confidence declined significantly over the path.

        Args:
            path: The decision path to analyze.
            threshold: Minimum decline to be considered significant.

        Returns:
            True if confidence declined by more than the threshold.

        Example:
            >>> if analyzer.detect_confidence_decline(path):
            ...     print("Warning: Confidence declined over the decision path")
        """
        if len(path.decisions) < 2:
            return False

        first_confidence = path.decisions[0].confidence
        last_confidence = path.decisions[-1].confidence

        return (first_confidence - last_confidence) > threshold
