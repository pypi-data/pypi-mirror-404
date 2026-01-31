# NewSampleWorkflow1Workflow

**A team leader that has 10 years of experiance coding.**

---

## Overview

**Patterns Used:**
- `multi-stage` - Multiple sequential stages with different tiers

**Complexity:** COMPLEX

**Stages:**
1. **analyze** - CHEAP tier
2. **process** - CAPABLE tier
3. **report** - PREMIUM tier

---

## Usage

```python
from empathy_os.workflows.new_sample_workflow1 import NewSampleWorkflow1Workflow

# Initialize workflow
workflow = NewSampleWorkflow1Workflow(
)

# Execute
result = await workflow.execute(
    # Add your input data here
)

# Check result
print(f"Success: {result.success}")
```

---

## CLI Usage

```bash
# Run via empathy CLI
empathy workflow run new-sample-workflow1 --input '{"key": "value"}'

# With options
```

---

## Configuration

This workflow does not use configuration files.

---

## Stages

### 1. Analyze

**Tier:** CHEAP

**Purpose:** TODO: Add description
**Input:** TODO: Add description
**Output:** TODO: Add description
### 2. Process

**Tier:** CAPABLE

**Purpose:** TODO: Add description
**Input:** TODO: Add description
**Output:** TODO: Add description
### 3. Report

**Tier:** PREMIUM

**Purpose:** TODO: Add description
**Input:** TODO: Add description
**Output:** TODO: Add description

---

## Testing

```bash
# Run tests
pytest tests/unit/workflows/test_new_sample_workflow1.py -v

# Run with coverage
pytest tests/unit/workflows/test_new_sample_workflow1.py --cov

# Run specific test
pytest tests/unit/workflows/test_new_sample_workflow1.py::TestNewSampleWorkflow1Workflow::test_workflow_execution_basic -v
```

---

## Cost Optimization

**Tier Distribution:**
- CHEAP: 1 stage(s)
- CAPABLE: 1 stage(s)
- PREMIUM: 1 stage(s)

---

## Examples

### Example 1: Basic Usage

```python
workflow = NewSampleWorkflow1Workflow()
result = await workflow.execute(
    # TODO: Add example input
)
```

### Example 2: With Custom Settings

```python
workflow = NewSampleWorkflow1Workflow(
)
result = await workflow.execute(
    # TODO: Add example input
)
```

---

## Troubleshooting

### Common Issues

**Issue:** Workflow fails with "X not found"
**Solution:** TODO: Add solution

**Issue:** High costs
**Solution:** Consider adding conditional tier routing
---

## Related Workflows

- TODO: Add related workflows

---

**Generated:** 2026-01-05
**Patterns:** multi-stage
**Complexity:** COMPLEX
