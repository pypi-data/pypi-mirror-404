"""Template rendering mixin for formatters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from daimyo.application.templating import TemplateRenderer
    from daimyo.domain import Category, CategoryKey, MergedScope, RuleSet


class TemplateAwareMixin:
    """Mixin providing template rendering capability.

    Classes using this mixin must have:
    - 'template_renderer' attribute of type TemplateRenderer | None
    - 'settings' attribute for accessing configuration
    """

    template_renderer: TemplateRenderer | None
    settings: Any

    def _get_when_with_fallback(
        self,
        when: str | None,
        scope: MergedScope,
        category_key: CategoryKey,
        failure_collector: MergedScope | None = None,
    ) -> str:
        """Get 'when' description with fallback to configured default.

        :param when: Optional when description
        :type when: str | None
        :param scope: Merged scope for template rendering
        :type scope: MergedScope
        :param category_key: Category key for template context
        :type category_key: CategoryKey
        :param failure_collector: Optional scope to collect failures
        :type failure_collector: MergedScope | None
        :returns: When description or rendered default
        :rtype: str
        """
        if when and when.strip():
            return when

        default_desc: str = str(self.settings.get("DEFAULT_CATEGORY_DESCRIPTION", ""))

        if not default_desc or not default_desc.strip():
            default_desc = "These rules apply at all times"

        if self.template_renderer:
            try:
                return self.template_renderer.render_default_category_description(
                    default_desc, scope, category_key, failure_collector
                )
            except Exception:
                return "These rules apply at all times"

        return default_desc

    def _get_when_with_hierarchical_fallback(
        self,
        category_key: CategoryKey,
        when: str | None,
        commandments: RuleSet,
        suggestions: RuleSet,
        scope: MergedScope,
        failure_collector: MergedScope | None = None,
    ) -> str:
        """Get 'when' description with hierarchical fallback.

        Fallback order:
        1. Provided 'when' parameter (from scope merging)
        2. Parent categories in hierarchy (e.g., python.web -> python)
        3. Configured default (from settings, may be templated)
        4. Hardcoded default: "These rules apply at all times"

        :param category_key: The category key
        :type category_key: CategoryKey
        :param when: Optional when description from category
        :type when: str | None
        :param commandments: Commandments ruleset to search parent categories
        :type commandments: RuleSet
        :param suggestions: Suggestions ruleset to search parent categories
        :type suggestions: RuleSet
        :param scope: Merged scope for template rendering
        :type scope: MergedScope
        :param failure_collector: Optional scope to collect failures
        :type failure_collector: MergedScope | None
        :returns: When description with hierarchical fallback
        :rtype: str
        """
        if when and when.strip():
            return when

        parts = category_key.parts
        for i in range(len(parts) - 1, 0, -1):
            parent_parts = parts[:i]
            from daimyo.domain import CategoryKey

            parent_key = CategoryKey(parts=parent_parts)

            if parent_key in commandments.categories:
                parent_when = commandments.categories[parent_key].when
                if parent_when and parent_when.strip():
                    return parent_when

            if parent_key in suggestions.categories:
                parent_when = suggestions.categories[parent_key].when
                if parent_when and parent_when.strip():
                    return parent_when

        return self._get_when_with_fallback(None, scope, category_key, failure_collector)

    def _render_text(
        self,
        text: str,
        scope: MergedScope,
        category: Category | None = None,
        failure_collector: MergedScope | None = None,
        rule_index: int | None = None,
    ) -> str:
        """Render text template if renderer available.

        :param text: Text to render
        :type text: str
        :param scope: Scope for context
        :type scope: MergedScope
        :param category: Optional category for context
        :type category: Category | None
        :param failure_collector: Optional scope to collect failures
        :type failure_collector: MergedScope | None
        :param rule_index: Optional rule index for error identification
        :type rule_index: int | None
        :returns: Rendered text (or original if no renderer)
        :rtype: str
        """
        if self.template_renderer:
            return self.template_renderer.render_rule_text(
                text, scope, category, failure_collector, rule_index
            )
        return text


__all__ = ["TemplateAwareMixin"]
