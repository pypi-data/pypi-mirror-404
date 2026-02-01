"""Tests for Plugin Registry

Tests the plugin auto-discovery and management system.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock, patch

import pytest

from empathy_os.plugins.base import BasePlugin, BaseWorkflow, PluginValidationError
from empathy_os.plugins.registry import PluginRegistry, get_global_registry


@dataclass
class MockPluginMetadata:
    """Mock plugin metadata for testing"""

    name: str = "test_plugin"
    domain: str = "testing"
    version: str = "1.0.0"
    description: str = "Test plugin"


class MockWorkflow(BaseWorkflow):
    """Mock wizard for testing"""

    def __init__(self, workflow_id: str, empathy_level: int = 4):
        self.workflow_id = workflow_id
        self._level = empathy_level
        self._name = f"Test Wizard {workflow_id}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def level(self) -> int:
        return self._level

    def get_required_context(self) -> list[str]:
        """Return empty list for mock wizard"""
        return []

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        return {"predictions": [], "recommendations": [], "confidence": 0.9}


class MockPlugin(BasePlugin):
    """Mock plugin for testing"""

    def __init__(self, name: str = "test", domain: str = "testing", version: str = "1.0.0"):
        self._metadata = MockPluginMetadata(name=name, domain=domain, version=version)
        self._custom_workflows: dict[str, BaseWorkflow] = {}
        super().__init__()

    def get_metadata(self) -> MockPluginMetadata:
        return self._metadata

    def register_workflows(self) -> dict[str, BaseWorkflow]:
        """Return custom wizards added via add_workflow"""
        return self._custom_workflows

    def initialize(self) -> None:
        """Override to use custom wizards"""
        if self._initialized:
            return
        self._workflows = self._custom_workflows
        self._initialized = True

    def add_workflow(self, workflow_id: str, wizard: BaseWorkflow):
        """Add a wizard to this mock plugin"""
        self._custom_workflows[workflow_id] = wizard
        if self._initialized:
            self._workflows[workflow_id] = wizard

    def list_workflows(self) -> list[str]:
        return list(self._custom_workflows.keys())

    def get_workflow(self, workflow_id: str):
        return self._custom_workflows.get(workflow_id)

    def get_workflow_info(self, workflow_id: str) -> dict[str, Any]:
        wizard = self._custom_workflows.get(workflow_id)
        if wizard:
            return {
                "id": workflow_id,
                "name": wizard.name,
                "empathy_level": wizard.level,
                "domain": self._metadata.domain,
            }
        return None


class TestPluginRegistryBasics:
    """Test basic registry operations"""

    def test_registry_initialization(self):
        """Test registry can be created"""
        registry = PluginRegistry()
        assert registry is not None
        assert registry._plugins == {}
        assert registry._auto_discovered is False

    def test_register_plugin(self):
        """Test manual plugin registration"""
        registry = PluginRegistry()
        plugin = MockPlugin(name="test", domain="software")

        registry.register_plugin("test", plugin)

        assert "test" in registry._plugins
        assert registry._plugins["test"] == plugin

    def test_register_plugin_without_name(self):
        """Test registering plugin with invalid metadata raises error"""
        registry = PluginRegistry()
        plugin = MockPlugin(name="", domain="software")  # Empty name

        with pytest.raises(PluginValidationError, match="missing 'name'"):
            registry.register_plugin("test", plugin)

    def test_register_plugin_without_domain(self):
        """Test registering plugin without domain raises error"""
        registry = PluginRegistry()
        plugin = MockPlugin(name="test", domain="")  # Empty domain

        with pytest.raises(PluginValidationError, match="missing 'domain'"):
            registry.register_plugin("test", plugin)

    def test_get_plugin(self):
        """Test retrieving a registered plugin"""
        registry = PluginRegistry()
        plugin = MockPlugin(name="test", domain="software")
        registry.register_plugin("test", plugin)

        retrieved = registry.get_plugin("test")

        assert retrieved == plugin
        assert retrieved._initialized is True  # Should be initialized on retrieval

    def test_get_nonexistent_plugin(self):
        """Test retrieving non-existent plugin returns None"""
        registry = PluginRegistry()

        result = registry.get_plugin("nonexistent")

        assert result is None

    def test_list_plugins(self):
        """Test listing all registered plugins"""
        registry = PluginRegistry()
        plugin1 = MockPlugin(name="plugin1", domain="software")
        plugin2 = MockPlugin(name="plugin2", domain="healthcare")

        registry.register_plugin("plugin1", plugin1)
        registry.register_plugin("plugin2", plugin2)

        plugins = registry.list_plugins()

        assert len(plugins) == 2
        assert "plugin1" in plugins
        assert "plugin2" in plugins


class TestPluginRegistryAutoDiscovery:
    """Test auto-discovery functionality"""

    @patch("empathy_os.plugins.registry.entry_points")
    def test_auto_discover_no_plugins(self, mock_entry_points):
        """Test auto-discovery with no plugins"""
        mock_entry_points.return_value = []

        registry = PluginRegistry()
        registry.auto_discover()

        assert registry._auto_discovered is True
        assert len(registry._plugins) == 0

    @patch("empathy_os.plugins.registry.entry_points")
    def test_auto_discover_with_plugins(self, mock_entry_points):
        """Test auto-discovery successfully loads plugins"""
        # Create mock entry point
        mock_ep = Mock()
        mock_ep.name = "test_plugin"
        mock_ep.load.return_value = MockPlugin

        mock_entry_points.return_value = [mock_ep]

        registry = PluginRegistry()
        registry.auto_discover()

        assert registry._auto_discovered is True
        assert len(registry._plugins) == 1
        assert "test_plugin" in registry._plugins

    @patch("empathy_os.plugins.registry.entry_points")
    def test_auto_discover_handles_load_failures(self, mock_entry_points):
        """Test auto-discovery gracefully handles plugin load failures"""
        # Create mock entry point that fails to load
        mock_ep = Mock()
        mock_ep.name = "broken_plugin"
        mock_ep.load.side_effect = ImportError("Module not found")

        mock_entry_points.return_value = [mock_ep]

        registry = PluginRegistry()
        registry.auto_discover()  # Should not raise exception

        assert registry._auto_discovered is True
        assert len(registry._plugins) == 0  # Broken plugin not added

    @patch("empathy_os.plugins.registry.entry_points")
    def test_auto_discover_only_runs_once(self, mock_entry_points):
        """Test auto-discovery only runs once"""
        mock_entry_points.return_value = []

        registry = PluginRegistry()
        registry.auto_discover()
        registry.auto_discover()  # Call again

        # entry_points should only be called once
        assert mock_entry_points.call_count == 1


class TestPluginRegistryWizards:
    """Test wizard-related functionality"""

    def test_list_all_workflows(self):
        """Test listing all wizards from all plugins"""
        registry = PluginRegistry()

        plugin1 = MockPlugin(name="plugin1", domain="software")
        plugin1.add_workflow("wizard1", MockWorkflow("wizard1"))
        plugin1.add_workflow("wizard2", MockWorkflow("wizard2"))

        plugin2 = MockPlugin(name="plugin2", domain="healthcare")
        plugin2.add_workflow("wizard3", MockWorkflow("wizard3"))

        registry.register_plugin("plugin1", plugin1)
        registry.register_plugin("plugin2", plugin2)

        all_workflows = registry.list_all_workflows()

        assert len(all_workflows) == 2
        assert "plugin1" in all_workflows
        assert "plugin2" in all_workflows
        assert len(all_workflows["plugin1"]) == 2
        assert len(all_workflows["plugin2"]) == 1

    def test_get_workflow(self):
        """Test retrieving a specific wizard"""
        registry = PluginRegistry()

        plugin = MockPlugin(name="test", domain="software")
        wizard = MockWorkflow("test_wizard")
        plugin.add_workflow("test_wizard", wizard)

        registry.register_plugin("test", plugin)

        retrieved = registry.get_workflow("test", "test_wizard")

        assert retrieved == wizard

    def test_get_workflow_from_nonexistent_plugin(self):
        """Test getting wizard from non-existent plugin returns None"""
        registry = PluginRegistry()

        result = registry.get_workflow("nonexistent", "wizard")

        assert result is None

    def test_get_workflow_info(self):
        """Test retrieving wizard information"""
        registry = PluginRegistry()

        plugin = MockPlugin(name="test", domain="software")
        wizard = MockWorkflow("test_wizard", empathy_level=4)
        plugin.add_workflow("test_wizard", wizard)

        registry.register_plugin("test", plugin)

        info = registry.get_workflow_info("test", "test_wizard")

        assert info is not None
        assert info["id"] == "test_wizard"
        assert info["empathy_level"] == 4

    def test_find_workflows_by_level(self):
        """Test finding wizards by empathy level"""
        registry = PluginRegistry()

        plugin1 = MockPlugin(name="plugin1", domain="software")
        plugin1.add_workflow("level4_wizard", MockWorkflow("level4", empathy_level=4))
        plugin1.add_workflow("level5_wizard", MockWorkflow("level5", empathy_level=5))

        plugin2 = MockPlugin(name="plugin2", domain="healthcare")
        plugin2.add_workflow("another_level4", MockWorkflow("level4_2", empathy_level=4))

        registry.register_plugin("plugin1", plugin1)
        registry.register_plugin("plugin2", plugin2)

        level4_workflows = registry.find_workflows_by_level(4)

        assert len(level4_workflows) == 2
        for wizard_info in level4_workflows:
            assert wizard_info["empathy_level"] == 4
            assert "plugin" in wizard_info

    def test_find_workflows_by_domain(self):
        """Test finding wizards by domain"""
        registry = PluginRegistry()

        plugin1 = MockPlugin(name="plugin1", domain="software")
        plugin1.add_workflow("wizard1", MockWorkflow("wizard1"))

        plugin2 = MockPlugin(name="plugin2", domain="software")
        plugin2.add_workflow("wizard2", MockWorkflow("wizard2"))

        plugin3 = MockPlugin(name="plugin3", domain="healthcare")
        plugin3.add_workflow("wizard3", MockWorkflow("wizard3"))

        registry.register_plugin("plugin1", plugin1)
        registry.register_plugin("plugin2", plugin2)
        registry.register_plugin("plugin3", plugin3)

        software_workflows = registry.find_workflows_by_domain("software")

        assert len(software_workflows) == 2
        for wizard_info in software_workflows:
            assert wizard_info["domain"] == "software"
            assert "plugin" in wizard_info


class TestPluginRegistryStatistics:
    """Test statistics functionality"""

    def test_get_statistics_empty_registry(self):
        """Test statistics for empty registry"""
        registry = PluginRegistry()

        stats = registry.get_statistics()

        assert stats["total_plugins"] == 0
        assert stats["total_workflows"] == 0
        assert "workflows_by_level" in stats

    def test_get_statistics_with_plugins(self):
        """Test statistics with registered plugins"""
        registry = PluginRegistry()

        plugin1 = MockPlugin(name="plugin1", domain="software", version="1.0.0")
        plugin1.add_workflow("wizard1", MockWorkflow("wizard1", empathy_level=4))
        plugin1.add_workflow("wizard2", MockWorkflow("wizard2", empathy_level=5))

        plugin2 = MockPlugin(name="plugin2", domain="healthcare", version="2.0.0")
        plugin2.add_workflow("wizard3", MockWorkflow("wizard3", empathy_level=4))

        registry.register_plugin("plugin1", plugin1)
        registry.register_plugin("plugin2", plugin2)

        stats = registry.get_statistics()

        assert stats["total_plugins"] == 2
        assert stats["total_workflows"] == 3
        assert len(stats["plugins"]) == 2

        # Check plugin info
        plugin_names = [p["name"] for p in stats["plugins"]]
        assert "plugin1" in plugin_names
        assert "plugin2" in plugin_names

        # Check wizards by level
        assert stats["workflows_by_level"]["level_4"] == 2
        assert stats["workflows_by_level"]["level_5"] == 1


class TestGlobalRegistry:
    """Test global registry singleton"""

    def test_get_global_registry(self):
        """Test getting global registry instance"""
        registry1 = get_global_registry()
        registry2 = get_global_registry()

        # Should return same instance
        assert registry1 is registry2

    @patch("empathy_os.plugins.registry._global_registry", None)
    def test_global_registry_auto_discovers(self):
        """Test global registry auto-discovers on first access"""
        with patch("empathy_os.plugins.registry.entry_points") as mock_ep:
            mock_ep.return_value = []

            registry = get_global_registry()

            assert registry._auto_discovered is True


class TestPluginRegistryEdgeCases:
    """Test edge cases and error conditions"""

    def test_register_plugin_with_get_metadata_error(self):
        """Test registering plugin that raises error in get_metadata"""
        registry = PluginRegistry()

        plugin = Mock()
        plugin.get_metadata.side_effect = Exception("Metadata error")

        with pytest.raises(PluginValidationError, match="Invalid plugin metadata"):
            registry.register_plugin("broken", plugin)

    def test_list_plugins_triggers_auto_discover(self):
        """Test that list_plugins triggers auto-discovery"""
        with patch("empathy_os.plugins.registry.entry_points") as mock_ep:
            mock_ep.return_value = []

            registry = PluginRegistry()
            assert registry._auto_discovered is False

            registry.list_plugins()

            assert registry._auto_discovered is True

    def test_get_plugin_triggers_auto_discover(self):
        """Test that get_plugin triggers auto-discovery"""
        with patch("empathy_os.plugins.registry.entry_points") as mock_ep:
            mock_ep.return_value = []

            registry = PluginRegistry()
            assert registry._auto_discovered is False

            registry.get_plugin("test")

            assert registry._auto_discovered is True

    def test_find_workflows_with_none_info(self):
        """Test finding wizards when get_workflow_info returns None"""
        registry = PluginRegistry()

        plugin = MockPlugin(name="test", domain="software")
        # Don't add any wizards, so get_workflow_info will return None
        plugin.add_workflow("invalid", MockWorkflow("invalid"))

        # Make get_workflow_info return None
        plugin.get_workflow_info = Mock(return_value=None)

        registry.register_plugin("test", plugin)

        # Should not crash, just return empty list
        results = registry.find_workflows_by_level(4)
        assert results == []

    def test_get_workflow_info_from_nonexistent_plugin(self):
        """Test get_workflow_info from non-existent plugin returns None"""
        registry = PluginRegistry()

        result = registry.get_workflow_info("nonexistent", "wizard")

        assert result is None
