"""
Custom exceptions for rotalabs-audit.

This module defines the exception hierarchy used throughout the rotalabs-audit
package for handling errors in reasoning chain parsing, analysis, tracing,
and integrations.
"""

from typing import Any, Dict, List, Optional


class AuditError(Exception):
    """
    Base exception for all rotalabs-audit errors.

    All exceptions raised by this package inherit from AuditError,
    allowing callers to catch all audit-related errors with a single
    except clause if desired.

    Attributes:
        message: Human-readable error description.
        details: Optional dictionary of additional error context.
        cause: Optional underlying exception that caused this error.

    Example:
        >>> try:
        ...     raise AuditError("Something went wrong", details={"code": 42})
        ... except AuditError as e:
        ...     print(f"Error: {e.message}, Details: {e.details}")
        Error: Something went wrong, Details: {'code': 42}
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize an AuditError.

        Args:
            message: Human-readable error description.
            details: Optional dictionary of additional error context.
            cause: Optional underlying exception that caused this error.
        """
        self.message = message
        self.details = details or {}
        self.cause = cause

        # Build the full message
        full_message = message
        if details:
            full_message += f" (details: {details})"
        if cause:
            full_message += f" [caused by: {type(cause).__name__}: {cause}]"

        super().__init__(full_message)

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"details={self.details!r}, "
            f"cause={self.cause!r})"
        )


class ParsingError(AuditError):
    """
    Exception raised when parsing reasoning chains fails.

    This exception is raised when the parser encounters problems
    extracting structured reasoning steps from raw model output,
    such as malformed input, unrecognized patterns, or timeout.

    Attributes:
        message: Human-readable error description.
        raw_text: The original text that failed to parse.
        partial_steps: Any steps that were successfully parsed before failure.
        position: Character position in raw_text where parsing failed.
        details: Additional error context.
        cause: Underlying exception if applicable.

    Example:
        >>> try:
        ...     raise ParsingError(
        ...         "Unexpected token",
        ...         raw_text="malformed input...",
        ...         position=15
        ...     )
        ... except ParsingError as e:
        ...     print(f"Parsing failed at position {e.position}")
    """

    def __init__(
        self,
        message: str,
        raw_text: Optional[str] = None,
        partial_steps: Optional[List[Any]] = None,
        position: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize a ParsingError.

        Args:
            message: Human-readable error description.
            raw_text: The original text that failed to parse.
            partial_steps: Any steps successfully parsed before failure.
            position: Character position where parsing failed.
            details: Additional error context.
            cause: Underlying exception if applicable.
        """
        self.raw_text = raw_text
        self.partial_steps = partial_steps or []
        self.position = position

        # Add parsing-specific details
        full_details = details or {}
        if position is not None:
            full_details["position"] = position
        if partial_steps:
            full_details["partial_step_count"] = len(partial_steps)
        if raw_text:
            # Include a snippet around the error position
            if position is not None:
                start = max(0, position - 20)
                end = min(len(raw_text), position + 20)
                full_details["context_snippet"] = raw_text[start:end]
            full_details["input_length"] = len(raw_text)

        super().__init__(message, details=full_details, cause=cause)


class AnalysisError(AuditError):
    """
    Exception raised when reasoning analysis fails.

    This exception is raised when analyzing a reasoning chain encounters
    problems, such as invalid chain structure, analysis timeout, or
    failures in quality assessment or awareness detection.

    Attributes:
        message: Human-readable error description.
        chain_id: Identifier of the chain being analyzed.
        analysis_type: Type of analysis that failed (e.g., "quality", "awareness").
        partial_results: Any results computed before failure.
        details: Additional error context.
        cause: Underlying exception if applicable.

    Example:
        >>> try:
        ...     raise AnalysisError(
        ...         "Quality assessment timed out",
        ...         chain_id="chain-123",
        ...         analysis_type="quality"
        ...     )
        ... except AnalysisError as e:
        ...     print(f"Analysis '{e.analysis_type}' failed for {e.chain_id}")
    """

    def __init__(
        self,
        message: str,
        chain_id: Optional[str] = None,
        analysis_type: Optional[str] = None,
        partial_results: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize an AnalysisError.

        Args:
            message: Human-readable error description.
            chain_id: Identifier of the chain being analyzed.
            analysis_type: Type of analysis that failed.
            partial_results: Any results computed before failure.
            details: Additional error context.
            cause: Underlying exception if applicable.
        """
        self.chain_id = chain_id
        self.analysis_type = analysis_type
        self.partial_results = partial_results or {}

        # Add analysis-specific details
        full_details = details or {}
        if chain_id:
            full_details["chain_id"] = chain_id
        if analysis_type:
            full_details["analysis_type"] = analysis_type
        if partial_results:
            full_details["partial_result_keys"] = list(partial_results.keys())

        super().__init__(message, details=full_details, cause=cause)


class TracingError(AuditError):
    """
    Exception raised when decision tracing fails.

    This exception is raised when capturing, storing, or retrieving
    decision traces encounters problems, such as persistence failures,
    depth limit exceeded, or invalid trace structure.

    Attributes:
        message: Human-readable error description.
        trace_id: Identifier of the trace involved.
        operation: The operation that failed (e.g., "capture", "store", "retrieve").
        depth: Current trace depth when error occurred.
        details: Additional error context.
        cause: Underlying exception if applicable.

    Example:
        >>> try:
        ...     raise TracingError(
        ...         "Maximum trace depth exceeded",
        ...         trace_id="trace-456",
        ...         operation="capture",
        ...         depth=25
        ...     )
        ... except TracingError as e:
        ...     print(f"Tracing failed during {e.operation} at depth {e.depth}")
    """

    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        operation: Optional[str] = None,
        depth: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize a TracingError.

        Args:
            message: Human-readable error description.
            trace_id: Identifier of the trace involved.
            operation: The operation that failed.
            depth: Current trace depth when error occurred.
            details: Additional error context.
            cause: Underlying exception if applicable.
        """
        self.trace_id = trace_id
        self.operation = operation
        self.depth = depth

        # Add tracing-specific details
        full_details = details or {}
        if trace_id:
            full_details["trace_id"] = trace_id
        if operation:
            full_details["operation"] = operation
        if depth is not None:
            full_details["depth"] = depth

        super().__init__(message, details=full_details, cause=cause)


class IntegrationError(AuditError):
    """
    Exception raised when integration with external systems fails.

    This exception is raised when interacting with external components
    like LLM APIs, databases, or other rotalabs packages encounters
    problems.

    Attributes:
        message: Human-readable error description.
        integration_name: Name of the integration that failed.
        endpoint: API endpoint or connection string involved.
        request_data: Data that was being sent (sanitized).
        response_data: Any response received before failure.
        status_code: HTTP status code if applicable.
        details: Additional error context.
        cause: Underlying exception if applicable.

    Example:
        >>> try:
        ...     raise IntegrationError(
        ...         "API request failed",
        ...         integration_name="openai",
        ...         endpoint="https://api.openai.com/v1/chat",
        ...         status_code=429
        ...     )
        ... except IntegrationError as e:
        ...     print(f"Integration '{e.integration_name}' failed: {e.status_code}")
    """

    def __init__(
        self,
        message: str,
        integration_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize an IntegrationError.

        Args:
            message: Human-readable error description.
            integration_name: Name of the integration that failed.
            endpoint: API endpoint or connection string involved.
            request_data: Data that was being sent (should be sanitized).
            response_data: Any response received before failure.
            status_code: HTTP status code if applicable.
            details: Additional error context.
            cause: Underlying exception if applicable.
        """
        self.integration_name = integration_name
        self.endpoint = endpoint
        self.request_data = request_data or {}
        self.response_data = response_data or {}
        self.status_code = status_code

        # Add integration-specific details
        full_details = details or {}
        if integration_name:
            full_details["integration_name"] = integration_name
        if endpoint:
            full_details["endpoint"] = endpoint
        if status_code is not None:
            full_details["status_code"] = status_code

        super().__init__(message, details=full_details, cause=cause)

    @property
    def is_rate_limited(self) -> bool:
        """Check if this error indicates rate limiting (HTTP 429)."""
        return self.status_code == 429

    @property
    def is_auth_error(self) -> bool:
        """Check if this error indicates authentication failure (HTTP 401/403)."""
        return self.status_code in (401, 403)

    @property
    def is_server_error(self) -> bool:
        """Check if this error indicates a server-side failure (HTTP 5xx)."""
        return self.status_code is not None and 500 <= self.status_code < 600


class ValidationError(AuditError):
    """
    Exception raised when input validation fails.

    This exception is raised when input data doesn't meet expected
    constraints, such as invalid configuration values, malformed
    data structures, or out-of-range parameters.

    Attributes:
        message: Human-readable error description.
        field_name: Name of the field that failed validation.
        expected: Description of expected value/format.
        actual: The actual value that was provided.
        details: Additional error context.
        cause: Underlying exception if applicable.

    Example:
        >>> try:
        ...     raise ValidationError(
        ...         "Confidence out of range",
        ...         field_name="confidence",
        ...         expected="0.0 to 1.0",
        ...         actual=1.5
        ...     )
        ... except ValidationError as e:
        ...     print(f"Field '{e.field_name}': expected {e.expected}, got {e.actual}")
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize a ValidationError.

        Args:
            message: Human-readable error description.
            field_name: Name of the field that failed validation.
            expected: Description of expected value/format.
            actual: The actual value that was provided.
            details: Additional error context.
            cause: Underlying exception if applicable.
        """
        self.field_name = field_name
        self.expected = expected
        self.actual = actual

        # Add validation-specific details
        full_details = details or {}
        if field_name:
            full_details["field_name"] = field_name
        if expected:
            full_details["expected"] = expected
        if actual is not None:
            full_details["actual"] = repr(actual)
            full_details["actual_type"] = type(actual).__name__

        super().__init__(message, details=full_details, cause=cause)


class TimeoutError(AuditError):
    """
    Exception raised when an operation times out.

    This exception is raised when parsing, analysis, or other operations
    exceed their configured time limits.

    Attributes:
        message: Human-readable error description.
        operation: The operation that timed out.
        timeout_seconds: The timeout limit that was exceeded.
        elapsed_seconds: How long the operation ran before timeout.
        details: Additional error context.
        cause: Underlying exception if applicable.

    Example:
        >>> try:
        ...     raise TimeoutError(
        ...         "Parsing timed out",
        ...         operation="parse_chain",
        ...         timeout_seconds=30.0,
        ...         elapsed_seconds=30.5
        ...     )
        ... except TimeoutError as e:
        ...     print(f"Operation '{e.operation}' exceeded {e.timeout_seconds}s limit")
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        elapsed_seconds: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize a TimeoutError.

        Args:
            message: Human-readable error description.
            operation: The operation that timed out.
            timeout_seconds: The timeout limit that was exceeded.
            elapsed_seconds: How long the operation ran before timeout.
            details: Additional error context.
            cause: Underlying exception if applicable.
        """
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.elapsed_seconds = elapsed_seconds

        # Add timeout-specific details
        full_details = details or {}
        if operation:
            full_details["operation"] = operation
        if timeout_seconds is not None:
            full_details["timeout_seconds"] = timeout_seconds
        if elapsed_seconds is not None:
            full_details["elapsed_seconds"] = elapsed_seconds

        super().__init__(message, details=full_details, cause=cause)
