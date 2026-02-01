---
description: Install Empathy Framework with pip in 2 minutes. Choose from developer, minimal, or full packages. CLI tools, VSCode extension included.
---

# Installation

Get Empathy Framework installed and configured in about 2 minutes.

---

## Step 1: Install the Package

Choose your installation option:

=== "Recommended (Developer)"

    ```bash
    pip install empathy-framework[developer]
    ```

    Includes: CLI tools, VSCode extension support, all workflows, local telemetry.

=== "Minimal"

    ```bash
    pip install empathy-framework
    ```

    Core functionality only. Add extras later as needed.

=== "Full"

    ```bash
    pip install empathy-framework[full]
    ```

    Everything: LLM providers, healthcare support, webhooks, caching.

=== "Healthcare"

    ```bash
    pip install empathy-framework[healthcare]
    ```

    Includes: FHIR client, HL7 parsing, HIPAA audit logging.

### Verify Installation

```bash
python -c "import empathy_os; print(f'Empathy Framework v{empathy_os.__version__}')"
```

---

## Step 2: Configure an LLM Provider

You need at least one LLM provider. Anthropic (Claude) is recommended.

### Option A: Environment Variable (Quick)

```bash
# Anthropic (recommended)
export ANTHROPIC_API_KEY="sk-ant-..."

# Or OpenAI
export OPENAI_API_KEY="sk-..."

# Or Google
export GOOGLE_API_KEY="..."
```

### Option B: .env File (Persistent)

Create a `.env` file in your project root:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

The framework auto-detects `.env` files.

### Option C: Interactive Setup

```bash
python -m empathy_os.models.cli provider --interactive
```

### Verify Provider

```bash
python -m empathy_os.models.cli provider
```

Expected output:
```
Current provider: anthropic
Available models: claude-opus-4, claude-sonnet-4, claude-haiku-4
API key configured
```

---

## Step 3: Optional - Redis for Memory

Redis enables multi-agent coordination and session persistence. Skip this for now if you just want to try the framework.

=== "macOS (Homebrew)"

    ```bash
    brew install redis
    brew services start redis
    redis-cli ping  # Should return: PONG
    ```

=== "Docker"

    ```bash
    docker run -d -p 6379:6379 --name empathy-redis redis:alpine
    ```

=== "Skip for Now"

    The framework works without Redis (falls back to in-memory storage).

    You can add Redis later when you need:

    - Multi-agent coordination
    - Session persistence
    - Pattern staging

See [Redis Setup](redis-setup.md) for production configuration.

---

## Troubleshooting

### "No API key configured"

```bash
# Check your environment
env | grep API_KEY

# Set it
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify
python -m empathy_os.models.cli provider --check
```

### "ModuleNotFoundError: empathy_os"

```bash
# Reinstall
pip install --upgrade empathy-framework[developer]

# Or for development
pip install -e .[dev]
```

### Python version too old

```bash
python --version  # Need 3.10+

# Use pyenv to manage versions
pyenv install 3.11
pyenv local 3.11
```

---

## Next Step

You're installed! Continue to [First Steps](first-steps.md) to run your first workflow.
