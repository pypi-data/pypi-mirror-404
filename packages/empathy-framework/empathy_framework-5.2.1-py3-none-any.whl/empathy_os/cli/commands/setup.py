"""Setup commands for initialization and validation.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import sys

from empathy_os.config import EmpathyConfig, _validate_file_path, load_config
from empathy_os.logging_config import get_logger

logger = get_logger(__name__)


def cmd_init(args):
    """Initialize a new Empathy Framework project.

    Creates a configuration file with sensible defaults.

    Args:
        args: Namespace object from argparse with attributes:
            - format (str): Output format ('yaml' or 'json').
            - output (str | None): Output file path.

    Returns:
        None: Creates configuration file at specified path.

    Raises:
        ValueError: If output path is invalid or unsafe.
    """
    config_format = args.format
    output_path = args.output or f"empathy.config.{config_format}"

    # Validate output path to prevent path traversal attacks
    validated_path = _validate_file_path(output_path)

    logger.info(f"Initializing new Empathy Framework project with format: {config_format}")

    # Create default config
    config = EmpathyConfig()

    # Save to file
    if config_format == "yaml":
        config.to_yaml(str(validated_path))
        logger.info(f"Created YAML configuration file: {output_path}")
        logger.info(f"✓ Created YAML configuration: {output_path}")
    elif config_format == "json":
        config.to_json(str(validated_path))
        logger.info(f"Created JSON configuration file: {validated_path}")
        logger.info(f"✓ Created JSON configuration: {validated_path}")

    logger.info("\nNext steps:")
    logger.info(f"  1. Edit {output_path} to customize settings")
    logger.info("  2. Use 'empathy run' to start using the framework")


def cmd_validate(args):
    """Validate a configuration file.

    Loads and validates the specified configuration file.

    Args:
        args: Namespace object from argparse with attributes:
            - config (str): Path to configuration file to validate.

    Returns:
        None: Prints validation result. Exits with code 1 on failure.
    """
    filepath = args.config
    logger.info(f"Validating configuration file: {filepath}")

    try:
        config = load_config(filepath=filepath, use_env=False)
        config.validate()
        logger.info(f"Configuration validation successful: {filepath}")
        logger.info(f"✓ Configuration valid: {filepath}")
        logger.info(f"\n  User ID: {config.user_id}")
        logger.info(f"  Target Level: {config.target_level}")
        logger.info(f"  Confidence Threshold: {config.confidence_threshold}")
        logger.info(f"  Persistence Backend: {config.persistence_backend}")
        logger.info(f"  Metrics Enabled: {config.metrics_enabled}")
    except (OSError, FileNotFoundError) as e:
        # Config file not found or cannot be read
        logger.error(f"Configuration file error: {e}")
        logger.error(f"✗ Cannot read configuration file: {e}")
        sys.exit(1)
    except ValueError as e:
        # Invalid configuration values
        logger.error(f"Configuration validation failed: {e}")
        logger.error(f"✗ Configuration invalid: {e}")
        sys.exit(1)
    except Exception as e:
        # Unexpected errors during config validation
        logger.exception(f"Unexpected error validating configuration: {e}")
        logger.error(f"✗ Configuration invalid: {e}")
        sys.exit(1)
