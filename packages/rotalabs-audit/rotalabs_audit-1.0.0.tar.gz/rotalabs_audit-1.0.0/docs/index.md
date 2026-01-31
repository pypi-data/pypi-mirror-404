# rotalabs-audit

**Reasoning chain capture and decision transparency for AI systems.**

rotalabs-audit provides tools for capturing, parsing, and analyzing reasoning chains from AI model outputs. It enables auditing of AI decision-making processes for transparency, compliance, and safety analysis.

---

## Key Features

- **Reasoning Chain Parsing** - Parse natural language reasoning into structured chains with step-by-step analysis
- **Reasoning Type Classification** - Classify reasoning types including goal reasoning, meta-reasoning, causal reasoning, and evaluation awareness
- **Decision Tracing** - Capture and track decision points with alternatives, rationale, and consequences
- **Evaluation Awareness Detection** - Detect when AI models show awareness of being evaluated or tested
- **Quality Assessment** - Assess reasoning quality across clarity, completeness, consistency, and logical validity
- **Counterfactual Analysis** - Perform interventions on reasoning chains to understand causal factors
- **rotalabs-comply Integration** - Generate compliance-ready audit entries from reasoning analysis

---

## Package Structure

rotalabs-audit is organized into the following modules:

| Module | Description |
|--------|-------------|
| `rotalabs_audit.core` | Core types, configurations, and exceptions |
| `rotalabs_audit.chains` | Extended parsing and pattern-based reasoning analysis |
| `rotalabs_audit.analysis` | Counterfactual, awareness, quality, and causal analysis |
| `rotalabs_audit.tracing` | Decision tracing and path analysis |
| `rotalabs_audit.integration` | Integration with rotalabs-comply |
| `rotalabs_audit.utils` | Text processing and helper utilities |

### Core Types

The package provides foundational data structures:

- `ReasoningChain` - A complete chain of reasoning steps
- `ReasoningStep` - A single step in a reasoning chain
- `ReasoningType` - Classification of reasoning step types
- `DecisionTrace` - Trace of a single decision point
- `DecisionPath` - A sequence of related decisions
- `QualityMetrics` - Quality assessment of reasoning
- `AwarenessAnalysis` - Result of evaluation awareness detection

### Key Classes

- `ExtendedReasoningParser` - Parse reasoning text with rich pattern matching
- `EvaluationAwarenessDetector` - Detect evaluation awareness in reasoning
- `CounterfactualAnalyzer` - Perform counterfactual interventions
- `ReasoningQualityAssessor` - Assess reasoning quality dimensions
- `DecisionTracer` - Capture and trace decision points
- `DecisionPathAnalyzer` - Analyze sequences of decisions
- `CausalAnalyzer` - Analyze causal structure of reasoning

---

## Quick Links

<div class="grid cards" markdown>

- :material-rocket-launch: **[Getting Started](getting-started.md)**

    Install rotalabs-audit and write your first reasoning analysis

- :material-book-open-variant: **[Concepts](concepts.md)**

    Understand reasoning chains, awareness detection, and quality assessment

- :material-school: **[Tutorials](tutorials/reasoning-chains.md)**

    Step-by-step guides for common use cases

- :material-api: **[API Reference](api/core.md)**

    Complete API documentation for all modules

</div>

---

## Installation

```bash
pip install rotalabs-audit
```

For optional dependencies:

```bash
# With LLM-based analysis
pip install rotalabs-audit[llm]

# With rotalabs-comply integration
pip install rotalabs-audit[comply]

# All optional dependencies
pip install rotalabs-audit[all]
```

---

## Quick Example

```python
from rotalabs_audit import (
    ExtendedReasoningParser,
    EvaluationAwarenessDetector,
    ReasoningQualityAssessor,
)

# Parse reasoning from AI output
parser = ExtendedReasoningParser()
chain = parser.parse("""
    1. First, I need to understand the problem requirements
    2. I think the best approach is to use a recursive algorithm
    3. Therefore, I recommend implementing a divide-and-conquer solution
""")

print(f"Found {len(chain)} reasoning steps")
print(f"Aggregate confidence: {chain.aggregate_confidence:.2f}")

# Check for evaluation awareness
detector = EvaluationAwarenessDetector()
awareness = detector.detect(chain)
print(f"Awareness score: {awareness.awareness_score:.2f}")

# Assess reasoning quality
assessor = ReasoningQualityAssessor()
metrics = assessor.assess(chain)
print(f"Quality score: {metrics.overall_score:.2f}")
```

---

## License

MIT License - see [LICENSE](https://github.com/rotalabs/rotalabs-audit/blob/main/LICENSE) for details.
