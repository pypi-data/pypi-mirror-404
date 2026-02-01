"""Integration tests for plugin system."""


from daimyo.infrastructure.di import ServiceContainer


class TestPluginSystemIntegration:
    """Test plugin system end-to-end."""

    def test_plugin_registry_initialization(self):
        """Plugin registry initializes through container."""
        container = ServiceContainer()
        registry = container.plugin_registry()

        assert registry is not None
        plugins = registry.list_plugins()
        assert isinstance(plugins, list)

    def test_template_renderer_has_plugin_registry(self):
        """Template renderer receives plugin registry from container."""
        container = ServiceContainer()
        renderer = container.template_renderer()

        assert renderer.plugin_registry is not None

    def test_discovered_but_not_enabled_plugins_not_used(
        self, sample_merged_scope, mock_settings
    ):
        """Discovered plugins not used unless enabled."""
        mock_settings.ENABLED_PLUGINS = []

        container = ServiceContainer()
        from daimyo.application.templating import TemplateRenderer

        renderer = TemplateRenderer(mock_settings, plugin_registry=container.plugin_registry())

        context = renderer._build_context(sample_merged_scope)

        setting_keys = set(mock_settings.as_dict().keys())
        extra_keys = set(context.keys()) - setting_keys - {"scope"}

        assert len(extra_keys) == 0

    def test_container_reset_clears_plugin_registry(self):
        """Container reset clears plugin registry."""
        container = ServiceContainer()
        registry1 = container.plugin_registry()

        container.reset()

        registry2 = container.plugin_registry()

        assert registry1 is not registry2
