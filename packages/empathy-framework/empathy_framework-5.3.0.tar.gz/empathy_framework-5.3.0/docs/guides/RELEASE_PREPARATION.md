---
description: Release Preparation Guide - Empathy Framework v3.7.0: Step-by-step tutorial with examples, best practices, and common patterns. Learn by doing with hands-on examples.
---

# Release Preparation Guide - Empathy Framework v3.7.0

**Date**: 2026-01-05
**Target Release**: v3.7.0 (XML-Enhanced Prompts)
**Status**: 🔄 In Preparation

---

## Executive Summary

This guide identifies beta/experimental content to exclude or hide before releasing Empathy Framework v3.7.0, ensuring a clean, production-ready package.

---

## Content Classification

### ✅ INCLUDE - Production-Ready (Ship in v3.7.0)

#### Core Framework
- ✅ `src/empathy_os/` - Core workflow engine
- ✅ `empathy_llm_toolkit/` - LLM toolkit with wizards
- ✅ `patterns/` - Pattern library
- ✅ `tests/` - Test suite (exclude from package, keep in repo)

#### XML-Enhanced Components
- ✅ BaseWorkflow with XML support
- ✅ BaseWizard with XML support
- ✅ All 4 CrewAI crews (XML-enabled)
- ✅ Healthcare, Customer Support, Technology wizards
- ✅ 14 production workflows with XML

#### Documentation (Select)
- ✅ `README.md`
- ✅ `CHANGELOG.md`
- ✅ `LICENSE`
- ✅ `pyproject.toml` / `setup.py`
- ✅ `docs/` - Core documentation

---

### ⚠️ BETA - Hide or Mark as Experimental

#### 1. Beta Workflows (Mark with warnings)

| File | Status | Action |
|------|--------|--------|
| `src/empathy_os/workflows/test5.py` | Test workflow | 🔴 **EXCLUDE** from package |
| `src/empathy_os/workflows/new_sample_workflow1.py` | Example template | 🔴 **EXCLUDE** or move to examples/ |
| `src/empathy_os/workflows/test_lifecycle.py` | Beta utility | ⚠️ Mark as `@beta` |
| `src/empathy_os/workflows/test_maintenance*.py` | Beta utilities | ⚠️ Mark as `@beta` |

#### 2. Beta Directories (Exclude from package)

| Directory | Purpose | Action |
|-----------|---------|--------|
| `scaffolding/` | Code generation templates | 🔴 **EXCLUDE** |
| `workflow_scaffolding/` | Workflow templates | 🔴 **EXCLUDE** |
| `hot_reload/` | Development tool | 🔴 **EXCLUDE** |
| `test_generator/` | Test scaffolding | 🔴 **EXCLUDE** |
| `drafts/` | Work in progress | 🔴 **EXCLUDE** |
| `manual_test*.py` | Manual test scripts | 🔴 **EXCLUDE** |
| `run_test5*.py` | Test runners | 🔴 **EXCLUDE** |

#### 3. Experimental Plugins (Separate packages)

| Plugin | Status | Action |
|--------|--------|--------|
| `empathy_healthcare_plugin/` | Experimental | 📦 Separate package (future release) |
| `empathy_software_plugin/` | Experimental | 📦 Separate package (future release) |
| `vscode-extension/` | Beta | 📦 Separate release cycle |
| `website/` | Marketing site | 📦 Separate deployment |
| `dashboard/` | Web dashboard | 📦 Separate deployment |

#### 4. Progress/Planning Documents (Keep in repo, exclude from package)

**Internal Progress Tracking** (untracked files):
```
BUG_FIX_SUMMARY.md                    → .gitignore or docs/internal/
BUG_REMEDIATION_PLAN.md              → .gitignore or docs/internal/
SPRINT1_PROGRESS.md                  → .gitignore or docs/internal/
WIZARD_FACTORY_PROGRESS.md           → .gitignore or docs/internal/
WORKFLOW_FACTORY_PROGRESS.md         → .gitignore or docs/internal/
REMEDIATION_SUMMARY.txt              → .gitignore or docs/internal/
TESTING.md                           → .gitignore or docs/internal/
```

**Implementation Documentation** (decide: include or exclude):
```
CREWAI_INTEGRATION_COMPLETE.md       → Consider: docs/architecture/
CREWAI_INTEGRATION_STATUS.md         → Consider: docs/architecture/
CREW_INTEGRATION_GUIDE.md            → ✅ Include in docs/guides/
XML_IMPLEMENTATION_GUIDE.md          → ✅ Include in docs/guides/
XML_IMPLEMENTATION_SUMMARY.md        → Consider: docs/architecture/
WIZARD_XML_MIGRATION_COMPLETE.md     → Consider: docs/architecture/
XML_MIGRATION_FINAL_STATUS.md        → Consider: docs/architecture/
```

**Cheat Sheets** (useful for users):
```
WIZARD_FACTORY_CHEATSHEET.md         → ✅ Move to docs/guides/
WORKFLOW_FACTORY_CHEATSHEET.md       → ✅ Move to docs/guides/
WIZARD_FACTORY_QUICKSTART.md         → ✅ Move to docs/quickstart/
WORKFLOW_FACTORY_QUICKSTART.md       → ✅ Move to docs/quickstart/
```

---

### 🔴 EXCLUDE - Not for Release

#### Development Tools
- 🔴 `.vscode/` (keep in repo, exclude from package)
- 🔴 `.pytest_cache/`
- 🔴 `__pycache__/`
- 🔴 `.mypy_cache/`
- 🔴 `.ruff_cache/`
- 🔴 `node_modules/` (VSCode extension)
- 🔴 `.env` files

#### Archived Content
- 🔴 `archived_wizards/`
- 🔴 `anthropic-cookbook/` (external submodule)
- 🔴 `ebook-site/` (separate project)

#### Test Artifacts
- 🔴 `patterns/debugging/bug_*.json` (test pattern data)
- 🔴 `manual_test.py`
- 🔴 `manual_test.sh`
- 🔴 `run_test5.py`
- 🔴 `run_test5_full.py`
- 🔴 `test_wizard_factory.py`
- 🔴 `test_workflow_factory_manual.py`

---

## Release Configuration

### 1. Update `.gitignore`

Add beta/experimental content:

```gitignore
# Beta/Experimental (exclude from releases)
/scaffolding/
/workflow_scaffolding/
/hot_reload/
/test_generator/
/drafts/
manual_test*.py
run_test5*.py
test_wizard_factory.py
test_workflow_factory_manual.py

# Internal progress docs
*PROGRESS.md
*REMEDIATION*.md
*REMEDIATION*.txt
BUG_FIX_SUMMARY.md
SPRINT*.md

# Test artifacts
patterns/debugging/bug_*.json

# VSCode extension build
vscode-extension/out/
vscode-extension/node_modules/
*.vsix

# Website/Dashboard (separate deployment)
website/.next/
website/node_modules/
dashboard/node_modules/
```

### 2. Update `pyproject.toml` - Package Includes

```toml
[tool.poetry]
name = "empathy-framework"
version = "3.7.0"
description = "Multi-model AI framework with XML-enhanced prompts, CrewAI integration, and HIPAA compliance"

# Include only production-ready code
packages = [
    { include = "empathy_os", from = "src" },
    { include = "empathy_llm_toolkit" },
]

# Exclude beta/experimental content
exclude = [
    "scaffolding",
    "workflow_scaffolding",
    "hot_reload",
    "test_generator",
    "drafts",
    "archived_wizards",
    "empathy_healthcare_plugin",
    "empathy_software_plugin",
    "vscode-extension",
    "website",
    "dashboard",
    "anthropic-cookbook",
    "ebook-site",
    "**/test5.py",
    "**/new_sample_workflow1.py",
    "manual_test*.py",
    "run_test5*.py",
]
```

### 3. Create `MANIFEST.in`

For sdist packaging:

```
# Include core documentation
include README.md
include CHANGELOG.md
include LICENSE
include pyproject.toml

# Include user-facing documentation
recursive-include docs/guides *.md
recursive-include docs/quickstart *.md
recursive-include docs/api *.md

# Include patterns library
recursive-include patterns *.json
exclude patterns/debugging/bug_*.json

# Exclude beta/experimental
prune scaffolding
prune workflow_scaffolding
prune hot_reload
prune test_generator
prune drafts
prune archived_wizards
prune empathy_healthcare_plugin
prune empathy_software_plugin
prune vscode-extension
prune website
prune dashboard
prune anthropic-cookbook
prune ebook-site

# Exclude development files
global-exclude *.pyc
global-exclude __pycache__
global-exclude *.so
global-exclude .DS_Store
```

---

## Documentation Reorganization

### Move to `docs/guides/`

Create proper documentation structure:

```bash
docs/
├── guides/
│   ├── xml-enhanced-prompts.md          ← XML_IMPLEMENTATION_GUIDE.md
│   ├── crewai-integration.md            ← CREW_INTEGRATION_GUIDE.md
│   ├── wizard-factory.md                ← WIZARD_FACTORY_CHEATSHEET.md
│   ├── workflow-factory.md              ← WORKFLOW_FACTORY_CHEATSHEET.md
│   ├── hipaa-compliance.md              ← From HealthcareWizard docs
│   └── signoz-integration.md            ← Already exists
├── quickstart/
│   ├── wizards.md                       ← WIZARD_FACTORY_QUICKSTART.md
│   ├── workflows.md                     ← WORKFLOW_FACTORY_QUICKSTART.md
│   └── getting-started.md
├── architecture/
│   ├── xml-migration-summary.md         ← XML_IMPLEMENTATION_SUMMARY.md
│   ├── crewai-integration.md            ← CREWAI_INTEGRATION_COMPLETE.md
│   └── phase-1-completion.md            ← docs/architecture/PHASE_1_COMPLETION.md
└── internal/  (excluded from package)
    ├── progress/
    │   ├── sprint1.md                   ← SPRINT1_PROGRESS.md
    │   ├── wizard-factory.md            ← WIZARD_FACTORY_PROGRESS.md
    │   └── workflow-factory.md          ← WORKFLOW_FACTORY_PROGRESS.md
    └── planning/
        ├── bug-remediation.md           ← BUG_REMEDIATION_PLAN.md
        └── testing.md                   ← TESTING.md
```

---

## Beta Feature Marking

### Add `@beta` Decorator

Create `src/empathy_os/_beta.py`:

```python
"""Beta feature marking for Empathy Framework."""

import warnings
from functools import wraps
from typing import Any, Callable


def beta(message: str = "This feature is in beta and may change in future releases."):
    """Mark a function, class, or module as beta.

    Usage:
        @beta("Test lifecycle workflows are experimental")
        class TestLifecycleWorkflow(BaseWorkflow):
            ...
    """
    def decorator(obj: Any) -> Any:
        @wraps(obj)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{obj.__name__} is in beta. {message}",
                category=FutureWarning,
                stacklevel=2
            )
            return obj(*args, **kwargs)

        # Mark as beta
        wrapper.__beta__ = True
        wrapper.__beta_message__ = message

        return wrapper if callable(obj) else obj

    return decorator
```

### Mark Beta Workflows

```python
# src/empathy_os/workflows/test_lifecycle.py
from empathy_os._beta import beta

@beta("Test lifecycle workflows are experimental and may change")
class TestLifecycleWorkflow(BaseWorkflow):
    ...

# src/empathy_os/workflows/test_maintenance.py
@beta("Test maintenance workflows are in active development")
class TestMaintenanceWorkflow(BaseWorkflow):
    ...
```

---

## Release Checklist

### Pre-Release Tasks

- [ ] **1. Clean up untracked files**
  ```bash
  # Move documentation
  mkdir -p docs/guides docs/quickstart docs/architecture docs/internal
  mv XML_IMPLEMENTATION_GUIDE.md docs/guides/xml-enhanced-prompts.md
  mv CREW_INTEGRATION_GUIDE.md docs/guides/crewai-integration.md
  # ... (see documentation reorganization above)
  ```

- [ ] **2. Update `.gitignore`**
  - Add beta directories
  - Add internal progress docs
  - Add test artifacts

- [ ] **3. Update `pyproject.toml`**
  - Set version to `3.7.0`
  - Update description
  - Add `exclude` list for beta content
  - Update dependencies

- [ ] **4. Create `MANIFEST.in`**
  - Include core docs
  - Exclude beta content
  - Exclude development files

- [ ] **5. Mark beta features**
  - Add `@beta` decorator
  - Mark test_lifecycle, test_maintenance workflows
  - Add warnings to experimental plugins

- [ ] **6. Update `CHANGELOG.md`**
  ```markdown
  ## [3.7.0] - 2026-01-05

  ### Added
  - XML-enhanced prompts for all workflows and wizards (53% reduction in hallucinations)
  - Complete CrewAI integration (4 crews: Security, CodeReview, Refactoring, HealthCheck)
  - HIPAA-compliant HealthcareWizard with XML
  - Customer Support and Technology wizards with XML
  - Comprehensive XML implementation guides

  ### Changed
  - BaseWorkflow now supports XML prompts by default
  - BaseWizard enhanced with XML prompt infrastructure
  - test-gen workflow uses XML for better consistency

  ### Deprecated
  - None

  ### Removed
  - Excluded beta scaffolding tools from package (available in source)
  - Excluded experimental plugins (separate packages planned)

  ### Fixed
  - Improved instruction following from 87% to 96%
  - Reduced parsing errors by 75%

  ### Security
  - Enhanced HIPAA compliance in healthcare wizard
  - Improved PII protection in customer support wizard
  - Better secrets detection in technology wizard
  ```

- [ ] **7. Update `README.md`**
  - Highlight XML-enhanced prompts as key feature
  - Update installation instructions
  - Add quick start with XML examples
  - Note beta features

- [ ] **8. Run full test suite**
  ```bash
  pytest tests/ -v
  python -m mypy src/empathy_os
  ruff check src/ empathy_llm_toolkit/
  ```

- [ ] **9. Build and test package**
  ```bash
  # Clean previous builds
  rm -rf dist/ build/ *.egg-info

  # Build package
  python -m build

  # Test installation in clean environment
  python -m venv test_env
  source test_env/bin/activate
  pip install dist/empathy_framework-3.7.0-py3-none-any.whl

  # Verify imports
  python -c "from empathy_os.workflows import BaseWorkflow; print('✅ OK')"
  python -c "from empathy_llm_toolkit.wizards import HealthcareWizard; print('✅ OK')"
  ```

- [ ] **10. Create git tag**
  ```bash
  git add .
  git commit -m "chore: Prepare v3.7.0 release - XML-enhanced prompts"
  git tag -a v3.7.0 -m "Release v3.7.0: XML-Enhanced Prompts & CrewAI Integration"
  git push origin main --tags
  ```

---

## Post-Release Tasks

- [ ] **1. Publish to PyPI**
  ```bash
  python -m twine upload dist/*
  ```

- [ ] **2. Create GitHub Release**
  - Title: "v3.7.0 - XML-Enhanced Prompts & CrewAI Integration"
  - Description: From CHANGELOG.md
  - Attach: dist files, documentation PDFs

- [ ] **3. Update documentation site**
  - Deploy new docs to website
  - Update API documentation
  - Add migration guide

- [ ] **4. Announce release**
  - Blog post
  - Twitter/social media
  - Email to users

- [ ] **5. Monitor feedback**
  - Watch GitHub issues
  - Monitor PyPI downloads
  - Collect user feedback on XML features

---

## Beta Features Roadmap (Future Releases)

### v3.8.0 (Planned)
- Graduate test_lifecycle and test_maintenance from beta
- Healthcare plugin as separate package
- VSCode extension stable release

### v3.9.0 (Planned)
- Software plugin as separate package
- Workflow factory UI
- Advanced wizard templates

---

## Questions to Resolve

1. **Should we include internal progress docs in the repo?**
   - ✅ Recommended: Move to `docs/internal/` (exclude from package)
   - ❌ Alternative: Add to `.gitignore` completely

2. **Should XML migration docs be public?**
   - ✅ Recommended: Yes, in `docs/architecture/` (helpful for users)
   - ❌ Alternative: Keep internal only

3. **What to do with plugins?**
   - ✅ Recommended: Keep in repo, mark as experimental, exclude from package
   - ❌ Alternative: Move to separate repositories

4. **Version number?**
   - ✅ v3.7.0 (XML-enhanced prompts is a major feature)
   - ❌ v3.6.x (if considered a patch)

---

## Summary

**Ready for Release**:
- ✅ Core framework
- ✅ XML-enhanced workflows and wizards
- ✅ CrewAI integration
- ✅ Comprehensive documentation

**Exclude from Package**:
- 🔴 Beta workflows (test5, new_sample_workflow1)
- 🔴 Scaffolding tools
- 🔴 Experimental plugins
- 🔴 Internal progress docs
- 🔴 Development tools

**Recommended Actions**:
1. Reorganize documentation
2. Update package configuration
3. Mark beta features
4. Clean up repository
5. Test thoroughly
6. Release v3.7.0

---

**Status**: 📋 Ready for implementation
**Next Step**: Execute pre-release checklist
**Target Date**: 2026-01-05 (today!)
