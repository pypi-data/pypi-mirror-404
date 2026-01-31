# Software Development Plugin

> **DEPRECATION NOTICE (January 2026):** The `empathy_software_plugin.wizards` module has been removed. Please use CLI workflows instead.

Production-ready analysis tools for software development.

**Copyright 2025-2026 Smart AI Memory, LLC**
**Licensed under Fair Source 0.9**

## Overview

The Software Development Plugin provides analysis capabilities through CLI workflows.

## Recommended Approach

```bash
# Security analysis
empathy workflow run security-audit --path ./src

# Bug prediction
empathy workflow run bug-predict --path ./src

# Test coverage analysis
empathy workflow run test-coverage --path ./src
```

Or use the Python workflow API:

```python
from empathy_os.workflows import BugPredictWorkflow

workflow = BugPredictWorkflow()
result = await workflow.execute(target_path="./src")
```

## Migration Guide

| Old Wizard | New Approach |
|------------|--------------|
| `EnhancedTestingWizard` | `empathy workflow run test-coverage` |
| `PerformanceProfilingWizard` | `empathy workflow run profile` |
| `SecurityAnalysisWizard` | `empathy workflow run security-audit` |

## Installation

```bash
pip install empathy-framework
```

## Support

- **Documentation:** [docs/](../docs/)
- **Issues:** [GitHub Issues](https://github.com/deepstudyai/empathy/issues)

## License

Copyright 2025-2026 Smart AI Memory, LLC - Licensed under Fair Source 0.9
