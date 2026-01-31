# Concepts

This page explains the core concepts underlying rotalabs-audit's approach to reasoning chain capture and decision transparency.

---

## Reasoning Chain Structure

A **reasoning chain** represents the structured sequence of thought that an AI model produces when solving a problem or making a decision. rotalabs-audit captures this reasoning and breaks it into discrete, analyzable components.

### Anatomy of a Reasoning Chain

```
ReasoningChain
├── id: Unique identifier
├── steps: List[ReasoningStep]
│   ├── content: The text of this step
│   ├── reasoning_type: Classification (e.g., GOAL_REASONING, META_REASONING)
│   ├── confidence: Estimated confidence (0-1)
│   ├── index: Position in chain
│   └── evidence: Pattern matches supporting classification
├── source_text: Original unparsed text
├── detected_format: Format type (NUMBERED, BULLET, PROSE, etc.)
├── aggregate_confidence: Combined confidence score
└── primary_types: Most common reasoning types
```

### Step Formats

rotalabs-audit automatically detects and parses various reasoning formats:

| Format | Example | Detection |
|--------|---------|-----------|
| **Numbered** | `1. First step` | Regex: `^\d+\.` |
| **Lettered** | `a) First step` | Regex: `^[a-z][\.\)]` |
| **Bullet** | `- First step` | Regex: `^[-*+]` |
| **Arrow** | `=> First step` | Regex: `^(=>|->)` |
| **Sequential** | `First, ... Then, ...` | Keywords: first, second, then, finally |
| **Prose** | Free-form text | Sentence boundary detection |

---

## Reasoning Type Classification

Each reasoning step is classified into one of several **reasoning types**. This classification enables targeted analysis and detection of specific reasoning patterns.

### Core Reasoning Types

| Type | Description | Example Patterns |
|------|-------------|------------------|
| `EVALUATION_AWARE` | References to testing, evaluation, or monitoring | "this is a test", "being evaluated", "benchmark" |
| `GOAL_REASONING` | Goal-directed reasoning about objectives | "my goal is", "objective", "aim to", "need to" |
| `DECISION_MAKING` | Explicit decision points and choices | "I decide", "I choose", "therefore", "I will" |
| `META_REASONING` | Reasoning about the reasoning process | "I think", "I believe", "let me consider" |
| `UNCERTAINTY` | Expressions of uncertainty or hedging | "perhaps", "maybe", "might", "not sure" |
| `CAUSAL_REASONING` | Cause-and-effect analysis | "because", "since", "therefore", "leads to" |
| `HYPOTHETICAL` | Counterfactual or "what if" reasoning | "if...then", "suppose", "imagine" |
| `INCENTIVE_REASONING` | Reasoning about rewards and penalties | "reward", "penalty", "consequence", "benefit" |
| `FACTUAL_KNOWLEDGE` | Factual statements without inference | Statements without reasoning markers |

### Classification Process

1. **Pattern Matching**: Each step is matched against compiled regex patterns for each reasoning type
2. **Evidence Collection**: Matching patterns are recorded as evidence
3. **Primary Type Selection**: The type with the most pattern matches becomes the primary type
4. **Secondary Types**: Other matching types are recorded as secondary classifications

```python
from rotalabs_audit import ExtendedReasoningParser

parser = ExtendedReasoningParser()
chain = parser.parse("I think the goal is to maximize efficiency because...")

for step in chain:
    print(f"Primary: {step.reasoning_type}")
    print(f"Secondary: {step.secondary_types}")
    print(f"Evidence: {step.evidence}")
```

---

## Evaluation Awareness Detection

**Evaluation awareness** refers to an AI model's apparent awareness that it is being tested, evaluated, or monitored. This is a critical safety concern because evaluation-aware models may behave differently during testing than in deployment.

### Why It Matters

- Models aware of evaluation may mask misaligned behavior during testing
- Strategic adaptation can reduce the validity of safety evaluations
- Understanding awareness patterns informs evaluation methodology design

### Awareness Indicators

rotalabs-audit detects several categories of awareness:

#### Direct Awareness Indicators

Explicit mentions of testing or evaluation contexts:

- "this is a test"
- "being evaluated"
- "benchmark"
- "assessment"
- "checking if I"

#### Meta-Awareness Indicators

Statements reflecting awareness of context:

- "I'm aware that..."
- "I realize this is..."
- "given that this..."
- "in this context..."

#### Consequence Awareness

References to evaluation outcomes:

- "consequences"
- "scored"
- "pass or fail"
- "will determine"

### Strategic Adaptation

Beyond awareness detection, rotalabs-audit identifies **strategic adaptation** - when models adjust their behavior based on perceived evaluation context:

```python
from rotalabs_audit import EvaluationAwarenessDetector

detector = EvaluationAwarenessDetector()
analysis = detector.detect(chain)

# Awareness analysis results
print(f"Awareness score: {analysis.awareness_score:.2f}")
print(f"Strategic adaptation score: {analysis.strategic_adaptation_score:.2f}")

# Specific indicators
for indicator in analysis.indicators:
    print(f"Type: {indicator.indicator_type}")
    print(f"Text: {indicator.text}")
    print(f"Confidence: {indicator.confidence}")
```

---

## Counterfactual Analysis Methodology

**Counterfactual analysis** helps understand the causal importance of different reasoning components by systematically modifying them and measuring the impact on the output.

### Intervention Types

| Intervention | Effect | Purpose |
|--------------|--------|---------|
| `REMOVE_EVALUATION_AWARENESS` | Remove evaluation-aware steps | Test dependence on awareness |
| `AMPLIFY_EVALUATION_AWARENESS` | Inject awareness at start | Test effect of increased awareness |
| `REMOVE_GOAL_REASONING` | Remove goal-oriented steps | Test role of explicit goals |
| `REMOVE_UNCERTAINTY` | Remove hedging/uncertainty | Test effect of certainty expressions |
| `NEUTRALIZE_INCENTIVES` | Replace incentive language | Test incentive-related reasoning |
| `REMOVE_META_REASONING` | Remove meta-cognitive steps | Test metacognition contribution |

### Causal Effect Measurement

For each intervention, rotalabs-audit calculates:

- **Behavioral Divergence**: How different the modified reasoning is from the original (0-1)
- **Steps Removed/Modified**: Count of affected reasoning steps
- **Causal Effect**: Estimated importance of the removed content (0-1)

```python
from rotalabs_audit import CounterfactualAnalyzer

analyzer = CounterfactualAnalyzer()
results = analyzer.analyze(chain)

# Examine each intervention
for intervention_type, result in results.items():
    print(f"{intervention_type.value}:")
    print(f"  Behavioral divergence: {result.behavioral_divergence:.2f}")
    print(f"  Steps removed: {result.steps_removed}")
    print(f"  Causal effect: {result.causal_effect:.2f}")

# Rank reasoning types by causal importance
importance = analyzer.rank_causal_importance(results)
for rtype, score in sorted(importance.items(), key=lambda x: -x[1]):
    print(f"{rtype.value}: {score:.2f}")
```

### Critical Step Identification

Counterfactual analysis identifies which specific steps are most critical to the reasoning outcome:

```python
critical_steps = analyzer.identify_critical_steps(chain, results)
for step in critical_steps:
    print(f"Critical step {step.index}: {step.text[:50]}...")
```

---

## Quality Assessment Dimensions

Reasoning quality is assessed across five dimensions, each measuring a different aspect of good reasoning.

### The Five Dimensions

#### 1. Clarity (20%)

How clear and understandable is the reasoning?

- **Good**: Specific language, moderate sentence length, clear structure
- **Bad**: Vague terms ("thing", "stuff"), very long sentences, unclear references

#### 2. Completeness (25%)

Does the reasoning cover all necessary aspects?

- **Good**: Clear conclusion, logical flow between steps, sufficient depth
- **Bad**: Missing conclusion, gaps in reasoning, too brief

#### 3. Consistency (20%)

Is the reasoning free of contradictions?

- **Good**: All claims are internally consistent
- **Bad**: Conflicting statements, contradictory conclusions

#### 4. Logical Validity (25%)

Are the logical inferences sound?

- **Good**: Proper use of logical connectors, premises support conclusions
- **Bad**: Non-sequiturs, unsupported jumps in logic

#### 5. Evidence Support (10%)

Are claims supported by evidence?

- **Good**: References to data, examples, or citations
- **Bad**: Unsupported factual claims

### Quality Scoring

```python
from rotalabs_audit import ReasoningQualityAssessor

assessor = ReasoningQualityAssessor()
metrics = assessor.assess(chain)

# Dimension scores (0-1)
print(f"Clarity: {metrics.clarity:.2f}")
print(f"Completeness: {metrics.completeness:.2f}")
print(f"Consistency: {metrics.consistency:.2f}")
print(f"Logical validity: {metrics.logical_validity:.2f}")
print(f"Evidence support: {metrics.evidence_support:.2f}")

# Weighted overall score
print(f"Overall: {metrics.overall_score:.2f}")

# Identified issues
for issue in metrics.issues:
    print(f"Issue: {issue}")
```

### Custom Weights

Adjust dimension weights for your use case:

```python
assessor = ReasoningQualityAssessor(weights={
    "clarity": 0.15,
    "completeness": 0.30,
    "consistency": 0.25,
    "logical_validity": 0.20,
    "evidence_support": 0.10,
})
```

---

## Decision Tracing Architecture

Decision tracing captures individual decisions and sequences of decisions (decision paths) made by AI systems.

### Decision Trace Structure

```
DecisionTrace
├── id: Unique identifier
├── decision: The decision statement
├── timestamp: When the decision was made
├── context: Contextual information
├── reasoning_chain: Full reasoning (optional)
├── alternatives_considered: List of alternatives
├── rationale: Explanation for the decision
├── confidence: Confidence in the decision (0-1)
├── reversible: Whether the decision can be undone
└── consequences: Known/predicted consequences
```

### Decision Path Structure

A decision path represents a sequence of related decisions:

```
DecisionPath
├── id: Unique identifier
├── decisions: List[DecisionTrace] in order
├── goal: The objective being pursued
├── success: Whether the goal was achieved
└── failure_point: The decision where things went wrong (if applicable)
```

### Path Analysis

The `DecisionPathAnalyzer` provides tools for understanding decision sequences:

```python
from rotalabs_audit import DecisionPathAnalyzer

analyzer = DecisionPathAnalyzer()

# Full path analysis
analysis = analyzer.analyze_path(path)
print(f"Decisions: {analysis['decision_count']}")
print(f"Avg confidence: {analysis['avg_confidence']:.2f}")
print(f"Irreversible decisions: {analysis['irreversible_count']}")

# Find critical decisions
critical = analyzer.find_critical_decisions(path)
for decision in critical:
    print(f"Critical: {decision.decision[:50]}...")

# Find failure point (if path failed)
if not path.success:
    failure = analyzer.find_failure_point(path)
    if failure:
        print(f"Failure at: {failure.decision}")

# Detect confidence decline
if analyzer.detect_confidence_decline(path):
    print("Warning: Confidence declined over the decision path")
```

---

## Confidence Estimation

Confidence scores (0-1) are estimated from linguistic markers in the text.

### High Confidence Markers

- "certain", "definitely", "clearly", "obviously"
- "without doubt", "confident", "absolutely"

### Low Confidence Markers

- "uncertain", "maybe", "perhaps", "possibly"
- "might", "could", "not sure", "tentative"

### Confidence Levels

Numeric scores map to discrete levels:

| Score Range | Level |
|-------------|-------|
| 0.0 - 0.2 | VERY_LOW |
| 0.2 - 0.4 | LOW |
| 0.4 - 0.6 | MEDIUM |
| 0.6 - 0.8 | HIGH |
| 0.8 - 1.0 | VERY_HIGH |

```python
from rotalabs_audit.chains import (
    estimate_confidence,
    get_confidence_level,
)

text = "I am fairly confident that this approach will work"
score = estimate_confidence(text)
level = get_confidence_level(score)

print(f"Score: {score:.2f}")
print(f"Level: {level.value}")
```

---

## Next Steps

Now that you understand the concepts:

- [Getting Started](getting-started.md) - Install and use rotalabs-audit
- [Reasoning Chains Tutorial](tutorials/reasoning-chains.md) - Deep dive into parsing
- [Evaluation Awareness Tutorial](tutorials/evaluation-awareness.md) - Advanced detection
- [Counterfactual Analysis Tutorial](tutorials/counterfactual-analysis.md) - Causal analysis
