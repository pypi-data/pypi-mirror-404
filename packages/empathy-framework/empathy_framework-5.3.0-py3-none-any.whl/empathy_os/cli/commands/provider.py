"""Provider configuration commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from pathlib import Path

from empathy_os.config import _validate_file_path
from empathy_os.logging_config import get_logger

logger = get_logger(__name__)


def cmd_provider_show(args):
    """Show current provider configuration (Anthropic-only as of v5.0.0).

    Args:
        args: Namespace object from argparse (no additional attributes used).

    Returns:
        None: Prints Anthropic provider configuration and model mappings.
    """
    from empathy_os.models import MODEL_REGISTRY
    from empathy_os.models.provider_config import ProviderConfig

    print("\n" + "=" * 60)
    print("Provider Configuration (Claude-Native v5.0.0)")
    print("=" * 60)

    # Check for Anthropic API key
    config = ProviderConfig.auto_detect()
    if config.available_providers:
        print("\n✓ ANTHROPIC_API_KEY detected")
    else:
        print("\n⚠️  ANTHROPIC_API_KEY not detected")
        print("   Set your API key: export ANTHROPIC_API_KEY='your-key-here'")
        print("   Get key at: https://console.anthropic.com/settings/keys")

    print("\nProvider: anthropic")

    # Show Anthropic models
    print("\nModel mapping:")
    anthropic_models = MODEL_REGISTRY.get("anthropic", {})
    for tier in ["cheap", "capable", "premium"]:
        model_info = anthropic_models.get(tier)
        if model_info:
            cost = f"${model_info.input_cost_per_million:.2f}/${model_info.output_cost_per_million:.2f} per M tokens"
            print(f"  {tier:8} → {model_info.id:40} {cost}")

    print()


def cmd_provider_set(args):
    """Set default provider (Anthropic-only as of v5.0.0).

    Args:
        args: Namespace object from argparse with attributes:
            - name (str): Provider name to set as default (must be 'anthropic').

    Returns:
        None: Saves provider to .empathy/workflows.yaml.

    Raises:
        SystemExit: If provider is not 'anthropic'.
    """
    import sys

    import yaml

    provider = args.name

    # Validate provider is Anthropic
    if provider.lower() != "anthropic":
        print(f"❌ Error: Provider '{provider}' is not supported.")
        print("   Empathy Framework is now Claude-native (v5.0.0).")
        print("   Only 'anthropic' provider is available.")
        print("   See docs/CLAUDE_NATIVE.md for migration guide.")
        sys.exit(1)

    workflows_path = Path(".empathy/workflows.yaml")

    # Load existing config or create new
    if workflows_path.exists():
        with open(workflows_path) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
        workflows_path.parent.mkdir(parents=True, exist_ok=True)

    config["default_provider"] = provider

    validated_workflows_path = _validate_file_path(str(workflows_path))
    with open(validated_workflows_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Default provider set to: {provider}")
    print(f"  Saved to: {validated_workflows_path}")
