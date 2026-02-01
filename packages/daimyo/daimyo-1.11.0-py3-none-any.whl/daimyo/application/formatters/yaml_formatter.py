"""YAML multi-document formatter for server federation."""

from typing import TYPE_CHECKING, Any

import yaml  # type: ignore[import-untyped]

from daimyo.application.formatters.helpers import (
    MetadataBuilderMixin,
    NestedDictNavigator,
    RuleProcessorMixin,
    TemplateAwareMixin,
)
from daimyo.domain import MergedScope, RuleSet

if TYPE_CHECKING:
    from daimyo.application.templating import TemplateRenderer


class YamlMultiDocFormatter(TemplateAwareMixin, RuleProcessorMixin, MetadataBuilderMixin):
    """Format merged scope as multi-document YAML.

    Output contains 3 or 4 YAML documents separated by '---':
    1. Metadata document
    2. Commandments document
    3. Suggestions document
    4. Template failures document (if any failures occurred)

    This format is useful for server federation where a server needs to
    parse and overlay rules from another server.
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

    def format(self, scope: MergedScope) -> str:
        """Format merged scope as multi-document YAML.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: Multi-document YAML string (3 or 4 documents if failures exist)
        :rtype: str
        """
        documents = []

        metadata_doc = {"metadata": self._build_metadata_dict(scope)}
        documents.append(metadata_doc)

        commandments_doc = {"commandments": self._format_ruleset(scope.commandments, scope)}
        documents.append(commandments_doc)

        suggestions_doc = {"suggestions": self._format_ruleset(scope.suggestions, scope)}
        documents.append(suggestions_doc)

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
            failures_doc: dict[str, Any] = {"template_failures": failures_list}
            documents.append(failures_doc)

        yaml_parts = []
        for doc in documents:
            yaml_str = yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)
            yaml_parts.append(yaml_str)

        return "---\n".join(yaml_parts)

    def _format_ruleset(self, ruleset: RuleSet, scope: MergedScope) -> dict[str, Any]:
        """Format a ruleset as nested dictionary.

        :param ruleset: The ruleset to format
        :type ruleset: RuleSet
        :param scope: Scope for template rendering
        :type scope: MergedScope
        :returns: Nested dictionary representation
        :rtype: Dict[str, Any]
        """
        result: dict[str, Any] = {}

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

            is_parent = self._is_parent_category(category.key, scope)
            if rendered_rules or is_parent:
                value = {
                    "when": rendered_when,
                    "ruleset": rendered_rules,
                }
                NestedDictNavigator.navigate_and_set(result, category.key, value)

        return result


__all__ = ["YamlMultiDocFormatter"]
