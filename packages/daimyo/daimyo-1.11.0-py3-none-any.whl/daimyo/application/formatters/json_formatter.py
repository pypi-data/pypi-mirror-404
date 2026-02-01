"""JSON formatter for API responses."""

from typing import TYPE_CHECKING, Any

from daimyo.application.formatters.helpers import (
    MetadataBuilderMixin,
    RuleProcessorMixin,
    TemplateAwareMixin,
)
from daimyo.domain import MergedScope, RuleSet

if TYPE_CHECKING:
    from daimyo.application.templating import TemplateRenderer


class JsonFormatter(TemplateAwareMixin, RuleProcessorMixin, MetadataBuilderMixin):
    """Format merged scope as JSON.

    Output contains structured JSON with metadata, commandments, and suggestions.
    """

    def __init__(self, template_renderer: "TemplateRenderer | None" = None):
        """Initialize formatter.

        :param template_renderer: Optional template renderer
        :type template_renderer: TemplateRenderer | None
        :returns: None
        :rtype: None
        """
        self.template_renderer = template_renderer
        from daimyo.config import settings

        self.settings = settings

    def format(self, scope: MergedScope) -> dict[str, Any]:
        """Format merged scope as JSON-serializable dictionary.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: Dictionary ready for JSON serialization
        :rtype: Dict[str, Any]
        """
        result: dict[str, Any] = {
            "metadata": self._build_metadata_dict(scope),
            "commandments": self._format_ruleset(scope.commandments, scope),
            "suggestions": self._format_ruleset(scope.suggestions, scope),
        }

        if scope.template_failures:
            failures_list: list[dict[str, Any]] = [
                {
                    "element_type": f.element_type,
                    "element_identifier": f.element_identifier,
                    "template_text": f.template_text,
                    "error_message": f.error_message,
                    "variable_name": f.variable_name,
                }
                for f in scope.template_failures
            ]
            result["template_failures"] = failures_list

        return result

    def _format_ruleset(self, ruleset: RuleSet, scope: MergedScope) -> dict[str, dict[str, Any]]:
        """Format a ruleset as flat dictionary with category keys.

        :param ruleset: The ruleset to format
        :type ruleset: RuleSet
        :param scope: Scope for template rendering
        :type scope: MergedScope
        :returns: Dictionary mapping category keys to their data
        :rtype: Dict[str, Dict[str, Any]]
        """
        result = {}

        for category in ruleset.categories.values():
            when_text = self._get_when_with_hierarchical_fallback(
                category.key,
                category.when,
                scope.commandments,
                scope.suggestions,
                scope,
                failure_collector=scope,
            )
            rendered_when = self._render_text(when_text, scope, category, failure_collector=scope)
            rendered_rules = self._render_and_prune_rules(category, scope, failure_collector=scope)

            if rendered_rules:
                result[str(category.key)] = {
                    "when": rendered_when,
                    "tags": category.tags,
                    "rules": rendered_rules,
                }

        return result


__all__ = ["JsonFormatter"]
