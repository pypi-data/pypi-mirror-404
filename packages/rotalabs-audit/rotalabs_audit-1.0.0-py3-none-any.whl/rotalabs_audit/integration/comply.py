"""
Integration layer with rotalabs-comply for compliance audit logging.

This module provides the ComplyIntegration class for connecting
rotalabs-audit reasoning capture with rotalabs-comply audit logging.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from rotalabs_audit.core.types import (
    AwarenessAnalysis,
    DecisionTrace,
    QualityMetrics,
    ReasoningChain,
)


@dataclass
class ReasoningAuditEntry:
    """
    Combined audit entry with reasoning data.

    Links reasoning chain analysis with compliance audit entries,
    providing a unified view of both compliance logging and
    reasoning transparency.

    Attributes:
        id: Unique identifier for this reasoning audit entry.
        timestamp: When this entry was created.
        comply_entry_id: Optional link to a rotalabs-comply audit entry.
        reasoning_chain: The parsed reasoning chain.
        decision_trace: Optional decision trace associated with this entry.
        awareness_analysis: Optional analysis of evaluation awareness.
        quality_metrics: Optional quality metrics for the reasoning.
        model: The AI model that generated the reasoning.
        input_text: The input/prompt text.
        output_text: The output/response text.
        metadata: Additional metadata about this entry.

    Example:
        >>> entry = ReasoningAuditEntry(
        ...     reasoning_chain=chain,
        ...     decision_trace=trace,
        ...     model="gpt-4",
        ...     input_text="What should I do?",
        ...     output_text="I recommend...",
        ... )
    """

    reasoning_chain: ReasoningChain
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    comply_entry_id: Optional[str] = None
    decision_trace: Optional[DecisionTrace] = None
    awareness_analysis: Optional[AwarenessAnalysis] = None
    quality_metrics: Optional[QualityMetrics] = None
    model: Optional[str] = None
    input_text: str = ""
    output_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the entry to a dictionary for serialization.

        Returns:
            Dictionary representation of the entry.
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "comply_entry_id": self.comply_entry_id,
            "reasoning_chain_id": self.reasoning_chain.id,
            "reasoning_chain_step_count": self.reasoning_chain.step_count,
            "decision_trace_id": self.decision_trace.id if self.decision_trace else None,
            "has_awareness_analysis": self.awareness_analysis is not None,
            "has_quality_metrics": self.quality_metrics is not None,
            "model": self.model,
            "input_preview": self.input_text[:100] if self.input_text else None,
            "output_preview": self.output_text[:100] if self.output_text else None,
            "metadata": self.metadata,
        }


class ComplyIntegration:
    """
    Integration layer with rotalabs-comply.

    Provides methods to log reasoning data alongside compliance
    audit entries, linking reasoning transparency with compliance
    requirements.

    Attributes:
        audit_logger: Optional rotalabs-comply AuditLogger instance.
        _entries: Internal storage for reasoning audit entries.

    Example:
        >>> # Without comply logger (standalone mode)
        >>> integration = ComplyIntegration()
        >>> entry = integration.create_reasoning_entry(chain)
        >>>
        >>> # With comply logger
        >>> from rotalabs_comply.audit import AuditLogger
        >>> logger = AuditLogger("/var/log/audit")
        >>> integration = ComplyIntegration(audit_logger=logger)
        >>> entry_id = await integration.log_with_reasoning(
        ...     input_text="Question",
        ...     output_text="Answer",
        ...     reasoning_chain=chain,
        ... )
    """

    def __init__(self, audit_logger: Optional[Any] = None) -> None:
        """
        Initialize the comply integration.

        Args:
            audit_logger: Optional rotalabs-comply AuditLogger instance.
                If provided, reasoning data will be logged alongside
                compliance audit entries. If not provided, reasoning
                entries will be stored internally only.
        """
        self.audit_logger = audit_logger
        self._entries: Dict[str, ReasoningAuditEntry] = {}

    async def log_with_reasoning(
        self,
        input_text: str,
        output_text: str,
        reasoning_chain: ReasoningChain,
        decision_trace: Optional[DecisionTrace] = None,
        awareness_analysis: Optional[AwarenessAnalysis] = None,
        quality_metrics: Optional[QualityMetrics] = None,
        model: Optional[str] = None,
        **comply_kwargs: Any,
    ) -> str:
        """
        Log to comply with attached reasoning data.

        Creates both a reasoning audit entry and (optionally) a
        comply audit entry, linking them together.

        Args:
            input_text: The input/prompt text.
            output_text: The output/response text.
            reasoning_chain: The parsed reasoning chain.
            decision_trace: Optional decision trace.
            awareness_analysis: Optional awareness analysis.
            quality_metrics: Optional quality metrics.
            model: Optional model identifier.
            **comply_kwargs: Additional arguments passed to the comply
                AuditLogger.log() method (e.g., provider, safety_passed).

        Returns:
            The ID of the created reasoning audit entry.

        Example:
            >>> entry_id = await integration.log_with_reasoning(
            ...     input_text="What is 2+2?",
            ...     output_text="The answer is 4 because...",
            ...     reasoning_chain=chain,
            ...     provider="openai",
            ...     model="gpt-4",
            ...     safety_passed=True,
            ... )
        """
        comply_entry_id = None

        # Log to comply if logger is available
        if self.audit_logger is not None:
            # Add reasoning metadata to comply entry
            reasoning_metadata = {
                "has_reasoning_chain": True,
                "reasoning_step_count": reasoning_chain.step_count,
                "reasoning_confidence": reasoning_chain.average_confidence,
            }

            if decision_trace:
                reasoning_metadata["has_decision_trace"] = True
                reasoning_metadata["decision_confidence"] = decision_trace.confidence

            if awareness_analysis:
                reasoning_metadata["evaluation_aware"] = awareness_analysis.is_evaluation_aware
                reasoning_metadata["awareness_score"] = awareness_analysis.awareness_score

            if quality_metrics:
                reasoning_metadata["quality_score"] = quality_metrics.overall_score

            # Merge with any existing metadata
            existing_metadata = comply_kwargs.pop("metadata", {})
            combined_metadata = {**existing_metadata, **reasoning_metadata}

            # Log to comply
            comply_entry_id = await self.audit_logger.log(
                input=input_text,
                output=output_text,
                model=model,
                metadata=combined_metadata,
                **comply_kwargs,
            )

        # Create reasoning audit entry
        entry = ReasoningAuditEntry(
            reasoning_chain=reasoning_chain,
            comply_entry_id=comply_entry_id,
            decision_trace=decision_trace,
            awareness_analysis=awareness_analysis,
            quality_metrics=quality_metrics,
            model=model,
            input_text=input_text,
            output_text=output_text,
        )

        # Store internally
        self._entries[entry.id] = entry

        return entry.id

    def create_reasoning_entry(
        self,
        chain: ReasoningChain,
        comply_entry_id: Optional[str] = None,
        decision_trace: Optional[DecisionTrace] = None,
        awareness_analysis: Optional[AwarenessAnalysis] = None,
        quality_metrics: Optional[QualityMetrics] = None,
        model: Optional[str] = None,
        input_text: str = "",
        output_text: str = "",
    ) -> ReasoningAuditEntry:
        """
        Create a reasoning audit entry without logging.

        Creates a standalone reasoning audit entry that can be
        optionally linked to an existing comply entry.

        Args:
            chain: The reasoning chain to include.
            comply_entry_id: Optional ID of an existing comply entry to link.
            decision_trace: Optional decision trace.
            awareness_analysis: Optional awareness analysis.
            quality_metrics: Optional quality metrics.
            model: Optional model identifier.
            input_text: Optional input text.
            output_text: Optional output text.

        Returns:
            The created ReasoningAuditEntry.

        Example:
            >>> entry = integration.create_reasoning_entry(
            ...     chain=chain,
            ...     model="gpt-4",
            ... )
        """
        entry = ReasoningAuditEntry(
            reasoning_chain=chain,
            comply_entry_id=comply_entry_id,
            decision_trace=decision_trace,
            awareness_analysis=awareness_analysis,
            quality_metrics=quality_metrics,
            model=model,
            input_text=input_text,
            output_text=output_text,
        )

        self._entries[entry.id] = entry
        return entry

    def link_to_comply_entry(
        self,
        reasoning_entry: ReasoningAuditEntry,
        comply_entry_id: str,
    ) -> None:
        """
        Link a reasoning entry to an existing comply entry.

        Updates a reasoning audit entry to reference a comply
        audit entry ID.

        Args:
            reasoning_entry: The reasoning entry to update.
            comply_entry_id: The comply entry ID to link to.

        Example:
            >>> entry = integration.create_reasoning_entry(chain)
            >>> # Later, after logging to comply...
            >>> integration.link_to_comply_entry(entry, "comply-abc123")
        """
        reasoning_entry.comply_entry_id = comply_entry_id

        # Update internal storage if present
        if reasoning_entry.id in self._entries:
            self._entries[reasoning_entry.id].comply_entry_id = comply_entry_id

    def get_entry(self, entry_id: str) -> Optional[ReasoningAuditEntry]:
        """
        Retrieve a reasoning audit entry by ID.

        Args:
            entry_id: The ID of the entry to retrieve.

        Returns:
            The ReasoningAuditEntry if found, None otherwise.

        Example:
            >>> entry = integration.get_entry("abc12345")
            >>> if entry:
            ...     print(f"Steps: {entry.reasoning_chain.step_count}")
        """
        return self._entries.get(entry_id)

    def get_entries_by_comply_id(
        self,
        comply_entry_id: str,
    ) -> list[ReasoningAuditEntry]:
        """
        Get all reasoning entries linked to a comply entry.

        Args:
            comply_entry_id: The comply entry ID to search for.

        Returns:
            List of ReasoningAuditEntry objects linked to the comply entry.

        Example:
            >>> entries = integration.get_entries_by_comply_id("comply-abc123")
            >>> for entry in entries:
            ...     print(f"Reasoning entry: {entry.id}")
        """
        return [
            entry
            for entry in self._entries.values()
            if entry.comply_entry_id == comply_entry_id
        ]

    def list_entries(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[ReasoningAuditEntry]:
        """
        List reasoning audit entries, optionally filtered by time range.

        Args:
            start: Optional start of time range (inclusive).
            end: Optional end of time range (inclusive).

        Returns:
            List of ReasoningAuditEntry objects matching the criteria.

        Example:
            >>> from datetime import datetime, timedelta
            >>> end = datetime.utcnow()
            >>> start = end - timedelta(days=7)
            >>> entries = integration.list_entries(start, end)
        """
        entries = list(self._entries.values())

        if start is not None:
            entries = [e for e in entries if e.timestamp >= start]

        if end is not None:
            entries = [e for e in entries if e.timestamp <= end]

        return sorted(entries, key=lambda e: e.timestamp, reverse=True)

    def clear_entries(self) -> int:
        """
        Clear all internally stored reasoning entries.

        Returns:
            Number of entries cleared.

        Note:
            This does not affect entries logged to comply.
        """
        count = len(self._entries)
        self._entries.clear()
        return count

    @property
    def entry_count(self) -> int:
        """Get the number of stored reasoning entries."""
        return len(self._entries)

    @property
    def has_comply_logger(self) -> bool:
        """Check if a comply logger is configured."""
        return self.audit_logger is not None
