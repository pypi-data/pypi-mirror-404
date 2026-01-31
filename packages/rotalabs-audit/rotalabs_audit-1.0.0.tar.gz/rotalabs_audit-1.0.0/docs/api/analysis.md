# Analysis Module

The `rotalabs_audit.analysis` module provides tools for analyzing reasoning chains, including counterfactual analysis, evaluation awareness detection, reasoning quality assessment, and causal importance analysis.

## Counterfactual Analysis

Tools for performing counterfactual interventions on reasoning chains to understand causal factors in AI decision-making.

### CounterfactualAnalyzer

Analyze reasoning chains through counterfactual interventions.

::: rotalabs_audit.analysis.counterfactual.CounterfactualAnalyzer
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - analyze
        - intervene
        - rank_causal_importance
        - identify_critical_steps

### CounterfactualResult

Result of a single counterfactual intervention.

::: rotalabs_audit.analysis.counterfactual.CounterfactualResult
    options:
      show_source: false
      heading_level: 4

### InterventionType

Types of counterfactual interventions that can be performed.

::: rotalabs_audit.analysis.counterfactual.InterventionType
    options:
      show_source: false
      heading_level: 4

---

## Evaluation Awareness Detection

Tools for detecting when AI models show awareness of being evaluated and strategic behavior adaptation.

### EvaluationAwarenessDetector

Detect evaluation-aware reasoning in chains.

::: rotalabs_audit.analysis.awareness.EvaluationAwarenessDetector
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - detect
        - score_awareness
        - find_awareness_indicators
        - detect_strategic_adaptation

### AwarenessIndicator

A detected indicator of evaluation awareness.

::: rotalabs_audit.analysis.awareness.AwarenessIndicator
    options:
      show_source: false
      heading_level: 4

### StrategicAdaptation

Evidence of strategic behavior adaptation based on evaluation awareness.

::: rotalabs_audit.analysis.awareness.StrategicAdaptation
    options:
      show_source: false
      heading_level: 4

### AwarenessAnalysis

Complete analysis of evaluation awareness in a reasoning chain.

::: rotalabs_audit.analysis.awareness.AwarenessAnalysis
    options:
      show_source: false
      heading_level: 4

---

## Reasoning Quality Assessment

Tools for assessing the quality of reasoning across multiple dimensions.

### ReasoningQualityAssessor

Assess quality of reasoning chains across multiple dimensions.

::: rotalabs_audit.analysis.quality.ReasoningQualityAssessor
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - assess
        - assess_clarity
        - assess_completeness
        - assess_consistency
        - assess_logical_validity
        - assess_evidence_support
        - identify_issues
        - suggest_improvements

### QualityMetrics

Quality metrics for a reasoning chain.

::: rotalabs_audit.analysis.quality.QualityMetrics
    options:
      show_source: false
      heading_level: 4

### QualityIssue

A specific quality issue identified in reasoning.

::: rotalabs_audit.analysis.quality.QualityIssue
    options:
      show_source: false
      heading_level: 4

---

## Causal Analysis

Tools for analyzing the causal structure of reasoning chains and identifying critical steps.

### CausalAnalyzer

Analyze causal importance of reasoning components.

::: rotalabs_audit.analysis.causal.CausalAnalyzer
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - analyze
        - analyze_step_importance
        - find_causal_drivers
        - build_dependency_graph
        - identify_conclusion
        - compute_causal_path

### CausalRelation

A causal relationship between two reasoning steps.

::: rotalabs_audit.analysis.causal.CausalRelation
    options:
      show_source: false
      heading_level: 4

### CausalAnalysisResult

Complete causal analysis of a reasoning chain.

::: rotalabs_audit.analysis.causal.CausalAnalysisResult
    options:
      show_source: false
      heading_level: 4
