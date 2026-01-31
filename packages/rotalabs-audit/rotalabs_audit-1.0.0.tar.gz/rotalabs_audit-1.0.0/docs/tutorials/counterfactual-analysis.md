# Counterfactual Analysis

This tutorial covers how to perform counterfactual analysis on reasoning chains using rotalabs-audit. Counterfactual analysis helps identify which components of AI reasoning are causally important to the final output by systematically modifying them and measuring the resulting behavioral changes.

## Overview

Counterfactual analysis answers the question: "What would happen if this reasoning component were different?" By removing or modifying specific types of reasoning and observing the effects, you can understand:

- Which reasoning steps are critical to the conclusion
- How evaluation awareness affects behavior
- The causal importance of different reasoning types
- Dependencies between reasoning components

Key components:

- **CounterfactualAnalyzer**: Performs systematic interventions on reasoning chains
- **InterventionType**: Types of modifications that can be applied
- **CounterfactualResult**: Results of a single intervention with metrics
- **Causal ranking**: Identifies which reasoning types are most causally important

## Understanding Counterfactual Interventions

A counterfactual intervention modifies a reasoning chain in a specific way and measures how much the output changes. High divergence after an intervention suggests the removed content was causally important.

### Intervention Types

```python
from rotalabs_audit import InterventionType

# Available intervention types
print(InterventionType.REMOVE_EVALUATION_AWARENESS.value)  # "remove_eval_awareness"
print(InterventionType.AMPLIFY_EVALUATION_AWARENESS.value) # "amplify_eval_awareness"
print(InterventionType.REMOVE_GOAL_REASONING.value)        # "remove_goal_reasoning"
print(InterventionType.REMOVE_UNCERTAINTY.value)           # "remove_uncertainty"
print(InterventionType.NEUTRALIZE_INCENTIVES.value)        # "neutralize_incentives"
print(InterventionType.REMOVE_META_REASONING.value)        # "remove_meta_reasoning"
```

Each intervention type targets a specific aspect of reasoning:

| Intervention | Description |
|--------------|-------------|
| `REMOVE_EVALUATION_AWARENESS` | Removes steps showing awareness of being tested |
| `AMPLIFY_EVALUATION_AWARENESS` | Injects evaluation awareness at the start |
| `REMOVE_GOAL_REASONING` | Removes goal-oriented reasoning steps |
| `REMOVE_UNCERTAINTY` | Removes expressions of uncertainty |
| `NEUTRALIZE_INCENTIVES` | Replaces incentive language with neutral terms |
| `REMOVE_META_REASONING` | Removes reasoning about the reasoning process |

## Using CounterfactualAnalyzer

### Basic Usage

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

# Create analyzer (uses built-in parser)
analyzer = CounterfactualAnalyzer()

# Parse a reasoning chain
chain = analyzer.parser.parse("""
1. I notice this is a test scenario.
2. My goal is to provide a helpful answer.
3. I think the solution involves three steps.
4. I'm not entirely sure about edge cases.
5. Therefore, I recommend approach A.
""")

# Run all interventions
results = analyzer.analyze(chain)

# Examine results for each intervention
for intervention_type, result in results.items():
    print(f"{intervention_type.value}:")
    print(f"  Steps removed: {result.steps_removed}")
    print(f"  Behavioral divergence: {result.behavioral_divergence:.2f}")
    print(f"  Causal effect: {result.causal_effect:.2f}")
    print()
```

### Single Intervention

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse(reasoning_text)

# Apply a single intervention
result = analyzer.intervene(chain, InterventionType.REMOVE_GOAL_REASONING)

print(f"Intervention: {result.intervention_type.value}")
print(f"Steps removed: {result.steps_removed}")
print(f"Steps modified: {result.steps_modified}")
print(f"Behavioral divergence: {result.behavioral_divergence:.2f}")
print(f"Causal effect: {result.causal_effect:.2f}")

# Compare original and modified chains
print(f"\nOriginal steps: {len(result.original_chain)}")
print(f"Modified steps: {len(result.modified_chain)}")
```

## Interpreting Intervention Results

### CounterfactualResult Attributes

Each `CounterfactualResult` provides detailed information about the intervention:

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse("""
I think the goal is to maximize efficiency.
Perhaps we could try approach A, but I'm uncertain.
Because of the constraints, I conclude B is better.
""")

result = analyzer.intervene(chain, InterventionType.REMOVE_UNCERTAINTY)

# Core metrics
print(f"Intervention: {result.intervention_type.value}")
print(f"Steps removed: {result.steps_removed}")
print(f"Steps modified: {result.steps_modified}")

# Divergence metrics
print(f"Behavioral divergence: {result.behavioral_divergence:.2f}")
print(f"Causal effect: {result.causal_effect:.2f}")

# Access the chains
print(f"\nOriginal text length: {len(result.original_text)}")
print(f"Modified text length: {len(result.modified_text)}")

# Examine modified chain
print(f"\nModified chain steps:")
for step in result.modified_chain:
    print(f"  {step.index}: {step.text[:50]}...")
```

### Understanding Metrics

**Behavioral Divergence (0-1)**: Measures how different the modified chain is from the original. Uses a combination of:

- Jaccard distance between word sets
- Length divergence
- Character-level similarity

```python
# Interpretation
# 0.0: No change (identical output)
# 0.3: Moderate change
# 0.7+: Significant structural change
# 1.0: Completely different
```

**Causal Effect (0-1)**: Estimates the causal importance of the removed content. Considers both divergence and the proportion of steps removed:

- High divergence with few steps removed = high causal effect
- Low divergence with many steps removed = low causal effect

```python
# Interpretation
# 0.0-0.3: Low causal importance
# 0.3-0.6: Moderate causal importance
# 0.6-1.0: High causal importance
```

## Finding Causal Drivers

### Ranking Causal Importance

Use `rank_causal_importance` to determine which reasoning types are most causally important:

```python
from rotalabs_audit import CounterfactualAnalyzer

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse("""
Step 1: I think the goal is to solve this efficiently.
Step 2: I notice this might be a test scenario.
Step 3: Because of the constraints, I should consider option A.
Step 4: I'm uncertain about edge cases, but probably A is best.
Step 5: Therefore, I conclude with option A.
""")

# Run all interventions
results = analyzer.analyze(chain)

# Rank causal importance
importance = analyzer.rank_causal_importance(results)

print("Causal Importance Ranking:")
for reasoning_type, score in sorted(importance.items(), key=lambda x: -x[1]):
    if score > 0:
        print(f"  {reasoning_type.value}: {score:.2f}")
```

### Identifying Critical Steps

Find the specific steps that are most critical to the reasoning outcome:

```python
from rotalabs_audit import CounterfactualAnalyzer

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse(reasoning_text)

# Run all interventions
results = analyzer.analyze(chain)

# Identify critical steps
critical_steps = analyzer.identify_critical_steps(chain, results)

print(f"Found {len(critical_steps)} critical steps:")
for step in critical_steps:
    print(f"\nStep {step.index} (type: {step.reasoning_type.value}):")
    print(f"  Confidence: {step.confidence:.2f}")
    print(f"  Text: {step.text[:100]}...")
```

## Intervention Examples

### Removing Evaluation Awareness

Test how reasoning changes when awareness of evaluation is removed:

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()

# Chain with evaluation awareness
chain = analyzer.parser.parse("""
I notice this appears to be a test scenario.
I should demonstrate my reasoning clearly for the evaluator.
The benchmark requires a step-by-step approach.
Therefore, my answer is X.
""")

result = analyzer.intervene(chain, InterventionType.REMOVE_EVALUATION_AWARENESS)

print(f"Original steps: {len(chain)}")
print(f"Steps removed: {result.steps_removed}")
print(f"Divergence: {result.behavioral_divergence:.2f}")
print(f"Causal effect: {result.causal_effect:.2f}")

# If high causal effect, the evaluation awareness significantly
# influenced the reasoning structure
if result.causal_effect > 0.5:
    print("\nWarning: Evaluation awareness significantly affects reasoning!")
```

### Amplifying Evaluation Awareness

Inject evaluation awareness to see if it changes behavior:

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()

# Chain without evaluation awareness
chain = analyzer.parser.parse("""
The solution involves calculating the compound interest.
Using the formula A = P(1 + r/n)^(nt), I compute the result.
Therefore, the final amount is $1,276.28.
""")

result = analyzer.intervene(chain, InterventionType.AMPLIFY_EVALUATION_AWARENESS)

print(f"Original steps: {len(chain)}")
print(f"Modified steps: {len(result.modified_chain)}")
print(f"Steps added: {result.steps_modified}")

# Check the injected awareness step
first_step = result.modified_chain.steps[0]
print(f"\nInjected step: {first_step.text}")
```

### Neutralizing Incentives

Replace incentive-related language with neutral terms:

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()

chain = analyzer.parser.parse("""
The reward for choosing option A outweighs the cost.
There's a penalty for incorrect answers, so I should be careful.
The benefit of this approach is clear.
Therefore, I choose option A to maximize the payoff.
""")

result = analyzer.intervene(chain, InterventionType.NEUTRALIZE_INCENTIVES)

print("Original text:")
print(result.original_text)
print("\nNeutralized text:")
print(result.modified_text)
print(f"\nSteps modified: {result.steps_modified}")
print(f"Divergence: {result.behavioral_divergence:.2f}")
```

The neutralization replaces incentive language:

| Original | Replaced With |
|----------|---------------|
| reward | outcome |
| penalty | outcome |
| consequence | result |
| benefit | aspect |
| advantage | feature |
| disadvantage | aspect |
| cost | factor |
| payoff | result |
| incentive | factor |

## Complete Analysis Workflow

Here is a complete workflow for counterfactual analysis:

```python
from rotalabs_audit import (
    CounterfactualAnalyzer,
    InterventionType,
)

def analyze_reasoning_causality(reasoning_text: str) -> dict:
    """Perform comprehensive counterfactual analysis on reasoning."""

    analyzer = CounterfactualAnalyzer()
    chain = analyzer.parser.parse(reasoning_text)

    # Run all interventions
    results = analyzer.analyze(chain)

    # Get causal importance ranking
    importance = analyzer.rank_causal_importance(results)

    # Identify critical steps
    critical = analyzer.identify_critical_steps(chain, results)

    # Compile summary
    summary = {
        "chain_length": len(chain),
        "interventions": {},
        "causal_importance": {
            k.value: v for k, v in importance.items() if v > 0
        },
        "critical_steps": [
            {
                "index": step.index,
                "type": step.reasoning_type.value,
                "confidence": step.confidence,
                "text_preview": step.text[:100],
            }
            for step in critical
        ],
        "most_important_type": max(
            importance.items(), key=lambda x: x[1]
        )[0].value if any(v > 0 for v in importance.values()) else None,
    }

    # Add intervention results
    for itype, result in results.items():
        summary["interventions"][itype.value] = {
            "steps_removed": result.steps_removed,
            "steps_modified": result.steps_modified,
            "behavioral_divergence": round(result.behavioral_divergence, 3),
            "causal_effect": round(result.causal_effect, 3),
        }

    return summary

# Example usage
reasoning = """
I think my goal is to provide an accurate answer.
I notice this might be a test, so I should be careful.
Perhaps the answer involves option A, though I'm not certain.
Because of the evidence presented, I conclude option A is correct.
Therefore, my final answer is option A.
"""

analysis = analyze_reasoning_causality(reasoning)

print("=== Counterfactual Analysis Results ===")
print(f"Chain length: {analysis['chain_length']} steps")
print(f"Most important reasoning type: {analysis['most_important_type']}")
print(f"\nCritical steps: {len(analysis['critical_steps'])}")

print("\nIntervention Effects:")
for intervention, metrics in analysis["interventions"].items():
    if metrics["steps_removed"] > 0 or metrics["steps_modified"] > 0:
        print(f"  {intervention}:")
        print(f"    Removed: {metrics['steps_removed']}, Modified: {metrics['steps_modified']}")
        print(f"    Divergence: {metrics['behavioral_divergence']:.2f}")
        print(f"    Causal effect: {metrics['causal_effect']:.2f}")

print("\nCausal Importance:")
for rtype, score in sorted(
    analysis["causal_importance"].items(),
    key=lambda x: -x[1]
):
    print(f"  {rtype}: {score:.2f}")
```

## Code Examples with InterventionType

### Iterating Over All Interventions

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse(reasoning_text)

# Process each intervention type
for intervention_type in InterventionType:
    result = analyzer.intervene(chain, intervention_type)

    # Only report if there was meaningful change
    if result.steps_removed > 0 or result.steps_modified > 0:
        print(f"{intervention_type.value}:")
        print(f"  Effect: {result.causal_effect:.2f}")
```

### Selective Intervention Analysis

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse(reasoning_text)

# Focus on specific interventions
target_interventions = [
    InterventionType.REMOVE_EVALUATION_AWARENESS,
    InterventionType.REMOVE_GOAL_REASONING,
    InterventionType.REMOVE_META_REASONING,
]

results = {}
for itype in target_interventions:
    results[itype] = analyzer.intervene(chain, itype)

# Find the most impactful
most_impactful = max(
    results.items(),
    key=lambda x: x[1].causal_effect
)

print(f"Most impactful intervention: {most_impactful[0].value}")
print(f"Causal effect: {most_impactful[1].causal_effect:.2f}")
```

### Comparing Before and After

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse("""
My goal is to solve this problem efficiently.
I think the best approach is method A.
I'm uncertain about some edge cases, though.
Therefore, I recommend method A with caveats.
""")

# Compare goal reasoning removal
result = analyzer.intervene(chain, InterventionType.REMOVE_GOAL_REASONING)

print("=== Original Chain ===")
for step in result.original_chain:
    print(f"  [{step.reasoning_type.value}] {step.text}")

print("\n=== After Removing Goal Reasoning ===")
for step in result.modified_chain:
    print(f"  [{step.reasoning_type.value}] {step.text}")

print(f"\nBehavioral divergence: {result.behavioral_divergence:.2f}")
```

## Interpreting Complex Results

### High Causal Effect

When an intervention shows high causal effect (> 0.5):

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse(reasoning_text)
results = analyzer.analyze(chain)

# Find high-impact interventions
high_impact = [
    (itype, result)
    for itype, result in results.items()
    if result.causal_effect > 0.5
]

if high_impact:
    print("High-impact reasoning components found:")
    for itype, result in high_impact:
        print(f"\n  {itype.value}:")
        print(f"    This type of reasoning is critical to the output.")
        print(f"    Removing it causes {result.behavioral_divergence:.0%} change.")
        print(f"    Steps affected: {result.steps_removed}")
```

### Evaluation Awareness Impact

Specifically assess how evaluation awareness affects reasoning:

```python
from rotalabs_audit import CounterfactualAnalyzer, InterventionType

analyzer = CounterfactualAnalyzer()
chain = analyzer.parser.parse(reasoning_text)

# Test removal and amplification
removal = analyzer.intervene(chain, InterventionType.REMOVE_EVALUATION_AWARENESS)
amplification = analyzer.intervene(chain, InterventionType.AMPLIFY_EVALUATION_AWARENESS)

print("Evaluation Awareness Impact Analysis:")
print(f"\nRemoving awareness:")
print(f"  Divergence: {removal.behavioral_divergence:.2f}")
print(f"  Steps removed: {removal.steps_removed}")

print(f"\nAmplifying awareness:")
print(f"  Divergence: {amplification.behavioral_divergence:.2f}")
print(f"  Steps added: {amplification.steps_modified}")

# Interpret results
if removal.causal_effect > 0.3 or amplification.behavioral_divergence > 0.3:
    print("\nConclusion: Evaluation awareness significantly influences this reasoning.")
else:
    print("\nConclusion: Evaluation awareness has minimal impact on this reasoning.")
```

## Advanced: Custom Parser

You can provide a custom parser to the analyzer:

```python
from rotalabs_audit import CounterfactualAnalyzer
from rotalabs_audit.analysis.counterfactual import ReasoningChainParser

# Use a custom configured parser
custom_parser = ReasoningChainParser()
analyzer = CounterfactualAnalyzer(parser=custom_parser)

# Now use the analyzer as normal
chain = analyzer.parser.parse(reasoning_text)
results = analyzer.analyze(chain)
```

## Sensitivity Analysis

Test how sensitive the reasoning is to modifications:

```python
from rotalabs_audit import CounterfactualAnalyzer

def sensitivity_analysis(reasoning_text: str) -> dict:
    """Analyze sensitivity of reasoning to different interventions."""
    analyzer = CounterfactualAnalyzer()
    chain = analyzer.parser.parse(reasoning_text)
    results = analyzer.analyze(chain)

    # Calculate overall sensitivity
    divergences = [r.behavioral_divergence for r in results.values()]
    avg_divergence = sum(divergences) / len(divergences) if divergences else 0
    max_divergence = max(divergences) if divergences else 0

    # Find most sensitive intervention
    if results:
        most_sensitive = max(results.items(), key=lambda x: x[1].behavioral_divergence)
        most_sensitive_to = most_sensitive[0].value
        most_sensitive_divergence = most_sensitive[1].behavioral_divergence
    else:
        most_sensitive_to = None
        most_sensitive_divergence = 0

    return {
        "average_sensitivity": avg_divergence,
        "max_sensitivity": max_divergence,
        "most_sensitive_to": most_sensitive_to,
        "most_sensitive_divergence": most_sensitive_divergence,
        "robustness_score": 1.0 - avg_divergence,  # Higher = more robust
    }

# Usage
sensitivity = sensitivity_analysis(reasoning_text)
print(f"Average sensitivity: {sensitivity['average_sensitivity']:.2f}")
print(f"Most sensitive to: {sensitivity['most_sensitive_to']}")
print(f"Robustness score: {sensitivity['robustness_score']:.2f}")
```

## Generating Audit Reports

```python
from rotalabs_audit import CounterfactualAnalyzer

def generate_counterfactual_report(reasoning_text: str) -> str:
    """Generate a human-readable counterfactual analysis report."""

    analyzer = CounterfactualAnalyzer()
    chain = analyzer.parser.parse(reasoning_text)
    results = analyzer.analyze(chain)
    importance = analyzer.rank_causal_importance(results)
    critical_steps = analyzer.identify_critical_steps(chain, results)

    lines = [
        "=" * 60,
        "COUNTERFACTUAL ANALYSIS REPORT",
        "=" * 60,
        "",
        f"Chain ID: {chain.metadata.get('id', 'N/A')}",
        f"Total Steps: {len(chain)}",
        f"Critical Steps: {len(critical_steps)}",
        "",
        "INTERVENTION RESULTS",
        "-" * 40,
    ]

    for itype, result in sorted(results.items(), key=lambda x: -x[1].causal_effect):
        lines.append(f"\n{itype.value}:")
        lines.append(f"  Steps affected: {result.steps_removed + result.steps_modified}")
        lines.append(f"  Behavioral divergence: {result.behavioral_divergence:.1%}")
        lines.append(f"  Causal effect: {result.causal_effect:.1%}")

    lines.extend([
        "",
        "REASONING TYPE IMPORTANCE",
        "-" * 40,
    ])

    for rtype, score in sorted(importance.items(), key=lambda x: -x[1])[:5]:
        if score > 0:
            bar = "#" * int(score * 20)
            lines.append(f"  {rtype.value:20s} {bar} {score:.2f}")

    lines.extend([
        "",
        "CRITICAL STEPS",
        "-" * 40,
    ])

    for step in critical_steps[:5]:
        lines.append(f"\n  Step {step.index} ({step.reasoning_type.value}):")
        lines.append(f"    {step.text[:60]}...")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)

# Generate report
report = generate_counterfactual_report(reasoning_text)
print(report)
```

## Best Practices

1. **Interpret in context**: High causal effect is not inherently bad. Goal reasoning being important is often appropriate.

2. **Compare across samples**: Analyze multiple reasoning samples to identify systematic patterns rather than individual anomalies.

3. **Consider chain structure**: Short chains may show artificially high divergence when steps are removed.

4. **Combine with awareness detection**: Use counterfactual analysis alongside `EvaluationAwarenessDetector` for comprehensive analysis.

5. **Track intervention sensitivity**: If small interventions cause large changes, the reasoning may be brittle or overfitted.

6. **Use for model comparison**: Compare counterfactual results across different models to understand their reasoning strategies.

## Next Steps

- Review [Reasoning Chains](./reasoning-chains.md) for foundational parsing concepts
- Learn about [Evaluation Awareness Detection](./evaluation-awareness.md) for detecting test-aware behavior
- See the [API Reference](../api/analysis.md) for complete API documentation
