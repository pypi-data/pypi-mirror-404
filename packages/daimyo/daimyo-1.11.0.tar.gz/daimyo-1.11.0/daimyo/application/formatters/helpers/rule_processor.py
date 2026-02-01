"""Rule processing utilities for formatters."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from daimyo.domain import Category, CategoryKey, MergedScope


class RuleProcessorMixin:
    """Mixin providing rule rendering and pruning logic.

    Classes using this mixin must implement _render_text() method.
    This is satisfied by TemplateAwareMixin.
    """

    def _render_text(
        self,
        text: str,
        scope: "MergedScope",
        category: "Category | None" = None,
        failure_collector: "MergedScope | None" = None,
        rule_index: int | None = None,
    ) -> str:
        raise NotImplementedError("Subclass must implement _render_text")

    def _render_and_prune_rules(
        self,
        category: "Category",
        scope: "MergedScope",
        failure_collector: "MergedScope | None" = None,
    ) -> list[str]:
        """Render category rules and prune empty results.

        This method centralizes the common pattern:
        1. Iterate through category.rules
        2. Render each rule.text with _render_text()
        3. Check if rendered_rule.strip() is truthy
        4. Only include non-empty rendered rules

        :param category: Category containing rules
        :type category: Category
        :param scope: Scope for template rendering
        :type scope: MergedScope
        :param failure_collector: Optional scope to collect failures
        :type failure_collector: MergedScope | None
        :returns: List of rendered, non-empty rule texts
        :rtype: list[str]
        """
        rendered_rules = []
        for idx, rule in enumerate(category.rules):
            rendered_rule = self._render_text(
                rule.text, scope, category, failure_collector, rule_index=idx
            )
            if rendered_rule.strip():
                rendered_rules.append(rendered_rule)
        return rendered_rules

    def _is_parent_category(self, category_key: "CategoryKey", scope: "MergedScope") -> bool:
        """Check if a category is a parent of other categories.

        :param category_key: The category to check
        :type category_key: CategoryKey
        :param scope: The merged scope
        :type scope: MergedScope
        :returns: True if any category starts with this key as prefix
        :rtype: bool
        """

        key_str = str(category_key)

        for ruleset in [scope.commandments, scope.suggestions]:
            for cat_key in ruleset.categories.keys():
                cat_str = str(cat_key)
                if cat_str.startswith(key_str + "."):
                    return True

        return False


__all__ = ["RuleProcessorMixin"]
