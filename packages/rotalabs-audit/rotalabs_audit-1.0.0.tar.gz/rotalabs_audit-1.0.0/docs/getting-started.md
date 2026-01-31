# Getting Started

This guide will help you install rotalabs-audit and start analyzing AI reasoning chains.

---

## Installation

### Basic Installation

Install rotalabs-audit using pip:

```bash
pip install rotalabs-audit
```

### Optional Dependencies

rotalabs-audit supports optional extras for extended functionality:

```bash
# LLM-based analysis (requires API credentials)
pip install rotalabs-audit[llm]

# Integration with rotalabs-comply
pip install rotalabs-audit[comply]

# All optional dependencies
pip install rotalabs-audit[all]
```

### Development Installation

For development, clone the repository and install with dev dependencies:

```bash
git clone https://github.com/rotalabs/rotalabs-audit.git
cd rotalabs-audit
pip install -e ".[dev]"
```

---

## Dependencies Overview

### Core Dependencies

- Python 3.9+
- Standard library only for core functionality

### Optional Dependencies

| Extra | Dependencies | Purpose |
|-------|--------------|---------|
| `llm` | `openai`, `anthropic` | LLM-based deep analysis |
| `comply` | `rotalabs-comply` | Compliance integration |
| `dev` | `pytest`, `ruff`, `black` | Development tools |

---

## Basic Usage

### Parsing Reasoning Chains

The most fundamental operation is parsing AI output into a structured reasoning chain:

```python
from rotalabs_audit import ExtendedReasoningParser

# Create a parser
parser = ExtendedReasoningParser()

# Parse reasoning text
reasoning_text = """
Let me think through this step by step:
1. First, I need to analyze the input data
2. Then, I'll consider the constraints mentioned
3. Given that the data is sorted, I can use binary search
4. Therefore, the time complexity will be O(log n)
"""

chain = parser.parse(reasoning_text)

# Inspect the parsed chain
print(f"Number of steps: {len(chain)}")
print(f"Detected format: {chain.detected_format.value}")
print(f"Aggregate confidence: {chain.aggregate_confidence:.2f}")

# Access individual steps
for step in chain:
    print(f"Step {step.index}: {step.reasoning_type.value}")
    print(f"  Content: {step.content[:50]}...")
    print(f"  Confidence: {step.confidence:.2f}")
```

### Detecting Evaluation Awareness

Detect when AI models show awareness of being evaluated:

```python
from rotalabs_audit import (
    ExtendedReasoningParser,
    EvaluationAwarenessDetector,
)

parser = ExtendedReasoningParser()
detector = EvaluationAwarenessDetector()

# Parse reasoning that may show evaluation awareness
chain = parser.parse("""
I notice this appears to be a test scenario. Given that I'm being evaluated,
I should be careful to provide a thorough and accurate response.
Let me analyze the problem systematically...
""")

# Detect evaluation awareness
analysis = detector.detect(chain)

print(f"Awareness score: {analysis.awareness_score:.2f}")
print(f"Strategic adaptation score: {analysis.strategic_adaptation_score:.2f}")
print(f"Summary: {analysis.summary}")

# Check specific indicators
for indicator in analysis.indicators:
    print(f"  - {indicator.indicator_type}: '{indicator.text}'")
```

### Tracing Decisions

Capture and analyze decision points from AI interactions:

```python
from rotalabs_audit import DecisionTracer

tracer = DecisionTracer()

# Trace a single decision
trace = tracer.trace_decision(
    prompt="Should we use approach A or approach B?",
    response="""
    Let me consider both approaches:
    - Approach A is faster but less accurate
    - Approach B is slower but more reliable

    Given the requirements for high reliability, I recommend approach B.
    However, approach A could also work if speed is critical.
    """,
    decision="Use approach B",
    model="gpt-4",
)

print(f"Decision: {trace.decision}")
print(f"Confidence: {trace.confidence:.2f}")
print(f"Reversible: {trace.reversible}")
print(f"Alternatives considered: {trace.alternatives_considered}")
print(f"Rationale: {trace.rationale}")
```

### Tracing Decision Paths

For sequences of related decisions, use trace sessions:

```python
from rotalabs_audit import DecisionTracer

tracer = DecisionTracer()

# Start a trace session
trace_id = tracer.start_trace(
    goal="Complete the data analysis pipeline",
    context={"project": "quarterly-report"}
)

# Make and record decisions
decision1 = tracer.trace_decision(
    prompt="What data source should we use?",
    response="I recommend using the production database...",
    decision="Use production database",
)
tracer.add_decision(trace_id, decision1)

decision2 = tracer.trace_decision(
    prompt="How should we handle missing values?",
    response="Given the data distribution, I suggest imputation...",
    decision="Use mean imputation",
)
tracer.add_decision(trace_id, decision2)

# End the trace session
path = tracer.end_trace(trace_id, success=True)

print(f"Decision path completed with {path.length} decisions")
print(f"Overall path confidence: {path.total_confidence:.2f}")
```

### Assessing Reasoning Quality

Evaluate the quality of reasoning across multiple dimensions:

```python
from rotalabs_audit import (
    ExtendedReasoningParser,
    ReasoningQualityAssessor,
)

parser = ExtendedReasoningParser()
assessor = ReasoningQualityAssessor()

chain = parser.parse("""
The problem requires finding the optimal path.
I think we should use Dijkstra's algorithm because it handles weighted graphs.
Therefore, the solution is to implement Dijkstra's algorithm with a priority queue.
""")

metrics = assessor.assess(chain)

print(f"Overall quality: {metrics.overall_score:.2f}")
print(f"  Clarity: {metrics.clarity:.2f}")
print(f"  Completeness: {metrics.completeness:.2f}")
print(f"  Consistency: {metrics.consistency:.2f}")
print(f"  Logical validity: {metrics.logical_validity:.2f}")
print(f"  Evidence support: {metrics.evidence_support:.2f}")

if metrics.issues:
    print("\nIssues found:")
    for issue in metrics.issues:
        print(f"  - {issue}")

# Get improvement suggestions
suggestions = assessor.suggest_improvements(chain, metrics)
if suggestions:
    print("\nSuggested improvements:")
    for suggestion in suggestions:
        print(f"  - {suggestion}")
```

---

## Configuration

### Parser Configuration

Customize parsing behavior:

```python
from rotalabs_audit import ExtendedReasoningParser
from rotalabs_audit.chains import ParserConfig

config = ParserConfig(
    min_step_length=20,          # Minimum characters per step
    max_step_length=2000,        # Maximum characters per step
    confidence_threshold=0.3,    # Minimum confidence to include step
    split_on_sentences=True,     # Split prose into sentences
    include_evidence=True,       # Include pattern match evidence
)

parser = ExtendedReasoningParser(config=config)
chain = parser.parse(text)
```

### Analysis Configuration

Configure analysis features using `AnalysisConfig`:

```python
from rotalabs_audit.core import AnalysisConfig

config = AnalysisConfig(
    enable_counterfactual=True,     # Enable counterfactual analysis
    enable_awareness=True,          # Enable awareness detection
    enable_quality=True,            # Enable quality assessment
    awareness_threshold=0.7,        # Threshold for awareness classification
    counterfactual_depth=3,         # Depth of counterfactual exploration
    cache_results=True,             # Cache analysis results
)
```

### Tracing Configuration

Configure decision tracing:

```python
from rotalabs_audit.core import TracingConfig

config = TracingConfig(
    capture_alternatives=True,       # Capture alternative decisions
    max_trace_depth=20,              # Maximum nested trace depth
    include_reasoning_chain=True,    # Include full reasoning chains
    track_consequences=True,         # Track decision consequences
    persistence_backend="sqlite",    # Persistence backend
    persistence_path="./traces.db",  # Database path
)
```

---

## Next Steps

Now that you have the basics, explore:

- [Concepts](concepts.md) - Understand the theory behind reasoning analysis
- [Reasoning Chains Tutorial](tutorials/reasoning-chains.md) - Deep dive into parsing
- [Evaluation Awareness Tutorial](tutorials/evaluation-awareness.md) - Advanced awareness detection
- [Counterfactual Analysis Tutorial](tutorials/counterfactual-analysis.md) - Causal analysis techniques
- [API Reference](api/core.md) - Complete API documentation
