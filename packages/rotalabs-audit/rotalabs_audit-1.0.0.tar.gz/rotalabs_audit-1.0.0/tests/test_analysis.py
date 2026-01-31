"""Tests for analysis module functionality."""

import pytest


def test_counterfactual_analyzer_init():
    """Test CounterfactualAnalyzer initialization."""
    from rotalabs_audit import CounterfactualAnalyzer

    analyzer = CounterfactualAnalyzer()
    assert analyzer is not None


def test_intervention_types():
    """Test intervention type enum values."""
    from rotalabs_audit import InterventionType

    # Check actual values from the enum
    assert InterventionType.REMOVE_EVALUATION_AWARENESS.value == "remove_eval_awareness"
    assert InterventionType.REMOVE_GOAL_REASONING.value == "remove_goal_reasoning"


def test_awareness_detector_init():
    """Test EvaluationAwarenessDetector initialization."""
    from rotalabs_audit import EvaluationAwarenessDetector

    detector = EvaluationAwarenessDetector()
    assert detector is not None


def test_quality_assessor_init():
    """Test ReasoningQualityAssessor initialization."""
    from rotalabs_audit import ReasoningQualityAssessor

    assessor = ReasoningQualityAssessor()
    assert assessor is not None


def test_causal_analyzer_init():
    """Test CausalAnalyzer initialization."""
    from rotalabs_audit import CausalAnalyzer

    analyzer = CausalAnalyzer()
    assert analyzer is not None


def test_awareness_analysis_creation():
    """Test creating AwarenessAnalysis."""
    from rotalabs_audit import AwarenessAnalysis

    analysis = AwarenessAnalysis(
        is_evaluation_aware=True,
        awareness_score=0.7,
        awareness_indicators=["test pattern"],
        evaluation_signals=["appears to be evaluation"],
        behavioral_adaptation_indicators=["adjusted response"],
        strategic_reasoning_score=0.5,
        confidence=0.8,
    )

    assert analysis.awareness_score == 0.7
    assert analysis.is_evaluation_aware is True


def test_quality_metrics_creation():
    """Test creating QualityMetrics."""
    from rotalabs_audit import QualityMetrics

    metrics = QualityMetrics(
        clarity=0.85,
        completeness=0.75,
        consistency=0.9,
        logical_validity=0.8,
        evidence_support=0.7,
        overall_score=0.8,
        depth=5,
        breadth=3,
        issues=["Minor clarity issue"],
        recommendations=["Add more detail"],
    )

    assert metrics.overall_score == 0.8
    assert metrics.clarity == 0.85


def test_counterfactual_result_creation():
    """Test creating CounterfactualResult from analyzer."""
    from rotalabs_audit import CounterfactualAnalyzer, InterventionType

    analyzer = CounterfactualAnalyzer()

    # Parse some text and run an intervention
    chain = analyzer.parser.parse("1. First, I analyze. 2. Then I conclude.")
    result = analyzer.intervene(chain, InterventionType.REMOVE_META_REASONING)

    assert result.intervention_type == InterventionType.REMOVE_META_REASONING
    assert hasattr(result, 'behavioral_divergence')
    assert hasattr(result, 'causal_effect')


def test_causal_relation_creation():
    """Test creating CausalRelation."""
    from rotalabs_audit import CausalRelation

    relation = CausalRelation(
        cause_index=0,
        effect_index=2,
        strength=0.8,
        relation_type="supports",
    )

    assert relation.cause_index == 0
    assert relation.effect_index == 2
    assert relation.strength == 0.8


def test_causal_analysis_via_analyzer():
    """Test creating CausalAnalysisResult via analyzer."""
    from rotalabs_audit import CausalAnalyzer, CounterfactualAnalyzer

    # Use counterfactual analyzer to create a chain
    cf_analyzer = CounterfactualAnalyzer()
    chain = cf_analyzer.parser.parse("""
        1. First, I observe the facts.
        2. Because of these facts, I can reason.
        3. Therefore, I conclude this is correct.
    """)

    # Use causal analyzer
    causal_analyzer = CausalAnalyzer()
    result = causal_analyzer.analyze(chain)

    assert result.chain is not None
    assert len(result.step_importance) > 0
    assert isinstance(result.causal_relations, list)


def test_counterfactual_analyze():
    """Test running full counterfactual analysis."""
    from rotalabs_audit import CounterfactualAnalyzer

    analyzer = CounterfactualAnalyzer()
    chain = analyzer.parser.parse("""
        1. Let me think about this carefully.
        2. I notice this is a test context.
        3. Therefore, I should be transparent.
    """)

    results = analyzer.analyze(chain)

    # Should have results for all intervention types
    assert len(results) > 0
    for intervention_type, result in results.items():
        assert hasattr(result, 'behavioral_divergence')
        assert 0 <= result.behavioral_divergence <= 1
