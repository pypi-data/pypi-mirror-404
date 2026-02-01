"""Smoke tests for quick validation of core functionality.

Run with: pytest -m smoke
These tests should complete in under 30 seconds and validate critical paths.
"""

import pytest

# Mark this file's tests as smoke tests
pytestmark = pytest.mark.smoke


class TestCoreImports:
    """Test that core modules can be imported."""

    def test_import_empathy_os(self):
        """Test main package import."""
        import empathy_os
        assert empathy_os is not None

    def test_import_workflows(self):
        """Test workflows import."""
        from empathy_os import workflows
        assert workflows is not None

    def test_import_cache(self):
        """Test cache import."""
        from empathy_os import cache
        assert cache is not None

    def test_import_meta_workflows(self):
        """Test meta workflows import."""
        from empathy_os import meta_workflows
        assert meta_workflows is not None

    def test_import_memory(self):
        """Test memory import."""
        from empathy_os import memory
        assert memory is not None


class TestCoreClasses:
    """Test core class instantiation."""

    def test_cache_creation(self):
        """Test cache can be created."""
        from empathy_os.cache import create_cache
        cache = create_cache(cache_type="hash")
        assert cache is not None

    def test_workflow_base_import(self):
        """Test workflow base classes."""
        from empathy_os.workflows.base import WorkflowResult
        # WorkflowResult has a different signature - just verify import
        assert WorkflowResult is not None

    def test_template_registry(self):
        """Test template registry loads built-in templates."""
        from empathy_os.meta_workflows import TemplateRegistry
        registry = TemplateRegistry()
        templates = registry.list_templates()
        assert len(templates) >= 5  # Should have built-in templates

    def test_pattern_library(self):
        """Test pattern library instantiation."""
        from empathy_os.pattern_library import PatternLibrary
        library = PatternLibrary()
        assert library is not None


class TestCLI:
    """Test CLI imports."""

    def test_cli_import(self):
        """Test CLI module import."""
        from empathy_os import cli
        assert cli is not None

    def test_cli_app_exists(self):
        """Test CLI app exists."""
        from empathy_os.cli_unified import app
        assert app is not None


class TestConfig:
    """Test configuration and security."""

    def test_validate_file_path(self):
        """Test path validation function exists."""
        from empathy_os.config import _validate_file_path
        # Function exists and works
        assert _validate_file_path is not None
        # Null bytes should be blocked
        with pytest.raises(ValueError, match="null"):
            _validate_file_path("test\x00file.txt")

    def test_config_dataclass(self):
        """Test config dataclass."""
        from empathy_os.config import EmpathyConfig
        config = EmpathyConfig(user_id="test")
        assert config.user_id == "test"


class TestLLMToolkit:
    """Test LLM toolkit modules."""

    def test_hooks_import(self):
        """Test hooks module."""
        from empathy_llm_toolkit.hooks import HookRegistry
        registry = HookRegistry()
        assert registry is not None

    def test_commands_import(self):
        """Test commands module."""
        from empathy_llm_toolkit.commands import CommandRegistry
        CommandRegistry.reset_instance()
        registry = CommandRegistry.get_instance()
        assert registry is not None
        CommandRegistry.reset_instance()

    def test_learning_import(self):
        """Test learning module."""
        from empathy_llm_toolkit.learning import PatternExtractor
        extractor = PatternExtractor()
        assert extractor is not None

    def test_context_import(self):
        """Test context module."""
        from empathy_llm_toolkit.context import ContextManager
        # Should be able to import without error
        assert ContextManager is not None


class TestModelsAndCosts:
    """Test model registry and cost tracking."""

    def test_model_registry(self):
        """Test model registry has models defined."""
        from empathy_os.models.registry import ModelRegistry
        registry = ModelRegistry()
        assert registry is not None

    def test_cost_tracker_import(self):
        """Test cost tracker."""
        from empathy_os.cost_tracker import CostTracker
        tracker = CostTracker()
        assert tracker is not None

    def test_token_estimator(self):
        """Test token estimation."""
        from empathy_os.models.token_estimator import estimate_tokens
        tokens = estimate_tokens("Hello, world!")
        assert tokens > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "smoke"])
