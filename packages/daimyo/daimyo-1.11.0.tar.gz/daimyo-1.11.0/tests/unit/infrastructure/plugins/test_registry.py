"""Tests for plugin registry."""


import pytest

from daimyo.domain import PluginExecutionError
from daimyo.infrastructure.plugins import PluginRegistry


class TestPluginRegistry:
    """Test plugin registry functionality."""

    def test_register_plugin(self, mock_plugin):
        """Register a plugin successfully."""
        registry = PluginRegistry()
        registry.register(mock_plugin)

        assert "test.plugin" in registry.list_plugins()
        assert registry.get_plugin("test.plugin") == mock_plugin

    def test_get_plugin_not_found(self):
        """Get plugin that doesn't exist returns None."""
        registry = PluginRegistry()
        assert registry.get_plugin("nonexistent") is None

    def test_list_plugins_empty(self):
        """List plugins when registry is empty."""
        registry = PluginRegistry()
        assert registry.list_plugins() == []

    def test_list_plugins_sorted(self, mock_plugin):
        """List plugins returns sorted names."""
        from daimyo.domain import BasePlugin

        class Plugin2(BasePlugin):
            @property
            def name(self) -> str:
                return "aaa.first"

            @property
            def description(self) -> str:
                return "First alphabetically"

            def is_available(self) -> bool:
                return True

        class Plugin3(BasePlugin):
            @property
            def name(self) -> str:
                return "zzz.last"

            @property
            def description(self) -> str:
                return "Last alphabetically"

            def is_available(self) -> bool:
                return True

        registry = PluginRegistry()

        registry.register(mock_plugin)
        registry.register(Plugin2())
        registry.register(Plugin3())

        plugins = registry.list_plugins()
        assert plugins == ["aaa.first", "test.plugin", "zzz.last"]

    def test_get_enabled_plugins_with_pattern(self, mock_plugin):
        """Get plugins matching enabled patterns."""
        registry = PluginRegistry()
        registry.register(mock_plugin)

        enabled = registry.get_enabled_plugins(["test.*"])
        assert len(enabled) == 1
        assert enabled[0] == mock_plugin

    def test_get_enabled_plugins_no_match(self, mock_plugin):
        """Get plugins with non-matching pattern."""
        registry = PluginRegistry()
        registry.register(mock_plugin)

        enabled = registry.get_enabled_plugins(["git.*"])
        assert len(enabled) == 0

    def test_get_enabled_plugins_empty_patterns(self, mock_plugin):
        """Get plugins with empty patterns list."""
        registry = PluginRegistry()
        registry.register(mock_plugin)

        enabled = registry.get_enabled_plugins([])
        assert len(enabled) == 0

    def test_get_context_providers(self, mock_plugin, mock_plugin_without_context):
        """Get only plugins with get_context method."""
        registry = PluginRegistry()
        registry.register(mock_plugin)
        registry.register(mock_plugin_without_context)

        providers = registry.get_context_providers(["test.*", "other.*"])
        assert len(providers) == 1
        assert providers[0] == mock_plugin

    def test_aggregate_context(self, mock_plugin, sample_merged_scope):
        """Aggregate context from enabled plugins."""
        registry = PluginRegistry()
        registry.register(mock_plugin)

        context = registry.aggregate_context(
            scope=sample_merged_scope, enabled_patterns=["test.*"]
        )

        assert context == {"test_var": "test_value"}

    def test_aggregate_context_plugin_unavailable(self, sample_merged_scope):
        """Skip plugins that are not available."""
        from daimyo.domain import ContextProviderPlugin

        class UnavailablePlugin(ContextProviderPlugin):
            @property
            def name(self) -> str:
                return "test.unavailable"

            @property
            def description(self) -> str:
                return "Unavailable plugin"

            def is_available(self) -> bool:
                return False

            def get_context(self, scope):
                return {"should_not": "appear"}

        registry = PluginRegistry()
        registry.register(UnavailablePlugin())

        context = registry.aggregate_context(
            scope=sample_merged_scope, enabled_patterns=["test.*"]
        )

        assert context == {}

    def test_aggregate_context_plugin_error(self, sample_merged_scope):
        """Wrap plugin exceptions in PluginExecutionError."""
        from daimyo.domain import ContextProviderPlugin

        class FailingPlugin(ContextProviderPlugin):
            @property
            def name(self) -> str:
                return "test.failing"

            @property
            def description(self) -> str:
                return "Failing plugin"

            def is_available(self) -> bool:
                return True

            def get_context(self, scope):
                raise RuntimeError("Plugin failed")

        registry = PluginRegistry()
        registry.register(FailingPlugin())

        with pytest.raises(PluginExecutionError) as exc_info:
            registry.aggregate_context(
                scope=sample_merged_scope, enabled_patterns=["test.*"]
            )

        assert exc_info.value.plugin_name == "test.failing"
        assert isinstance(exc_info.value.original_error, RuntimeError)

    def test_aggregate_context_multiple_plugins(self, sample_merged_scope):
        """Aggregate context from multiple plugins."""
        from daimyo.domain import ContextProviderPlugin

        class Plugin1(ContextProviderPlugin):
            @property
            def name(self) -> str:
                return "plugin1"

            @property
            def description(self) -> str:
                return "First plugin"

            def is_available(self) -> bool:
                return True

            def get_context(self, scope):
                return {"var1": "value1"}

        class Plugin2(ContextProviderPlugin):
            @property
            def name(self) -> str:
                return "plugin2"

            @property
            def description(self) -> str:
                return "Second plugin"

            def is_available(self) -> bool:
                return True

            def get_context(self, scope):
                return {"var2": "value2"}

        registry = PluginRegistry()
        registry.register(Plugin1())
        registry.register(Plugin2())

        context = registry.aggregate_context(
            scope=sample_merged_scope, enabled_patterns=["plugin*"]
        )

        assert context == {"var1": "value1", "var2": "value2"}

    def test_aggregate_context_conflicts(self, sample_merged_scope):
        """Later plugins override conflicting context keys."""
        from daimyo.domain import ContextProviderPlugin

        class Plugin1(ContextProviderPlugin):
            @property
            def name(self) -> str:
                return "plugin1"

            @property
            def description(self) -> str:
                return "First plugin"

            def is_available(self) -> bool:
                return True

            def get_context(self, scope):
                return {"shared": "from_plugin1", "unique1": "value1"}

        class Plugin2(ContextProviderPlugin):
            @property
            def name(self) -> str:
                return "plugin2"

            @property
            def description(self) -> str:
                return "Second plugin"

            def is_available(self) -> bool:
                return True

            def get_context(self, scope):
                return {"shared": "from_plugin2", "unique2": "value2"}

        registry = PluginRegistry()
        registry.register(Plugin1())
        registry.register(Plugin2())

        context = registry.aggregate_context(
            scope=sample_merged_scope, enabled_patterns=["plugin*"]
        )

        assert context["shared"] == "from_plugin2"
        assert context["unique1"] == "value1"
        assert context["unique2"] == "value2"

    def test_register_overwrites_existing(self):
        """Registering same plugin name overwrites."""
        from daimyo.domain import BasePlugin

        class Plugin1(BasePlugin):
            @property
            def name(self) -> str:
                return "test.plugin"

            @property
            def description(self) -> str:
                return "First version"

            def is_available(self) -> bool:
                return True

        class Plugin2(BasePlugin):
            @property
            def name(self) -> str:
                return "test.plugin"

            @property
            def description(self) -> str:
                return "Second version"

            def is_available(self) -> bool:
                return True

        registry = PluginRegistry()
        plugin1_instance = Plugin1()
        plugin2_instance = Plugin2()

        registry.register(plugin1_instance)
        registry.register(plugin2_instance)

        assert len(registry.list_plugins()) == 1
        assert registry.get_plugin("test.plugin") == plugin2_instance
