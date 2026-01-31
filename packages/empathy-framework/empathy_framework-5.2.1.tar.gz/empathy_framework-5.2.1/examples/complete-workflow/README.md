# Complete Workflow Example

Demonstrates the full Empathy Framework 4.7.0 workflow.

> **Attribution**: Architectural patterns inspired by [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by Affaan Mustafa (MIT License).

## Workflow

```
SessionStart → Hooks → Interactions → Learning → PreCompact → SessionEnd
```

## Run

```bash
cd examples/complete-workflow
python workflow_example.py
```

## What It Demonstrates

1. **Session Start** - Hook fires, previous state restored
2. **Interactions** - Recorded for learning evaluation
3. **Corrections** - Captured as high-value learning patterns
4. **State Save** - Context preserved through compaction
5. **Pattern Extraction** - Learning from corrections
6. **Session End** - Quality evaluation, patterns stored

## Output

```
SESSION START
[HOOK] Session starting for user: demo_user

INTERACTION
[INTERACTION] Recorded: How do I handle errors...

CORRECTION
[CORRECTION] Recorded: 'Log using print()' → 'Use logging module'

SESSION END
[LEARNING] Extracted: error logging → Use logging module
Session quality: good
```
