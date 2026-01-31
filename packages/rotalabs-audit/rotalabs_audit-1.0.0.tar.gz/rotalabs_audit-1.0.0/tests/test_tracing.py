"""Tests for tracing module functionality."""

import pytest
from datetime import datetime


def test_decision_tracer_init():
    """Test DecisionTracer initialization."""
    from rotalabs_audit import DecisionTracer

    tracer = DecisionTracer()
    assert tracer is not None


def test_decision_path_analyzer_init():
    """Test DecisionPathAnalyzer initialization."""
    from rotalabs_audit import DecisionPathAnalyzer

    analyzer = DecisionPathAnalyzer()
    assert analyzer is not None


def test_decision_trace_creation():
    """Test creating DecisionTrace from core types."""
    from rotalabs_audit import DecisionTrace

    trace = DecisionTrace(
        id="test-trace-001",
        decision="Choose option A",
        timestamp=datetime.utcnow(),
        context={"user": "test"},
        rationale="Option A is better because...",
        confidence=0.95,
    )

    assert trace.id == "test-trace-001"
    assert trace.decision == "Choose option A"
    assert trace.confidence == 0.95


def test_decision_path_creation():
    """Test creating DecisionPath."""
    from rotalabs_audit import DecisionPath, DecisionTrace

    decisions = [
        DecisionTrace(
            id="d1",
            decision="First decision",
            timestamp=datetime.utcnow(),
            context={},
            confidence=0.8,
        ),
        DecisionTrace(
            id="d2",
            decision="Second decision",
            timestamp=datetime.utcnow(),
            context={},
            confidence=0.9,
        ),
    ]

    path = DecisionPath(
        id="path-001",
        decisions=decisions,
        goal="Complete the task",
        success=True,
    )

    assert path.id == "path-001"
    assert path.length == 2
    assert path.success is True


def test_tracing_config_creation():
    """Test creating TracingConfig."""
    from rotalabs_audit import TracingConfig

    config = TracingConfig(
        capture_alternatives=True,
        max_trace_depth=15,
        include_reasoning_chain=True,
    )

    assert config.capture_alternatives is True
    assert config.max_trace_depth == 15
    assert config.include_reasoning_chain is True
