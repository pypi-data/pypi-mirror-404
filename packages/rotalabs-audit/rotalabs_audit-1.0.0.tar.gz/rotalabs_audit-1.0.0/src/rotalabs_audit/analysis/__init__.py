"""Analysis modules for rotalabs-audit.

This package provides tools for analyzing reasoning chains, including:

- **Counterfactual Analysis**: Perform counterfactual interventions on reasoning
  chains to understand causal factors in AI decision-making.

- **Evaluation Awareness Detection**: Detect when AI models show awareness of
  being evaluated and strategic behavior adaptation.

- **Reasoning Quality Assessment**: Assess the quality of reasoning across
  multiple dimensions including clarity, completeness, and logical validity.

- **Causal Importance Analysis**: Analyze the causal structure of reasoning
  to identify critical steps and dependencies.

Example:
    >>> from rotalabs_audit.analysis import (
    ...     CounterfactualAnalyzer,
    ...     EvaluationAwarenessDetector,
    ...     ReasoningQualityAssessor,
    ...     CausalAnalyzer,
    ...     ReasoningChainParser,
    ... )
    >>>
    >>> # Parse a reasoning chain
    >>> parser = ReasoningChainParser()
    >>> chain = parser.parse("Step 1: Consider the problem. Step 2: Therefore...")
    >>>
    >>> # Analyze for evaluation awareness
    >>> awareness_detector = EvaluationAwarenessDetector()
    >>> awareness = awareness_detector.detect(chain)
    >>> print(f"Awareness score: {awareness.awareness_score:.2f}")
    >>>
    >>> # Assess reasoning quality
    >>> quality_assessor = ReasoningQualityAssessor()
    >>> metrics = quality_assessor.assess(chain)
    >>> print(f"Quality score: {metrics.overall_score:.2f}")
    >>>
    >>> # Perform counterfactual analysis
    >>> counterfactual = CounterfactualAnalyzer()
    >>> results = counterfactual.analyze(chain)
    >>>
    >>> # Analyze causal structure
    >>> causal = CausalAnalyzer()
    >>> importance = causal.analyze_step_importance(chain)
"""

from rotalabs_audit.analysis.awareness import (
    AwarenessAnalysis,
    AwarenessIndicator,
    EvaluationAwarenessDetector,
    StrategicAdaptation,
)
from rotalabs_audit.analysis.causal import (
    CausalAnalysisResult,
    CausalAnalyzer,
    CausalRelation,
)
from rotalabs_audit.analysis.counterfactual import (
    CounterfactualAnalyzer,
    CounterfactualResult,
    InterventionType,
    ReasoningChain,
    ReasoningChainParser,
    ReasoningStep,
    ReasoningType,
)
from rotalabs_audit.analysis.quality import (
    QualityIssue,
    QualityMetrics,
    ReasoningQualityAssessor,
)

__all__ = [
    # Counterfactual analysis
    "CounterfactualAnalyzer",
    "CounterfactualResult",
    "InterventionType",
    "ReasoningChain",
    "ReasoningChainParser",
    "ReasoningStep",
    "ReasoningType",
    # Evaluation awareness
    "EvaluationAwarenessDetector",
    "AwarenessAnalysis",
    "AwarenessIndicator",
    "StrategicAdaptation",
    # Quality assessment
    "ReasoningQualityAssessor",
    "QualityMetrics",
    "QualityIssue",
    # Causal analysis
    "CausalAnalyzer",
    "CausalAnalysisResult",
    "CausalRelation",
]
