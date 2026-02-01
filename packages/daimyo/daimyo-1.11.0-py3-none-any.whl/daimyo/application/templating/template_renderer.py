"""Template rendering service using Jinja2."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, StrictUndefined, TemplateError, UndefinedError

from daimyo.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from daimyo.domain import Category, CategoryKey, MergedScope

logger = get_logger(__name__)

TEMPLATE_PATTERN = re.compile(r"\{\{.*?\}\}|\{%.*?%\}")


class TemplateRenderer:
    """Renders Jinja2 templates in rule text with strict undefined checking.

    Features:
    - Strict mode: Raises TemplateRenderingError if variable is undefined
    - Auto-detection: Only processes strings with {{ }} or {% %} syntax
    - Rich context: Provides config, scope metadata, category info
    """

    def __init__(self, settings: Any, plugin_registry: Any = None):
        """Initialize renderer with Dynaconf settings.

        :param settings: Dynaconf settings object
        :type settings: Any
        :param plugin_registry: Optional plugin registry for context and filter providers
        :type plugin_registry: Any | None
        """
        self.settings = settings
        self.plugin_registry = plugin_registry

        self.env = Environment(
            undefined=StrictUndefined,
            autoescape=False,
        )

        # Register plugin-provided filters and tests
        if self.plugin_registry is not None:
            enabled_patterns = getattr(self.settings, "ENABLED_PLUGINS", [])
            if enabled_patterns:
                try:
                    filters, tests = self.plugin_registry.aggregate_filters_and_tests(
                        enabled_patterns
                    )

                    self.env.filters.update(filters)
                    self.env.tests.update(tests)

                    logger.info(
                        f"Registered {len(filters)} custom filters "
                        f"and {len(tests)} custom tests from plugins"
                    )

                except Exception as e:
                    logger.error(f"Failed to register plugin filters/tests: {e}")

    def needs_rendering(self, text: str) -> bool:
        """Check if text contains template syntax.

        :param text: Text to check
        :type text: str
        :returns: True if text contains {{ }} or {% %}
        :rtype: bool
        """
        return bool(TEMPLATE_PATTERN.search(text))

    def render_rule_text(
        self,
        text: str,
        scope: MergedScope,
        category: Category | None = None,
        failure_collector: MergedScope | None = None,
        rule_index: int | None = None,
    ) -> str:
        """Render a rule text template.

        :param text: Rule text (may contain templates)
        :type text: str
        :param scope: Merged scope for context
        :type scope: MergedScope
        :param category: Optional category for context
        :type category: Category | None
        :param failure_collector: Optional scope to collect failures (graceful mode)
        :type failure_collector: MergedScope | None
        :param rule_index: Optional rule index for error identification
        :type rule_index: int | None
        :returns: Rendered text or original text if failed gracefully
        :rtype: str
        :raises TemplateRenderingError: If template variable is undefined and no failure_collector
        """
        if not self.needs_rendering(text):
            return text

        context = self._build_context(scope, category)

        try:
            template = self.env.from_string(text)
            result = template.render(context)
            logger.debug(f"Rendered template: {text[:50]}... → {result[:50]}...")
            return result

        except UndefinedError as e:
            if failure_collector is None:
                from daimyo.domain import TemplateRenderingError

                match = re.search(r"'([^']+)' is undefined", str(e))
                variable_name = match.group(1) if match else "unknown"

                context_info = f"scope '{scope.metadata.name}'"
                if category:
                    context_info += f", category '{category.key}'"

                raise TemplateRenderingError(
                    template_text=text,
                    variable_name=variable_name,
                    context_info=context_info,
                ) from e

            match = re.search(r"'([^']+)' is undefined", str(e))
            variable_name = match.group(1) if match else None

            element_id = f"rule #{rule_index + 1}" if rule_index is not None else "rule"
            if category:
                element_id = f"{category.key} {element_id}"

            failure_collector.add_template_failure(
                element_type="rule",
                element_identifier=element_id,
                template_text=text,
                error=e,
                variable_name=variable_name,
            )

            logger.warning(f"Template rendering failed for {element_id}: {variable_name}")
            return ""

        except TemplateError as e:
            if failure_collector is None:
                from daimyo.domain import TemplateRenderingError

                context_info = f"scope '{scope.metadata.name}'"
                if category:
                    context_info += f", category '{category.key}'"

                # For non-UndefinedError template errors, use the error message as variable_name
                error_description = str(e)

                raise TemplateRenderingError(
                    template_text=text,
                    variable_name=error_description,
                    context_info=context_info,
                ) from e

            element_id = f"rule #{rule_index + 1}" if rule_index is not None else "rule"
            if category:
                element_id = f"{category.key} {element_id}"

            failure_collector.add_template_failure(
                element_type="rule",
                element_identifier=element_id,
                template_text=text,
                error=e,
                variable_name=None,
            )

            logger.warning(f"Template rendering failed for {element_id}: {str(e)}")
            return ""

    def render_category_when(
        self,
        when_text: str,
        scope: MergedScope,
        category: Category,
        failure_collector: MergedScope | None = None,
    ) -> str:
        """Render a category 'when' description template.

        :param when_text: Category when description
        :type when_text: str
        :param scope: Merged scope for context
        :type scope: MergedScope
        :param category: Category for context
        :type category: Category
        :param failure_collector: Optional scope to collect failures (graceful mode)
        :type failure_collector: MergedScope | None
        :returns: Rendered when description or original text if failed gracefully
        :rtype: str
        :raises TemplateRenderingError: If template variable is undefined and no failure_collector
        """
        if not self.needs_rendering(when_text):
            return when_text

        context = self._build_context(scope, category)

        try:
            template = self.env.from_string(when_text)
            result = template.render(context)
            logger.debug(f"Rendered category when: {when_text[:50]}... → {result[:50]}...")
            return result

        except UndefinedError as e:
            if failure_collector is None:
                from daimyo.domain import TemplateRenderingError

                match = re.search(r"'([^']+)' is undefined", str(e))
                variable_name = match.group(1) if match else "unknown"

                context_info = f"scope '{scope.metadata.name}', category '{category.key}'"

                raise TemplateRenderingError(
                    template_text=when_text,
                    variable_name=variable_name,
                    context_info=context_info,
                ) from e

            match = re.search(r"'([^']+)' is undefined", str(e))
            variable_name = match.group(1) if match else None

            element_id = f"{category.key} when description"

            failure_collector.add_template_failure(
                element_type="category_when",
                element_identifier=element_id,
                template_text=when_text,
                error=e,
                variable_name=variable_name,
            )

            logger.warning(f"Template rendering failed for {element_id}: {variable_name}")
            return ""

        except TemplateError as e:
            if failure_collector is None:
                from daimyo.domain import TemplateRenderingError

                context_info = f"scope '{scope.metadata.name}', category '{category.key}'"

                # For non-UndefinedError template errors, use the error message as variable_name
                error_description = str(e)

                raise TemplateRenderingError(
                    template_text=when_text,
                    variable_name=error_description,
                    context_info=context_info,
                ) from e

            element_id = f"{category.key} when description"

            failure_collector.add_template_failure(
                element_type="category_when",
                element_identifier=element_id,
                template_text=when_text,
                error=e,
                variable_name=None,
            )

            logger.warning(f"Template rendering failed for {element_id}: {str(e)}")
            return ""

    def render_prologue_epilogue(
        self,
        text: str,
        scope: MergedScope,
        context_type: str = "unknown",
        failure_collector: MergedScope | None = None,
    ) -> str:
        """Render prologue/epilogue template.

        Prologues and epilogues have NO category context, only scope and config.
        This is important because they appear before/after category hierarchies.

        :param text: Prologue or epilogue text (may contain templates)
        :type text: str
        :param scope: Merged scope for context
        :type scope: MergedScope
        :param context_type: Description like "rules prologue" for error messages
        :type context_type: str
        :param failure_collector: Optional scope to collect failures (graceful mode)
        :type failure_collector: MergedScope | None
        :returns: Rendered text or original text if failed gracefully
        :rtype: str
        :raises TemplateRenderingError: If template variable is undefined and no failure_collector
        """
        if not self.needs_rendering(text):
            return text

        context = self._build_context(scope, category=None)

        try:
            template = self.env.from_string(text)
            result = template.render(context)
            logger.debug(f"Rendered {context_type}: {text[:50]}... → {result[:50]}...")
            return result

        except UndefinedError as e:
            if failure_collector is None:
                from daimyo.domain import TemplateRenderingError

                match = re.search(r"'([^']+)' is undefined", str(e))
                variable_name = match.group(1) if match else "unknown"

                context_info = f"{context_type} for scope '{scope.metadata.name}'"

                raise TemplateRenderingError(
                    template_text=text,
                    variable_name=variable_name,
                    context_info=context_info,
                ) from e

            match = re.search(r"'([^']+)' is undefined", str(e))
            variable_name = match.group(1) if match else None

            element_type = "prologue" if "prologue" in context_type.lower() else "epilogue"

            failure_collector.add_template_failure(
                element_type=element_type,
                element_identifier=context_type,
                template_text=text,
                error=e,
                variable_name=variable_name,
            )

            logger.warning(f"Template rendering failed for {context_type}: {variable_name}")
            return ""

        except TemplateError as e:
            if failure_collector is None:
                from daimyo.domain import TemplateRenderingError

                context_info = f"{context_type} for scope '{scope.metadata.name}'"

                # For non-UndefinedError template errors, use the error message as variable_name
                error_description = str(e)

                raise TemplateRenderingError(
                    template_text=text,
                    variable_name=error_description,
                    context_info=context_info,
                ) from e

            element_type = "prologue" if "prologue" in context_type.lower() else "epilogue"

            failure_collector.add_template_failure(
                element_type=element_type,
                element_identifier=context_type,
                template_text=text,
                error=e,
                variable_name=None,
            )

            logger.warning(f"Template rendering failed for {context_type}: {str(e)}")
            return ""

    def render_default_category_description(
        self,
        text: str,
        scope: MergedScope,
        category_key: CategoryKey,
        failure_collector: MergedScope | None = None,
    ) -> str:
        """Render default category description template.

        Used when a category has no 'when' description and no parent 'when' either.
        Unlike prologues/epilogues, this CAN use category context (the key).

        :param text: Default description text (may contain templates)
        :type text: str
        :param scope: Merged scope for context
        :type scope: MergedScope
        :param category_key: The category key for context
        :type category_key: CategoryKey
        :param failure_collector: Optional scope to collect failures (graceful mode)
        :type failure_collector: MergedScope | None
        :returns: Rendered text or original text if failed gracefully
        :rtype: str
        :raises TemplateRenderingError: If template variable is undefined and no failure_collector
        """
        if not self.needs_rendering(text):
            return text

        from daimyo.domain import Category

        temp_category = Category(key=category_key, when="")

        context = self._build_context(scope, temp_category)

        try:
            template = self.env.from_string(text)
            result = template.render(context)
            logger.debug(
                f"Rendered default category description for {category_key}: "
                f"{text[:50]}... → {result[:50]}..."
            )
            return result

        except UndefinedError as e:
            if failure_collector is None:
                from daimyo.domain import TemplateRenderingError

                match = re.search(r"'([^']+)' is undefined", str(e))
                variable_name = match.group(1) if match else "unknown"

                context_info = (
                    f"default category description for '{category_key}' "
                    f"in scope '{scope.metadata.name}'"
                )

                raise TemplateRenderingError(
                    template_text=text,
                    variable_name=variable_name,
                    context_info=context_info,
                ) from e

            match = re.search(r"'([^']+)' is undefined", str(e))
            variable_name = match.group(1) if match else None

            element_id = f"{category_key} default description"

            failure_collector.add_template_failure(
                element_type="default_category_description",
                element_identifier=element_id,
                template_text=text,
                error=e,
                variable_name=variable_name,
            )

            logger.warning(f"Template rendering failed for {element_id}: {variable_name}")
            return ""

        except TemplateError as e:
            if failure_collector is None:
                from daimyo.domain import TemplateRenderingError

                context_info = (
                    f"default category description for '{category_key}' "
                    f"in scope '{scope.metadata.name}'"
                )

                # For non-UndefinedError template errors, use the error message as variable_name
                error_description = str(e)

                raise TemplateRenderingError(
                    template_text=text,
                    variable_name=error_description,
                    context_info=context_info,
                ) from e

            element_id = f"{category_key} default description"

            failure_collector.add_template_failure(
                element_type="default_category_description",
                element_identifier=element_id,
                template_text=text,
                error=e,
                variable_name=None,
            )

            logger.warning(f"Template rendering failed for {element_id}: {str(e)}")
            return ""

    def _build_context(
        self,
        scope: MergedScope,
        category: Category | None = None,
    ) -> dict[str, Any]:
        """Build Jinja2 context dictionary including plugin-provided context.

        :param scope: Merged scope
        :type scope: MergedScope
        :param category: Optional category
        :type category: Category | None
        :returns: Context dictionary for template rendering
        :rtype: dict[str, Any]
        """
        context: dict[str, Any] = {}

        for key, value in self.settings.as_dict().items():
            if isinstance(value, (str, int, bool, float, type(None))):
                context[key] = value

        context["scope"] = {
            "name": scope.metadata.name,
            "description": scope.metadata.description,
            "tags": scope.metadata.tags,
            "sources": scope.sources,
        }

        if category:
            context["category"] = {
                "key": str(category.key),
                "when": category.when,
            }

        if self.plugin_registry is not None:
            enabled_patterns = getattr(self.settings, "ENABLED_PLUGINS", [])

            if enabled_patterns:
                try:
                    plugin_context = self.plugin_registry.aggregate_context(
                        scope=scope,
                        enabled_patterns=enabled_patterns,
                    )

                    conflicts = set(context.keys()) & set(plugin_context.keys())
                    if conflicts:
                        logger.warning(f"Plugin context conflicts: {conflicts}")

                    context.update(plugin_context)
                    logger.debug(f"Added {len(plugin_context)} plugin context variables")

                except Exception as e:
                    logger.error(f"Failed to get plugin context: {e}")

        return context

    def get_context_with_sources(
        self,
        scope: MergedScope,
        category: Category | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Get template context organized by source.

        This method exposes the template context used for rendering rules,
        organized by where each variable comes from. Useful for debugging
        and understanding what variables are available in templates.

        :param scope: Merged scope for context
        :type scope: MergedScope
        :param category: Optional category for context
        :type category: Category | None
        :returns: Dictionary with sections: config, scope, category (optional), plugins
        :rtype: dict[str, dict[str, Any]]
        """
        result: dict[str, dict[str, Any]] = {
            "config": {},
            "scope": {},
            "plugins": {},
        }

        for key, value in self.settings.as_dict().items():
            if isinstance(value, (str, int, bool, float, type(None))):
                result["config"][key] = value

        result["scope"] = {
            "name": scope.metadata.name,
            "description": scope.metadata.description,
            "tags": scope.metadata.tags,
            "sources": scope.sources,
        }

        if category:
            result["category"] = {
                "key": str(category.key),
                "when": category.when,
            }

        if self.plugin_registry is not None:
            enabled_patterns = getattr(self.settings, "ENABLED_PLUGINS", [])

            if enabled_patterns:
                try:
                    plugin_context = self.plugin_registry.aggregate_context(
                        scope=scope,
                        enabled_patterns=enabled_patterns,
                    )
                    result["plugins"] = plugin_context
                    logger.debug(f"Extracted {len(plugin_context)} plugin context variables")

                except Exception as e:
                    logger.error(f"Failed to get plugin context: {e}")

        return result


__all__ = ["TemplateRenderer"]
