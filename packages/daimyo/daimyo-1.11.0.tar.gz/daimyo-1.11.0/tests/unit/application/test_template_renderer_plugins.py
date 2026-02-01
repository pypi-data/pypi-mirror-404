"""Tests for template renderer with plugin integration."""


from daimyo.application.templating import TemplateRenderer


class TestTemplateRendererWithPlugins:
    """Test template renderer with plugin context."""

    def test_render_with_plugin_context(
        self, mock_settings_with_plugins, plugin_registry_with_mocks, sample_merged_scope
    ):
        """Render template using plugin-provided context."""
        renderer = TemplateRenderer(
            mock_settings_with_plugins, plugin_registry=plugin_registry_with_mocks
        )

        text = "Value: {{ test_var }}"
        result = renderer.render_rule_text(text, sample_merged_scope)

        assert result == "Value: test_value"

    def test_plugin_context_in_build_context(
        self, mock_settings_with_plugins, plugin_registry_with_mocks, sample_merged_scope
    ):
        """Plugin context included in built context."""
        renderer = TemplateRenderer(
            mock_settings_with_plugins, plugin_registry=plugin_registry_with_mocks
        )

        context = renderer._build_context(sample_merged_scope)

        assert "test_var" in context
        assert context["test_var"] == "test_value"

    def test_disabled_plugins_not_executed(
        self, mock_settings, plugin_registry_with_mocks, sample_merged_scope
    ):
        """Plugins not executed when disabled."""
        mock_settings.ENABLED_PLUGINS = []

        renderer = TemplateRenderer(
            mock_settings, plugin_registry=plugin_registry_with_mocks
        )

        context = renderer._build_context(sample_merged_scope)

        assert "test_var" not in context

    def test_no_plugin_registry(self, mock_settings, sample_merged_scope):
        """Renderer works without plugin registry."""
        renderer = TemplateRenderer(mock_settings, plugin_registry=None)

        context = renderer._build_context(sample_merged_scope)

        assert "test_var" not in context
        assert "scope" in context

    def test_plugin_error_doesnt_break_rendering(
        self, mock_settings_with_plugins, sample_merged_scope
    ):
        """Plugin errors logged but don't break rendering."""
        from daimyo.domain import ContextProviderPlugin
        from daimyo.infrastructure.plugins import PluginRegistry

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
                raise RuntimeError("Plugin error")

        registry = PluginRegistry()
        registry.register(FailingPlugin())

        renderer = TemplateRenderer(mock_settings_with_plugins, plugin_registry=registry)

        # Plugin error should be caught and logged, not raise
        context = renderer._build_context(sample_merged_scope)

        # Context should still be built despite plugin error
        assert "scope" in context
        # Plugin context should not be added due to error
        assert "test_var" not in context

    def test_plugin_context_conflicts_with_existing(
        self, mock_settings_with_plugins, sample_merged_scope
    ):
        """Plugin context can override existing context keys."""
        from daimyo.domain import ContextProviderPlugin
        from daimyo.infrastructure.plugins import PluginRegistry

        class ConflictingPlugin(ContextProviderPlugin):
            @property
            def name(self) -> str:
                return "test.conflict"

            @property
            def description(self) -> str:
                return "Conflicting plugin"

            def is_available(self) -> bool:
                return True

            def get_context(self, scope):
                return {"RULES_PATH": "plugin_override"}

        registry = PluginRegistry()
        registry.register(ConflictingPlugin())

        renderer = TemplateRenderer(mock_settings_with_plugins, plugin_registry=registry)

        context = renderer._build_context(sample_merged_scope)

        assert context["RULES_PATH"] == "plugin_override"

    def test_empty_enabled_patterns_no_plugins(
        self, mock_settings, plugin_registry_with_mocks, sample_merged_scope
    ):
        """Empty enabled patterns means no plugins execute."""
        mock_settings.ENABLED_PLUGINS = []

        renderer = TemplateRenderer(
            mock_settings, plugin_registry=plugin_registry_with_mocks
        )

        context = renderer._build_context(sample_merged_scope)

        assert "test_var" not in context

    def test_plugin_provides_nested_context(
        self, mock_settings_with_plugins, sample_merged_scope
    ):
        """Plugin can provide nested dictionary context."""
        from daimyo.domain import ContextProviderPlugin
        from daimyo.infrastructure.plugins import PluginRegistry

        class NestedPlugin(ContextProviderPlugin):
            @property
            def name(self) -> str:
                return "test.nested"

            @property
            def description(self) -> str:
                return "Nested context plugin"

            def is_available(self) -> bool:
                return True

            def get_context(self, scope):
                return {"git": {"branch": "main", "commit": "abc123"}}

        registry = PluginRegistry()
        registry.register(NestedPlugin())

        renderer = TemplateRenderer(mock_settings_with_plugins, plugin_registry=registry)

        text = "Branch: {{ git.branch }}, Commit: {{ git.commit }}"
        result = renderer.render_rule_text(text, sample_merged_scope)

        assert result == "Branch: main, Commit: abc123"
