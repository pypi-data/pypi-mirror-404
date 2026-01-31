"""
Decision tracing for capturing and analyzing AI decision points.

This module provides the DecisionTracer class for tracing decision points
in AI reasoning, extracting alternatives, and building decision paths.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from rotalabs_audit.core.types import (
    DecisionPath,
    DecisionTrace,
    ReasoningChain,
    ReasoningStep,
    ReasoningType,
)


class ReasoningChainParser:
    """
    Parser for chain-of-thought reasoning text.

    Extracts structured reasoning chains from raw text, classifying
    each step by type and estimating confidence levels.

    Example:
        >>> parser = ReasoningChainParser()
        >>> chain = parser.parse("First, I'll analyze... Then, considering...")
        >>> print(f"Found {chain.step_count} reasoning steps")
    """

    def __init__(self) -> None:
        """Initialize the parser with compiled regex patterns."""
        # Evaluation awareness patterns
        self._eval_patterns = re.compile(
            r"\b(test|evaluat|assess|check|examin|measuring|being tested|"
            r"you're testing|this is a test|evaluation context)\b",
            re.IGNORECASE,
        )

        # Goal reasoning patterns
        self._goal_patterns = re.compile(
            r"\b(goal|objective|aim|purpose|intend|want to|need to|"
            r"should|must|have to|trying to)\b",
            re.IGNORECASE,
        )

        # Meta-reasoning patterns
        self._meta_patterns = re.compile(
            r"\b(i think|i believe|i reason|my reasoning|my thought|"
            r"let me think|considering|analyzing|reflect)\b",
            re.IGNORECASE,
        )

        # Decision/action patterns
        self._decision_patterns = re.compile(
            r"\b(will|shall|going to|decide|choose|select|answer|respond|"
            r"therefore|thus|so|conclusion|recommend|suggest)\b",
            re.IGNORECASE,
        )

        # Causal reasoning patterns
        self._causal_patterns = re.compile(
            r"\b(because|since|therefore|thus|hence|implies|means|"
            r"indicates|suggests|conclude|infer|deduce|cause|effect)\b",
            re.IGNORECASE,
        )

        # Uncertainty patterns
        self._uncertainty_patterns = re.compile(
            r"\b(uncertain|maybe|perhaps|possibly|might|could|"
            r"not sure|unclear|doubt|tentative|probably)\b",
            re.IGNORECASE,
        )

        # Hypothetical patterns
        self._hypothetical_patterns = re.compile(
            r"\b(if|what if|suppose|assuming|hypothetically|imagine|"
            r"consider the case|in the scenario)\b",
            re.IGNORECASE,
        )

        # Incentive patterns
        self._incentive_patterns = re.compile(
            r"\b(reward|penalty|consequence|outcome|benefit|"
            r"advantage|disadvantage|cost|payoff|incentive)\b",
            re.IGNORECASE,
        )

        # High confidence markers
        self._confidence_high = re.compile(
            r"\b(certain|definitely|clearly|obviously|undoubtedly|"
            r"without doubt|confident|sure|absolutely)\b",
            re.IGNORECASE,
        )

        # Low confidence markers
        self._confidence_low = re.compile(
            r"\b(uncertain|maybe|perhaps|possibly|might|could|"
            r"not sure|unclear|doubt|tentative)\b",
            re.IGNORECASE,
        )

    def parse(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> ReasoningChain:
        """
        Parse chain-of-thought text into a structured ReasoningChain.

        Args:
            text: The chain-of-thought text to parse.
            model: Optional model identifier that generated this text.

        Returns:
            ReasoningChain with parsed steps, confidence, and depth.

        Raises:
            ValueError: If text is empty or invalid.

        Example:
            >>> parser = ReasoningChainParser()
            >>> chain = parser.parse("1. First, let me analyze the problem...")
            >>> print(chain.steps[0].reasoning_type)
        """
        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")

        # Split into steps
        steps_text = self._split_into_steps(text)

        # Parse each step
        steps: List[ReasoningStep] = []
        for i, step_text in enumerate(steps_text):
            step_type = self._classify_step(step_text)
            confidence = self._estimate_confidence(step_text)
            steps.append(
                ReasoningStep(
                    content=step_text,
                    reasoning_type=step_type,
                    confidence=confidence,
                    index=i,
                )
            )

        # Calculate parsing confidence
        parsing_confidence = self._calculate_parsing_confidence(steps)

        return ReasoningChain(
            id=str(uuid.uuid4())[:8],
            steps=steps,
            raw_text=text,
            model=model,
            parsing_confidence=parsing_confidence,
        )

    def _split_into_steps(self, text: str) -> List[str]:
        """
        Split text into individual reasoning steps.

        Handles numbered lists, bullet points, and sentence-based splitting.

        Args:
            text: The text to split.

        Returns:
            List of step texts.
        """
        # Try to split by common reasoning delimiters
        # Numbered steps: "1.", "1)", "Step 1:"
        step_pattern = r"(?:^|\n)(?:\d+[\.\)]\s*|step \d+:?\s*|-\s*|\*\s*)"
        steps = re.split(step_pattern, text, flags=re.IGNORECASE | re.MULTILINE)

        # Filter out empty steps
        steps = [s.strip() for s in steps if s.strip()]

        # If no explicit steps found, split by sentences
        if len(steps) <= 1:
            steps = re.split(r"[.!?]+", text)
            steps = [s.strip() for s in steps if s.strip()]

        return steps

    def _classify_step(self, text: str) -> ReasoningType:
        """
        Classify a reasoning step by type.

        Args:
            text: The step text to classify.

        Returns:
            The ReasoningType classification.
        """
        if not text:
            return ReasoningType.UNKNOWN

        # Check patterns in order of specificity
        if self._eval_patterns.search(text):
            return ReasoningType.EVALUATION_AWARE

        if self._uncertainty_patterns.search(text):
            return ReasoningType.UNCERTAINTY

        if self._hypothetical_patterns.search(text):
            return ReasoningType.HYPOTHETICAL

        if self._incentive_patterns.search(text):
            return ReasoningType.INCENTIVE_REASONING

        if self._decision_patterns.search(text):
            return ReasoningType.DECISION_MAKING

        if self._causal_patterns.search(text):
            return ReasoningType.CAUSAL_REASONING

        if self._goal_patterns.search(text):
            return ReasoningType.GOAL_REASONING

        if self._meta_patterns.search(text):
            return ReasoningType.META_REASONING

        return ReasoningType.FACTUAL_KNOWLEDGE

    def _estimate_confidence(self, text: str) -> float:
        """
        Estimate confidence based on linguistic markers.

        Args:
            text: The text to analyze.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if not text:
            return 0.5  # Neutral default

        high_matches = len(self._confidence_high.findall(text))
        low_matches = len(self._confidence_low.findall(text))

        # Base confidence
        confidence = 0.5

        # Adjust based on markers
        confidence += high_matches * 0.1
        confidence -= low_matches * 0.1

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def _calculate_parsing_confidence(self, steps: List[ReasoningStep]) -> float:
        """
        Calculate confidence in the quality of parsing.

        Args:
            steps: The parsed steps.

        Returns:
            Parsing confidence between 0.0 and 1.0.
        """
        if not steps:
            return 0.0

        # High confidence if we found structured steps
        if len(steps) > 1:
            base_confidence = 0.7
        else:
            base_confidence = 0.5

        # Boost if we classified most steps successfully
        classified_count = sum(
            1 for s in steps if s.reasoning_type != ReasoningType.UNKNOWN
        )
        classification_ratio = classified_count / len(steps)
        base_confidence += 0.2 * classification_ratio

        return min(1.0, base_confidence)


class DecisionTracer:
    """
    Trace and capture decision points in AI reasoning.

    Provides tools for creating decision traces from AI interactions,
    managing active trace sessions, and extracting decision-related
    information from reasoning text.

    Attributes:
        parser: ReasoningChainParser for parsing reasoning text.
        _active_traces: Dictionary of currently active trace sessions.

    Example:
        >>> tracer = DecisionTracer()
        >>> trace = tracer.trace_decision(
        ...     prompt="What approach should I use?",
        ...     response="I recommend approach A because...",
        ...     decision="Use approach A",
        ... )
        >>> print(f"Alternatives: {trace.alternatives_considered}")
    """

    def __init__(self, parser: Optional[ReasoningChainParser] = None) -> None:
        """
        Initialize the decision tracer.

        Args:
            parser: Optional ReasoningChainParser instance. If not provided,
                a new parser will be created.
        """
        self.parser = parser or ReasoningChainParser()
        self._active_traces: Dict[str, _ActiveTrace] = {}

    def trace_decision(
        self,
        prompt: str,
        response: str,
        decision: str,
        model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionTrace:
        """
        Create a decision trace from an AI interaction.

        Parses the response for reasoning, extracts alternatives considered,
        identifies the rationale, and creates a structured DecisionTrace.

        Args:
            prompt: The prompt/question that led to this decision.
            response: The full AI response containing the decision.
            decision: The decision that was made (explicit statement).
            model: Optional model identifier.
            context: Optional additional context dictionary.

        Returns:
            DecisionTrace capturing the decision details.

        Example:
            >>> trace = tracer.trace_decision(
            ...     prompt="Should we deploy now or wait?",
            ...     response="After considering the risks... I recommend waiting.",
            ...     decision="Wait for deployment",
            ...     model="gpt-4",
            ... )
        """
        # Parse the response for reasoning
        reasoning_chain = self.parser.parse(response, model=model)

        # Extract alternatives considered
        alternatives = self.extract_alternatives(response)

        # Extract rationale
        rationale = self.extract_rationale(reasoning_chain)

        # Estimate confidence based on reasoning chain
        confidence = self._estimate_decision_confidence(reasoning_chain, response)

        # Assess reversibility
        reversible = self.assess_reversibility(decision, context or {})

        return DecisionTrace(
            id=str(uuid.uuid4())[:8],
            decision=decision,
            timestamp=datetime.utcnow(),
            context=context or {},
            reasoning_chain=reasoning_chain,
            alternatives_considered=alternatives,
            rationale=rationale,
            confidence=confidence,
            reversible=reversible,
            metadata={"prompt": prompt, "model": model},
        )

    def start_trace(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start tracing a decision path.

        Begins a new trace session for capturing a sequence of decisions
        related to achieving a specific goal.

        Args:
            goal: The goal or objective for this decision path.
            context: Optional context that applies to all decisions in the path.

        Returns:
            trace_id: Unique identifier for this trace session.

        Example:
            >>> trace_id = tracer.start_trace("Complete the data analysis")
            >>> # ... make decisions ...
            >>> path = tracer.end_trace(trace_id, success=True)
        """
        trace_id = str(uuid.uuid4())[:8]

        self._active_traces[trace_id] = _ActiveTrace(
            id=trace_id,
            goal=goal,
            decisions=[],
            context=context or {},
            start_time=datetime.utcnow(),
        )

        return trace_id

    def add_decision(
        self,
        trace_id: str,
        decision: DecisionTrace,
    ) -> None:
        """
        Add a decision to an active trace.

        Appends a decision trace to an ongoing trace session.

        Args:
            trace_id: The ID of the active trace session.
            decision: The DecisionTrace to add.

        Raises:
            KeyError: If trace_id does not correspond to an active trace.

        Example:
            >>> trace_id = tracer.start_trace("Complete task")
            >>> decision = tracer.trace_decision(...)
            >>> tracer.add_decision(trace_id, decision)
        """
        if trace_id not in self._active_traces:
            raise KeyError(f"No active trace found with ID: {trace_id}")

        self._active_traces[trace_id].decisions.append(decision)

    def end_trace(
        self,
        trace_id: str,
        success: bool,
    ) -> DecisionPath:
        """
        End tracing and return the complete decision path.

        Finalizes a trace session, marking it as successful or not,
        and returns the complete DecisionPath.

        Args:
            trace_id: The ID of the active trace session.
            success: Whether the decision path achieved its goal.

        Returns:
            The complete DecisionPath with all decisions.

        Raises:
            KeyError: If trace_id does not correspond to an active trace.

        Example:
            >>> path = tracer.end_trace(trace_id, success=True)
            >>> print(f"Made {path.length} decisions, success: {path.success}")
        """
        if trace_id not in self._active_traces:
            raise KeyError(f"No active trace found with ID: {trace_id}")

        active = self._active_traces.pop(trace_id)

        return DecisionPath(
            id=active.id,
            decisions=active.decisions,
            goal=active.goal,
            success=success,
            metadata={"context": active.context, "start_time": active.start_time.isoformat()},
        )

    def get_active_trace_ids(self) -> List[str]:
        """
        List all active trace IDs.

        Returns:
            List of active trace session IDs.
        """
        return list(self._active_traces.keys())

    def cancel_trace(self, trace_id: str) -> bool:
        """
        Cancel an active trace without creating a DecisionPath.

        Args:
            trace_id: The ID of the trace to cancel.

        Returns:
            True if the trace was cancelled, False if not found.
        """
        if trace_id in self._active_traces:
            del self._active_traces[trace_id]
            return True
        return False

    def extract_alternatives(self, text: str) -> List[str]:
        """
        Extract alternatives considered from reasoning text.

        Looks for phrases indicating alternative options that were
        considered during decision-making.

        Args:
            text: The reasoning text to analyze.

        Returns:
            List of alternatives mentioned in the text.

        Example:
            >>> alternatives = tracer.extract_alternatives(
            ...     "We could use option A, alternatively option B, or option C"
            ... )
            >>> print(alternatives)  # ["option B", "option C"]
        """
        alternatives: List[str] = []

        # Patterns for identifying alternatives
        patterns = [
            # "alternatively, X"
            r"alternatively[,:]?\s*([^.!?]+)",
            # "another option is X"
            r"another (?:option|approach|way|method|alternative) (?:is|would be)[,:]?\s*([^.!?]+)",
            # "could also X"
            r"could also\s+([^.!?]+)",
            # "or we could X"
            r"or (?:we |you |one )?could\s+([^.!?]+)",
            # "option B is..."
            r"option [B-Z]\s+(?:is|would be)\s+([^.!?]+)",
            # "on the other hand"
            r"on the other hand[,:]?\s*([^.!?]+)",
            # "however, X could work"
            r"however[,:]?\s*([^.!?]+?)\s*(?:could|might|would)\s+(?:also\s+)?work",
            # "X is also possible"
            r"([^.!?]+?)\s+is also (?:possible|an option|viable)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cleaned = match.strip()
                if cleaned and len(cleaned) > 5 and cleaned not in alternatives:
                    alternatives.append(cleaned)

        # Also look for numbered/bulleted alternatives
        list_pattern = r"(?:^|\n)\s*(?:\d+[\.\)]|[-*])\s*([^.!?\n]+)(?:\s*\((?:alternative|option|rejected)\))"
        list_matches = re.findall(list_pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in list_matches:
            cleaned = match.strip()
            if cleaned and cleaned not in alternatives:
                alternatives.append(cleaned)

        return alternatives

    def extract_rationale(self, chain: ReasoningChain) -> str:
        """
        Extract the main rationale from a reasoning chain.

        Identifies the primary justification or reasoning that supports
        the decision made.

        Args:
            chain: The reasoning chain to analyze.

        Returns:
            The extracted rationale as a string.

        Example:
            >>> chain = parser.parse("I recommend A because it's faster and safer...")
            >>> rationale = tracer.extract_rationale(chain)
        """
        rationale_parts: List[str] = []

        # Look for causal reasoning steps - these often contain rationale
        causal_steps = chain.get_steps_by_type(ReasoningType.CAUSAL_REASONING)
        for step in causal_steps:
            rationale_parts.append(step.content)

        # Look for decision steps - these explain choices
        decision_steps = chain.get_steps_by_type(ReasoningType.DECISION_MAKING)
        for step in decision_steps:
            rationale_parts.append(step.content)

        # If no structured rationale found, look for "because" clauses
        if not rationale_parts:
            because_pattern = r"because\s+([^.!?]+)"
            matches = re.findall(because_pattern, chain.raw_text, re.IGNORECASE)
            rationale_parts.extend(matches)

        # If still nothing, use goal-oriented steps
        if not rationale_parts:
            goal_steps = chain.get_steps_by_type(ReasoningType.GOAL_REASONING)
            for step in goal_steps:
                rationale_parts.append(step.content)

        if rationale_parts:
            # Combine and clean
            return " ".join(rationale_parts[:3])  # Limit to top 3 parts

        # Fallback: return the middle section of reasoning
        if chain.steps and len(chain.steps) > 2:
            mid_idx = len(chain.steps) // 2
            return chain.steps[mid_idx].content

        return ""

    def assess_reversibility(
        self,
        decision: str,
        context: Dict[str, Any],
    ) -> bool:
        """
        Assess if a decision is reversible.

        Analyzes the decision text and context to determine if the
        decision can be easily undone or changed.

        Args:
            decision: The decision statement.
            context: Context dictionary that may contain reversibility hints.

        Returns:
            True if the decision appears reversible, False otherwise.

        Example:
            >>> is_reversible = tracer.assess_reversibility(
            ...     decision="Delete the database",
            ...     context={"has_backup": True},
            ... )
        """
        # Check context for explicit reversibility indication
        if "reversible" in context:
            return bool(context["reversible"])

        # Patterns indicating irreversible actions
        irreversible_patterns = [
            r"\bdelete\b",
            r"\bremove permanently\b",
            r"\bdestroy\b",
            r"\bdrop\b",
            r"\bformat\b",
            r"\berase\b",
            r"\bterminate\b",
            r"\bshut down\b",
            r"\bpublish\b",
            r"\brelease\b",
            r"\bdeploy to production\b",
            r"\bsend\b",
            r"\bsubmit\b",
            r"\bfinalize\b",
            r"\bcommit\b",
            r"\bpush\b",
            r"\bmerge\b",
        ]

        decision_lower = decision.lower()

        for pattern in irreversible_patterns:
            if re.search(pattern, decision_lower):
                # Check for mitigation factors in context
                if context.get("has_backup"):
                    return True
                if context.get("can_undo"):
                    return True
                if context.get("is_test_environment"):
                    return True
                return False

        # By default, assume decisions are reversible
        return True

    def _estimate_decision_confidence(
        self,
        chain: ReasoningChain,
        response: str,
    ) -> float:
        """
        Estimate confidence in a decision based on reasoning.

        Analyzes the reasoning chain and response text to estimate
        how confident the decision-maker appears to be.

        Args:
            chain: The parsed reasoning chain.
            response: The full response text.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        confidence = chain.average_confidence

        # Boost confidence if there's strong rationale
        causal_steps = chain.get_steps_by_type(ReasoningType.CAUSAL_REASONING)
        if len(causal_steps) >= 2:
            confidence += 0.1

        # Boost confidence if alternatives were considered and rejected
        if "however" in response.lower() or "alternatively" in response.lower():
            confidence += 0.05

        # Reduce confidence if there's hedging language
        hedging_patterns = [
            r"\bperhaps\b",
            r"\bmaybe\b",
            r"\bmight\b",
            r"\bnot sure\b",
            r"\buncertain\b",
        ]
        for pattern in hedging_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                confidence -= 0.05

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def quick_trace(
        self,
        prompt: str,
        response: str,
        decision: str,
        model: Optional[str] = None,
    ) -> DecisionTrace:
        """
        Create a quick decision trace with minimal parsing.

        A faster alternative to trace_decision that performs less
        analysis but creates a valid trace more quickly.

        Args:
            prompt: The prompt that led to this decision.
            response: The AI response.
            decision: The decision made.
            model: Optional model identifier.

        Returns:
            A DecisionTrace with basic information.
        """
        return DecisionTrace(
            id=str(uuid.uuid4())[:8],
            decision=decision,
            timestamp=datetime.utcnow(),
            context={"prompt": prompt},
            confidence=0.5,
            reversible=True,
            metadata={"model": model, "response_preview": response[:200]},
        )


class _ActiveTrace:
    """Internal class to track active trace sessions."""

    def __init__(
        self,
        id: str,
        goal: str,
        decisions: List[DecisionTrace],
        context: Dict[str, Any],
        start_time: datetime,
    ):
        self.id = id
        self.goal = goal
        self.decisions = decisions
        self.context = context
        self.start_time = start_time
