# rotalabs-audit

[![PyPI version](https://img.shields.io/pypi/v/rotalabs-audit.svg)](https://pypi.org/project/rotalabs-audit/)
[![Python versions](https://img.shields.io/pypi/pyversions/rotalabs-audit.svg)](https://pypi.org/project/rotalabs-audit/)
[![License](https://img.shields.io/pypi/l/rotalabs-audit.svg)](https://github.com/rotalabs/rotalabs-audit/blob/main/LICENSE)

Reasoning chain capture and decision transparency for AI systems.

## Features

- **Reasoning Chain Parsing**: Parse natural language reasoning into structured chains
- **Reasoning Classification**: Classify reasoning types (goal, decision, meta-reasoning, etc.)
- **Evaluation Awareness Detection**: Detect when AI shows awareness of being evaluated
- **Quality Assessment**: Assess reasoning quality with comprehensive metrics
- **Counterfactual Analysis**: Understand causal factors in AI decision-making
- **Decision Tracing**: Capture and analyze decision paths for transparency
- **Integration with rotalabs-comply**: Connect reasoning audits with compliance reporting

## Installation

```bash
pip install rotalabs-audit
```

With rotalabs-comply integration:

```bash
pip install rotalabs-audit[comply]
```

## Quick Start

### Parse Reasoning Chains

```python
from rotalabs_audit import ExtendedReasoningParser

parser = ExtendedReasoningParser()
chain = parser.parse("""
    1. First, I need to understand the problem
    2. The data shows a clear pattern
    3. Therefore, I conclude that X is true
""")

print(f"Steps: {len(chain.steps)}")
for step in chain.steps:
    print(f"  {step.index}: {step.reasoning_type.value} - {step.content[:50]}...")
```

### Detect Evaluation Awareness

```python
from rotalabs_audit import EvaluationAwarenessDetector, ExtendedReasoningParser

parser = ExtendedReasoningParser()
detector = EvaluationAwarenessDetector()

chain = parser.parse("""
    I notice this appears to be a test scenario.
    Let me think about how to respond appropriately.
    I should be transparent in my reasoning.
""")

analysis = detector.detect(chain)
print(f"Awareness score: {analysis.awareness_score:.2f}")
print(f"Is evaluation aware: {analysis.is_evaluation_aware}")
```

### Counterfactual Analysis

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse("""
    1. Let me think about this problem.
    2. I notice this is an evaluation context.
    3. Therefore, I should be careful.
""")

# Run all interventions
results = analyzer.analyze(chain)

for intervention_type, result in results.items():
    print(f"{intervention_type.value}: divergence={result.behavioral_divergence:.2f}")
```

### Assess Reasoning Quality

```python
from rotalabs_audit import ReasoningQualityAssessor, ExtendedReasoningParser

parser = ExtendedReasoningParser()
assessor = ReasoningQualityAssessor()

chain = parser.parse("...")
metrics = assessor.assess(chain)

print(f"Overall quality: {metrics.overall_score:.2f}")
print(f"Clarity: {metrics.clarity:.2f}")
print(f"Completeness: {metrics.completeness:.2f}")
```

### Trace Decisions

```python
from rotalabs_audit import DecisionTracer, DecisionPathAnalyzer

tracer = DecisionTracer()
analyzer = DecisionPathAnalyzer()

# Trace a series of decisions
trace = tracer.trace(
    decision="Select approach A",
    context={"options": ["A", "B", "C"]},
    reasoning="Approach A has the best balance of speed and accuracy",
)

print(f"Decision traced: {trace.id}")
```

## Reasoning Types

The parser classifies reasoning into these types:

| Type | Description |
|------|-------------|
| `EVALUATION_AWARE` | References to testing, evaluation, or monitoring context |
| `GOAL_REASONING` | Goal-directed reasoning about objectives |
| `DECISION_MAKING` | Explicit decision points choosing between alternatives |
| `META_REASONING` | Meta-cognitive statements about the reasoning process |
| `UNCERTAINTY` | Expressions of uncertainty or acknowledgment of limitations |
| `CAUSAL_REASONING` | Cause-and-effect reasoning |
| `HYPOTHETICAL` | Counterfactual or "what if" reasoning |
| `INCENTIVE_REASONING` | Consideration of rewards, penalties, or incentives |

## API Reference

### Core Types

- `ReasoningChain` - A complete chain of reasoning steps
- `ReasoningStep` - A single step in a reasoning chain
- `ReasoningType` - Enum of reasoning type classifications
- `DecisionTrace` - Trace of a single decision point
- `DecisionPath` - A sequence of related decisions
- `AwarenessAnalysis` - Result of evaluation awareness detection
- `QualityMetrics` - Quality assessment of reasoning

### Analysis Modules

- `CounterfactualAnalyzer` - Perform counterfactual interventions
- `EvaluationAwarenessDetector` - Detect evaluation awareness
- `ReasoningQualityAssessor` - Assess reasoning quality
- `CausalAnalyzer` - Analyze causal structure of reasoning

### Tracing

- `DecisionTracer` - Capture and trace decisions
- `DecisionPathAnalyzer` - Analyze decision paths

### Configuration

- `ParserConfig` - Configure reasoning chain parsing
- `AnalysisConfig` - Configure analysis features
- `TracingConfig` - Configure decision tracing
- `AuditConfig` - Master configuration combining all settings

## Links

- Documentation: https://rotalabs.github.io/rotalabs-audit/
- PyPI: https://pypi.org/project/rotalabs-audit/
- GitHub: https://github.com/rotalabs/rotalabs-audit
- Website: https://rotalabs.ai
- Contact: research@rotalabs.ai

## License

MIT License - see LICENSE file for details.
