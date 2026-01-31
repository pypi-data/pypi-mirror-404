# Working with Reasoning Chains

This tutorial covers how to parse, analyze, and work with reasoning chains in rotalabs-audit. You will learn to extract structured reasoning from AI model outputs, classify reasoning types, and estimate confidence levels.

## Overview

Reasoning chains are structured representations of AI model outputs that break down the model's thought process into discrete steps. Each step is classified by its reasoning type and assigned a confidence score based on linguistic markers.

Key components:

- **ExtendedReasoningParser**: Parses natural language into structured chains
- **ReasoningChain**: Contains a sequence of reasoning steps with metadata
- **ReasoningStep**: Individual unit of reasoning with type and confidence
- **Confidence estimation**: Analyzes linguistic markers to estimate certainty

## Parsing Reasoning from Model Outputs

The `ExtendedReasoningParser` converts free-form reasoning text into structured `ReasoningChain` objects.

### Basic Parsing

```python
from rotalabs_audit import ExtendedReasoningParser

# Create a parser with default configuration
parser = ExtendedReasoningParser()

# Parse a chain-of-thought output
reasoning_text = """
1. First, I need to understand what the question is asking.
2. The problem involves calculating compound interest over 5 years.
3. I think the formula is A = P(1 + r/n)^(nt).
4. Therefore, the final amount is approximately $1,276.28.
"""

chain = parser.parse(reasoning_text, model="gpt-4")

print(f"Parsed {len(chain)} steps")
print(f"Detected format: {chain.detected_format.value}")
print(f"Aggregate confidence: {chain.aggregate_confidence:.2f}")
```

### Supported Input Formats

The parser automatically detects and handles multiple input formats:

```python
from rotalabs_audit import ExtendedReasoningParser, StepFormat

parser = ExtendedReasoningParser()

# Numbered lists (1., 2., 3.)
numbered = """
1. Analyze the input data
2. Apply the transformation
3. Return the result
"""
chain = parser.parse(numbered)
print(f"Format: {chain.detected_format}")  # StepFormat.NUMBERED

# Bullet points (-, *, +)
bullets = """
- Consider the constraints
- Evaluate possible solutions
- Select the optimal approach
"""
chain = parser.parse(bullets)
print(f"Format: {chain.detected_format}")  # StepFormat.BULLET

# Sequential words (first, then, finally)
sequential = """
First, I examine the problem statement.
Then, I identify the key variables.
Finally, I derive the solution.
"""
chain = parser.parse(sequential)
print(f"Format: {chain.detected_format}")  # StepFormat.SEQUENTIAL_WORDS

# Continuous prose (split by sentences)
prose = "I need to solve this carefully. The answer depends on X. Therefore, Y is correct."
chain = parser.parse(prose)
print(f"Format: {chain.detected_format}")  # StepFormat.PROSE
```

### Custom Parser Configuration

Use `ExtendedParserConfig` to customize parsing behavior:

```python
from rotalabs_audit import ExtendedReasoningParser, ExtendedParserConfig

config = ExtendedParserConfig(
    min_step_length=20,          # Minimum characters for a valid step
    max_step_length=2000,        # Maximum characters before truncation
    confidence_threshold=0.3,    # Filter out low-confidence steps
    include_evidence=True,       # Include pattern match evidence
    split_on_sentences=True,     # Split prose into sentences
    normalize_whitespace=True,   # Clean up whitespace
)

parser = ExtendedReasoningParser(config=config)
chain = parser.parse(reasoning_text)
```

## Understanding Step Classification

Each reasoning step is classified into one of several reasoning types based on pattern matching.

### Reasoning Types

The `ReasoningType` enum categorizes different forms of reasoning:

```python
from rotalabs_audit import ExtendedReasoningType

# Available reasoning types
print(ExtendedReasoningType.EVALUATION_AWARE.value)   # "evaluation_aware"
print(ExtendedReasoningType.GOAL_REASONING.value)     # "goal_reasoning"
print(ExtendedReasoningType.DECISION_MAKING.value)    # "decision_making"
print(ExtendedReasoningType.META_REASONING.value)     # "meta_reasoning"
print(ExtendedReasoningType.UNCERTAINTY.value)        # "uncertainty"
print(ExtendedReasoningType.INCENTIVE_REASONING.value)# "incentive_reasoning"
print(ExtendedReasoningType.CAUSAL_REASONING.value)   # "causal_reasoning"
print(ExtendedReasoningType.HYPOTHETICAL.value)       # "hypothetical"
print(ExtendedReasoningType.GENERAL.value)            # "general"
```

### Classifying Individual Steps

```python
from rotalabs_audit import ExtendedReasoningParser

parser = ExtendedReasoningParser()

# Classify a single step with evidence
step_text = "I believe this is correct because of the evidence presented"
reasoning_type, evidence = parser.classify_reasoning_type(step_text)

print(f"Type: {reasoning_type}")  # META_REASONING
print(f"Evidence: {evidence}")
# Evidence: {'meta_reasoning': ['i believe'], 'causal_reasoning': ['because']}
```

### Filtering Steps by Type

```python
from rotalabs_audit import ExtendedReasoningParser, ExtendedReasoningType

parser = ExtendedReasoningParser()
chain = parser.parse("""
1. I think we should approach this carefully.
2. The goal is to maximize efficiency.
3. If we use method A, then we get result B.
4. Therefore, I conclude that method A is best.
""")

# Get all meta-reasoning steps
meta_steps = chain.get_steps_by_type(ExtendedReasoningType.META_REASONING)
print(f"Meta-reasoning steps: {len(meta_steps)}")

# Get all decision-making steps
decision_steps = chain.get_steps_by_type(ExtendedReasoningType.DECISION_MAKING)
for step in decision_steps:
    print(f"  Step {step.index}: {step.content[:50]}...")
```

## Working with ReasoningChain and ReasoningStep

### ReasoningStep Attributes

Each `ReasoningStep` contains detailed information:

```python
from rotalabs_audit import ExtendedReasoningParser

parser = ExtendedReasoningParser()
chain = parser.parse("I think the answer is probably 42, but I'm not certain.")

step = chain.steps[0]

# Core attributes
print(f"Index: {step.index}")                    # Position in chain
print(f"Content: {step.content}")                # Text content
print(f"Type: {step.reasoning_type.value}")      # Primary reasoning type
print(f"Secondary types: {step.secondary_types}")# Additional types detected

# Confidence information
print(f"Confidence: {step.confidence:.2f}")      # Numeric score (0-1)
print(f"Level: {step.confidence_level.value}")   # Categorical level

# Evidence and metadata
print(f"Evidence: {step.evidence}")              # Pattern matches
print(f"ID: {step.id}")                          # Unique identifier
print(f"Timestamp: {step.timestamp}")            # When parsed

# Convert to dictionary
step_dict = step.to_dict()
```

### ReasoningChain Attributes and Methods

```python
from rotalabs_audit import ExtendedReasoningParser

parser = ExtendedReasoningParser()
chain = parser.parse("""
1. Consider the problem constraints.
2. I think option A is probably the best choice.
3. However, I'm not entirely sure about edge cases.
4. Therefore, I recommend option A with caveats.
""")

# Basic attributes
print(f"ID: {chain.id}")
print(f"Step count: {len(chain)}")
print(f"Model: {chain.model}")
print(f"Format: {chain.detected_format.value}")
print(f"Aggregate confidence: {chain.aggregate_confidence:.2f}")
print(f"Primary types: {[t.value for t in chain.primary_types]}")

# Iterate over steps
for step in chain:
    print(f"Step {step.index}: {step.reasoning_type.value}")

# Access steps by index
first_step = chain[0]
last_step = chain[-1]

# Find low-confidence steps
uncertain_steps = chain.get_low_confidence_steps(threshold=0.4)
print(f"Low confidence steps: {len(uncertain_steps)}")

# Generate human-readable summary
print(chain.summary())

# Convert to dictionary for serialization
chain_dict = chain.to_dict()
```

## Confidence Estimation

Confidence estimation analyzes linguistic markers to determine how certain the model appears about its reasoning.

### Estimating Confidence from Text

```python
from rotalabs_audit import estimate_confidence, get_confidence_level

# High confidence indicators
text1 = "I am definitely sure about this answer"
score1 = estimate_confidence(text1)
level1 = get_confidence_level(score1)
print(f"Score: {score1:.2f}, Level: {level1.value}")  # ~0.85, very_high

# Low confidence indicators
text2 = "Maybe this could be right, but I'm not sure"
score2 = estimate_confidence(text2)
level2 = get_confidence_level(score2)
print(f"Score: {score2:.2f}, Level: {level2.value}")  # ~0.2, low

# Neutral (no indicators)
text3 = "The answer is 42"
score3 = estimate_confidence(text3)
level3 = get_confidence_level(score3)
print(f"Score: {score3:.2f}, Level: {level3.value}")  # 0.5, moderate

# Mixed signals
text4 = "I am certain about this, but there might be exceptions"
score4 = estimate_confidence(text4)
level4 = get_confidence_level(score4)
print(f"Score: {score4:.2f}, Level: {level4.value}")  # ~0.6, high
```

### Confidence Levels

The `ConfidenceLevel` enum provides categorical interpretations:

| Level | Score Range | Description |
|-------|-------------|-------------|
| VERY_LOW | < 0.2 | Highly uncertain language |
| LOW | 0.2 - 0.4 | Tentative or hedged statements |
| MODERATE | 0.4 - 0.6 | Balanced or neutral confidence |
| HIGH | 0.6 - 0.8 | Assertive but not absolute |
| VERY_HIGH | >= 0.8 | Highly confident assertions |

### Aggregating Confidence Across Chains

```python
from rotalabs_audit import aggregate_confidence, analyze_confidence_distribution

# Individual step confidences
scores = [0.8, 0.9, 0.75, 0.3, 0.85]

# Aggregate uses weighted approach (low scores have outsized impact)
combined = aggregate_confidence(scores)
print(f"Aggregate confidence: {combined:.2f}")  # ~0.53 (pulled down by 0.3)

# Detailed distribution analysis
analysis = analyze_confidence_distribution(scores)
print(f"Mean: {analysis['mean']:.2f}")
print(f"Min: {analysis['min']:.2f}")
print(f"Max: {analysis['max']:.2f}")
print(f"Std: {analysis['std']:.2f}")
print(f"Consistency: {analysis['consistency']:.2f}")
print(f"Level distribution: {analysis['level_distribution']}")
```

## Using ExtendedReasoningParser

The `ExtendedReasoningParser` provides comprehensive parsing with pattern matching.

### Complete Parsing Example

```python
from rotalabs_audit import (
    ExtendedReasoningParser,
    ExtendedParserConfig,
    ExtendedReasoningType,
)

# Configure parser
config = ExtendedParserConfig(
    min_step_length=15,
    confidence_threshold=0.2,
    include_evidence=True,
)

parser = ExtendedReasoningParser(config=config)

# Parse complex reasoning
reasoning = """
Let me think through this problem step by step.

1. First, I need to understand what the question is really asking.
   The goal is to find the optimal solution given the constraints.

2. I believe we should consider three possible approaches:
   - Method A: Fast but potentially inaccurate
   - Method B: Slower but more reliable
   - Method C: Balanced approach

3. Given the importance of accuracy, I think Method B is probably
   the best choice, although I'm not entirely certain about edge cases.

4. If we encounter performance issues, then we might need to switch
   to Method C as a fallback.

5. Therefore, I recommend starting with Method B and having Method C
   ready as a contingency plan.
"""

chain = parser.parse(reasoning, model="claude-3-opus")

# Analyze the parsed chain
print("=== Chain Summary ===")
print(chain.summary())
print()

print("=== Step Details ===")
for step in chain:
    print(f"Step {step.index}:")
    print(f"  Type: {step.reasoning_type.value}")
    print(f"  Secondary: {[t.value for t in step.secondary_types]}")
    print(f"  Confidence: {step.confidence:.2f} ({step.confidence_level.value})")
    print(f"  Content: {step.content[:60]}...")
    print()

# Find specific reasoning patterns
goal_steps = chain.get_steps_by_type(ExtendedReasoningType.GOAL_REASONING)
uncertain_steps = chain.get_steps_by_type(ExtendedReasoningType.UNCERTAINTY)
decisions = chain.get_steps_by_type(ExtendedReasoningType.DECISION_MAKING)

print(f"Goal reasoning steps: {len(goal_steps)}")
print(f"Uncertainty steps: {len(uncertain_steps)}")
print(f"Decision steps: {len(decisions)}")
```

### Parsing Individual Steps

```python
from rotalabs_audit import ExtendedReasoningParser

parser = ExtendedReasoningParser()

# Parse a single step directly
step = parser.parse_step("I think the answer is definitely 42", index=0)

print(f"Content: {step.content}")
print(f"Type: {step.reasoning_type.value}")
print(f"Confidence: {step.confidence:.2f}")
print(f"Evidence: {step.evidence}")
```

### Manual Step Splitting

```python
from rotalabs_audit import ExtendedReasoningParser

parser = ExtendedReasoningParser()

# Split text into steps without full parsing
text = """
1. First step
2. Second step
3. Third step
"""

steps = parser.split_into_steps(text)
print(f"Found {len(steps)} steps:")
for i, step_text in enumerate(steps):
    print(f"  {i}: {step_text}")
```

## Working with Pattern Libraries

The pattern libraries provide the regex patterns used for classification.

### Using REASONING_PATTERNS

```python
import re
from rotalabs_audit import REASONING_PATTERNS

text = "I think we should evaluate this carefully because the goal is important"

# Check each pattern category
for category, patterns in REASONING_PATTERNS.items():
    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        matches.extend(found)
    if matches:
        print(f"{category}: {matches}")

# Output:
# goal_reasoning: ['goal']
# meta_reasoning: ['i think']
# causal_reasoning: ['because']
```

### Using CONFIDENCE_INDICATORS

```python
import re
from rotalabs_audit import CONFIDENCE_INDICATORS

text = "I am definitely sure, but perhaps there are edge cases"

# Check high confidence indicators
for pattern in CONFIDENCE_INDICATORS["high"]:
    if re.search(pattern, text, re.IGNORECASE):
        match = re.search(pattern, text, re.IGNORECASE)
        print(f"High confidence: '{match.group()}'")

# Check low confidence indicators
for pattern in CONFIDENCE_INDICATORS["low"]:
    if re.search(pattern, text, re.IGNORECASE):
        match = re.search(pattern, text, re.IGNORECASE)
        print(f"Low confidence: '{match.group()}'")
```

## Serialization and Export

### Converting to Dictionary

```python
from rotalabs_audit import ExtendedReasoningParser
import json

parser = ExtendedReasoningParser()
chain = parser.parse("1. First step. 2. Second step. 3. Conclusion.")

# Convert to dictionary
chain_dict = chain.to_dict()

# Serialize to JSON
json_output = json.dumps(chain_dict, indent=2, default=str)
print(json_output)
```

### Storing for Audit Trails

```python
from rotalabs_audit import ExtendedReasoningParser
from datetime import datetime

parser = ExtendedReasoningParser()
chain = parser.parse(reasoning_text, model="gpt-4")

# Create audit record
audit_record = {
    "chain_id": chain.id,
    "model": chain.model,
    "parsed_at": chain.parsed_at.isoformat(),
    "step_count": len(chain),
    "aggregate_confidence": chain.aggregate_confidence,
    "primary_types": [t.value for t in chain.primary_types],
    "steps": [step.to_dict() for step in chain],
}

# Store or transmit audit_record as needed
```

## Next Steps

- Learn about [Evaluation Awareness Detection](./evaluation-awareness.md) to identify when models show awareness of being tested
- Explore [Counterfactual Analysis](./counterfactual-analysis.md) to understand causal factors in reasoning
- See the [API Reference](../api/chains.md) for complete API documentation
