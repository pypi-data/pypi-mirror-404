---
description: Empathy Framework - API Reference API reference: **Version:** 4.0.0 **Last Updated:** January 16, 2026 **Status:** Living Documentation --- ## Overvi
---

# Empathy Framework - API Reference

**Version:** 4.0.0
**Last Updated:** January 16, 2026
**Status:** Living Documentation

---

## Overview

This API reference documents the **actual implementation** of Empathy Framework v4.0. Where APIs are private or missing, we note the workarounds and future plans.

**📘 See Also:**
- [ARCHITECTURAL_GAPS_ANALYSIS.md](../ARCHITECTURAL_GAPS_ANALYSIS.md) - Known gaps between ideal and actual
- [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) - How to extend the framework
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design overview

---

## API Documentation Structure

### 🟢 Core APIs (Public, Stable)
- [Meta-Orchestration API](./meta-orchestration.md) - v4.0 dynamic agent composition
- [Workflow API](./workflows.md) - 10 built-in workflows
- [Model Provider API](./models.md) - Multi-provider LLM routing
- [Cache API](./cache.md) - Response caching (hash-only & hybrid)
- [Telemetry API](./telemetry.md) - Usage tracking and analytics

### 🟡 Memory APIs (Partially Public)
- [Redis Short-Term Memory](./memory-redis.md) - Session storage (public API)
- [Unified Memory](./memory-unified.md) - Multi-tier memory (API incomplete, see gaps)
- [Long-Term Memory](./memory-long-term.md) - Encrypted patterns (implementation TBD)

### 🟠 Configuration APIs
- [Empathy Config](./config.md) - Configuration management
- [Workflow Config](./workflow-config.md) - Workflow configuration

### 🔵 Wizard APIs (Legacy, Stable)
- [Base Wizard](./base-wizard.md) - Building custom wizards
- [Built-in Wizards](./wizards.md) - CustomerSupport, Healthcare (deprecated), Technology (deprecated)

---

## Quick Reference by Use Case

### "I want to run a security audit"

```python
from empathy_os.workflows import SecurityAuditWorkflow

workflow = SecurityAuditWorkflow()
result = await workflow.execute(target_path="./src")

print(f"Found {len(result.findings)} issues")
for finding in result.findings:
    print(f"- {finding.severity}: {finding.description}")
```

**API Docs:** [Workflow API](./workflows.md#securityauditworkflow)

---

### "I want to use meta-orchestration"

```python
from empathy_os.workflows.orchestrated_release_prep import (
    OrchestratedReleasePrepWorkflow
)

workflow = OrchestratedReleasePrepWorkflow()
report = await workflow.execute(path=".")

if report.approved:
    print(f"✅ Release approved! Confidence: {report.confidence}")
else:
    print("❌ Blockers:")
    for blocker in report.blockers:
        print(f"  - {blocker}")
```

**API Docs:** [Meta-Orchestration API](./meta-orchestration.md)

---

### "I want to configure providers"

```python
# CLI approach (recommended)
# python -m empathy_os.models.cli provider --set hybrid

# Programmatic approach
from empathy_os.models.registry import get_model

model = get_model(provider="anthropic", tier="CAPABLE")
print(f"Selected: {model.name} (${model.cost_per_1k_in:.4f}/1k tokens)")
```

**API Docs:** [Model Provider API](./models.md)

---

### "I want to enable caching"

```python
from empathy_os.workflows import SecurityAuditWorkflow

# Cache is auto-configured based on available dependencies
workflow = SecurityAuditWorkflow(enable_cache=True)
result = await workflow.execute(target_path="./src")

print(f"Cache hit rate: {result.cost_report.cache_hit_rate:.1f}%")
print(f"Savings: ${result.cost_report.savings_from_cache:.4f}")
```

**API Docs:** [Cache API](./cache.md)

---

### "I want to track usage and costs"

```bash
# View recent usage
empathy telemetry show

# Calculate savings
empathy telemetry savings --days 30

# Export for analysis
empathy telemetry export --format csv --output usage.csv
```

**API Docs:** [Telemetry API](./telemetry.md)

---

### "I want to build a custom wizard"

```python
from empathy_llm_toolkit.wizards import BaseWizard, WizardConfig
from empathy_llm_toolkit import EmpathyLLM

class MyWizard(BaseWizard):
    def __init__(self, llm: EmpathyLLM | None = None):
        config = WizardConfig(
            name="my-wizard",
            description="Custom wizard for...",
            classification="INTERNAL",
        )
        super().__init__(config=config, llm=llm)

    async def analyze(self, context: dict) -> dict:
        # Your custom logic
        pass
```

**API Docs:** [Base Wizard API](./base-wizard.md)

---

## API Maturity Levels

We use these maturity indicators throughout the documentation:

| Level | Meaning | What to Expect |
|-------|---------|----------------|
| 🟢 **Stable** | Public API, backward compatible | Safe to use in production, won't change |
| 🟡 **Beta** | Public API, may change | Usable, but may require updates in future versions |
| 🟠 **Alpha** | Experimental, incomplete | Use with caution, API may change significantly |
| 🔴 **Private** | Internal use only | May change without notice, use workarounds |
| ⚫ **Planned** | Not yet implemented | See architectural gaps analysis |

---

## Current API Status

Based on [ARCHITECTURAL_GAPS_ANALYSIS.md](../ARCHITECTURAL_GAPS_ANALYSIS.md):

### Meta-Orchestration
- 🟢 `analyze_and_compose()` - Stable, full orchestration flow
- 🔴 `_analyze_task()` - Private (use `analyze_and_compose` instead)
- 🔴 `_select_agents()` - Private (use `analyze_and_compose` instead)
- ⚫ `create_execution_plan()` - Planned (currently embedded in `analyze_and_compose`)

### Memory System
- 🟢 `RedisShortTermMemory` - Stable, has mock mode
- 🟡 `UnifiedMemory` - Beta, API incomplete (see gaps analysis)
- ⚫ `LongTermMemory` - Planned (architecture TBD)

### Model Provider
- 🟢 `get_model()` - Stable, functional interface
- 🟢 `MODEL_REGISTRY` - Stable, module-level dict
- 🟠 `FallbackPolicy` - Alpha, API incomplete
- ⚫ `ModelRegistry` class - Planned (functional interface works for now)

### Workflows
- 🟢 All 10 built-in workflows - Stable
- 🟢 `BaseWorkflow` - Stable for custom workflows

### Cache
- 🟢 Hash-only cache - Stable
- 🟡 Hybrid cache - Beta (requires sentence-transformers)

### Telemetry
- 🟢 CLI commands - Stable
- 🟡 Programmatic API - Beta

---

## API Conventions

### Naming Patterns

**Public Methods:**
- `analyze()` - Analyze input and return structured results
- `execute()` - Execute workflow/operation
- `get_*()` - Retrieve data without side effects
- `create_*()` - Create new objects
- `save_*()` - Persist data

**Private Methods:**
- `_validate_*()` - Internal validation
- `_build_*()` - Internal construction
- `_execute_*()` - Internal execution

### Return Types

**Workflows return structured results:**
```python
@dataclass
class WorkflowResult:
    status: str  # "success" | "partial" | "failed"
    findings: list[dict]
    recommendations: list[str]
    cost_report: CostReport
    metadata: dict
```

**Errors use specific exceptions:**
- `ValueError` - Invalid input
- `FileNotFoundError` - File not found
- `PermissionError` - Insufficient permissions
- `ProviderUnavailableError` - LLM provider unavailable
- `SecurityError` - Security violation (path traversal, etc.)

---

## Migration Notes

### From v3.x to v4.0

**Meta-Orchestration:**
```python
# v3.x - Manual workflow orchestration
workflow1 = SecurityAuditWorkflow()
workflow2 = TestGenerationWorkflow()
# ... manual coordination

# v4.0 - Automatic orchestration
from empathy_os.workflows.orchestrated_release_prep import (
    OrchestratedReleasePrepWorkflow
)
workflow = OrchestratedReleasePrepWorkflow()
# Automatically coordinates multiple agents
```

**Deprecated Wizards:**
```python
# v3.x
from empathy_llm_toolkit.wizards import HealthcareWizard
wizard = HealthcareWizard()  # DeprecationWarning in v4.0

# v4.0 - Use specialized plugin
# pip install empathy-healthcare-wizards
from empathy_healthcare_wizards import HealthcareWizard
```

---

## Common Patterns

### Pattern 1: Run Workflow with Caching

```python
from empathy_os.workflows import SecurityAuditWorkflow

workflow = SecurityAuditWorkflow(enable_cache=True)
result = await workflow.execute(target_path="./src")

# Check results
if result.status == "success":
    print(f"Audit complete: {len(result.findings)} issues")
    print(f"Cache saved: ${result.cost_report.savings_from_cache:.4f}")
```

### Pattern 2: Custom Tier Routing

```python
from empathy_os.workflows import BaseWorkflow, WorkflowConfig

class MyWorkflow(BaseWorkflow):
    def __init__(self):
        config = WorkflowConfig(
            name="my-workflow",
            tier="CAPABLE",  # or "CHEAP", "PREMIUM"
        )
        super().__init__(config=config)
```

### Pattern 3: Error Handling

```python
from empathy_os.workflows import SecurityAuditWorkflow
from empathy_os.models.exceptions import ProviderUnavailableError

workflow = SecurityAuditWorkflow()

try:
    result = await workflow.execute(target_path="./src")
except ProviderUnavailableError as e:
    print(f"All providers unavailable: {e}")
    # Fallback logic
except ValueError as e:
    print(f"Invalid input: {e}")
```

---

## Next Steps

**For Users:**
1. Start with [Quick Start Guide](../guides/QUICK_START.md) (5 minutes)
2. Explore [Common Use Cases](../guides/USE_CASES.md)
3. Review specific API docs for your needs

**For Contributors:**
1. Read [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)
2. Review [ARCHITECTURAL_GAPS_ANALYSIS.md](../ARCHITECTURAL_GAPS_ANALYSIS.md)
3. See [ARCHITECTURE.md](../ARCHITECTURE.md) for system design

---

## Feedback

Found an API that's undocumented or behaves unexpectedly?

- **Issues:** https://github.com/Smart-AI-Memory/empathy-framework/issues
- **Discussions:** https://github.com/Smart-AI-Memory/empathy-framework/discussions
- **Email:** team@smartaimemory.com

---

**Last Updated:** January 16, 2026
**Maintained By:** Documentation Team
**License:** Fair Source 0.9
