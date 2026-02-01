"""Markdown formatter for MCP API responses."""

from typing import TYPE_CHECKING

from daimyo.application.formatters.helpers import RuleProcessorMixin, TemplateAwareMixin
from daimyo.application.formatters.tree_builder import CategoryTreeBuilder
from daimyo.domain import Category, MergedScope, RuleSet

if TYPE_CHECKING:
    from daimyo.application.templating import TemplateRenderer


class MarkdownFormatter(TemplateAwareMixin, RuleProcessorMixin):
    """Format merged scope as markdown with hierarchy and MUST/SHOULD markers.

    Features:
    - Nested headings for category hierarchy (## python, ### web, #### testing)
    - MUST markers for commandments, SHOULD markers for suggestions
    - Include 'when' descriptions for each category
    - Jinja2 template rendering support
    """

    def __init__(self, template_renderer: "TemplateRenderer | None" = None):
        """Initialize formatter.

        :param template_renderer: Optional template renderer for dynamic rule text
        :type template_renderer: TemplateRenderer | None
        """
        self.template_renderer = template_renderer
        from daimyo.config import settings

        self.settings = settings

    def format(self, scope: MergedScope) -> str:
        """Format merged scope as markdown.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: Markdown-formatted string
        :rtype: str
        """
        lines = []

        prologue = self.settings.get("RULES_MARKDOWN_PROLOGUE", "")
        if prologue:
            if self.template_renderer:
                rendered_prologue = self.template_renderer.render_prologue_epilogue(
                    prologue,
                    scope,
                    context_type="rules markdown prologue",
                    failure_collector=scope,
                )
                lines.append(rendered_prologue)
            else:
                lines.append(prologue)
            lines.append("")

        lines.append(f"# Rules for {scope.metadata.name}\n")
        if scope.metadata.description:
            lines.append(f"{scope.metadata.description}\n")

        categorized = self.settings.get("RULES_CATEGORIZED", True)

        if categorized:
            merged_tree = CategoryTreeBuilder.merge_trees(
                list(scope.commandments.categories.values()),
                list(scope.suggestions.categories.values()),
            )
            lines.extend(self._format_merged_tree(merged_tree, scope, depth=2))
        else:
            lines.extend(self._format_aggregated(scope))

        epilogue = self.settings.get("RULES_MARKDOWN_EPILOGUE", "")
        if epilogue:
            lines.append("")
            if self.template_renderer:
                rendered_epilogue = self.template_renderer.render_prologue_epilogue(
                    epilogue,
                    scope,
                    context_type="rules markdown epilogue",
                    failure_collector=scope,
                )
                lines.append(rendered_epilogue)
            else:
                lines.append(epilogue)

        if scope.template_failures:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("<ignore-failed-template>")
            lines.append("## Template Failures\n")
            for failure in scope.template_failures:
                if failure.variable_name:
                    lines.append(
                        f"**{failure.element_identifier}**: `{failure.variable_name}` undefined"
                    )
                else:
                    lines.append(f"**{failure.element_identifier}**: render error")
                lines.append(f"```\n{failure.template_text}\n```\n")
            lines.append("</ignore-failed-template>")

        return "\n".join(lines)

    def _format_merged_tree(
        self, tree: dict[str, dict], scope: MergedScope, depth: int, path: str = ""
    ) -> list[str]:
        """Format merged category tree with both MUST and SHOULD rules.

        :param tree: Merged category tree
        :type tree: Dict[str, Dict]
        :param scope: Scope for template rendering
        :type scope: MergedScope
        :param depth: Current heading depth
        :type depth: int
        :param path: Current category path
        :type path: str
        :returns: List of markdown lines
        :rtype: List[str]
        """
        lines = []

        for key, node in sorted(tree.items()):
            current_path = f"{path}.{key}" if path else key

            commandments = node.get("_commandments", [])
            suggestions = node.get("_suggestions", [])

            when_description = None
            category_for_when = None

            for category in commandments:
                if category.when:
                    when_description = category.when
                    category_for_when = category
                    break
            if not when_description:
                for category in suggestions:
                    if category.when:
                        when_description = category.when
                        category_for_when = category
                        break

            must_rules = []
            for category in commandments:
                must_rules.extend(
                    self._render_and_prune_rules(category, scope, failure_collector=scope)
                )

            should_rules = []
            for category in suggestions:
                should_rules.extend(
                    self._render_and_prune_rules(category, scope, failure_collector=scope)
                )

            children = node.get("_children", {})
            children_lines = []
            if children:
                children_lines = self._format_merged_tree(children, scope, depth + 1, current_path)

            if must_rules or should_rules or children_lines:
                heading = "#" * depth
                lines.append(f"{heading} {key}\n")

                if must_rules or should_rules:
                    from daimyo.domain import CategoryKey

                    category_tags = self._get_category_tags(commandments, suggestions)
                    if category_tags:
                        tags_str = "; ".join(category_tags)
                        lines.append(f"<tags>{tags_str}</tags>\n")

                    current_category_key = CategoryKey.from_string(current_path)
                    when_to_render = self._get_when_with_hierarchical_fallback(
                        current_category_key,
                        when_description,
                        scope.commandments,
                        scope.suggestions,
                        scope,
                        failure_collector=scope,
                    )
                    if category_for_when:
                        rendered_when = self._render_text(
                            when_to_render, scope, category_for_when, failure_collector=scope
                        )
                    else:
                        rendered_when = when_to_render
                    lines.append(f"*{rendered_when}*\n")

                    for rendered_rule in must_rules:
                        wrapped_rule = self._wrap_rule_in_xml_tag(rendered_rule, "commandments")
                        lines.append(f"- **MUST**: {wrapped_rule}")

                    for rendered_rule in should_rules:
                        wrapped_rule = self._wrap_rule_in_xml_tag(rendered_rule, "suggestions")
                        lines.append(f"- **SHOULD**: {wrapped_rule}")

                    lines.append("")

                lines.extend(children_lines)

        return lines

    def _format_ruleset_markdown(self, ruleset: RuleSet, marker: str) -> str:
        """Format a ruleset as markdown with hierarchical headings.

        :param ruleset: The ruleset to format
        :type ruleset: RuleSet
        :param marker: The marker to use (MUST or SHOULD)
        :type marker: str
        :returns: Markdown string
        :rtype: str
        """
        lines = []

        category_tree = CategoryTreeBuilder.build_tree(list(ruleset.categories.values()))

        lines.extend(self._format_tree(category_tree, marker, depth=3))

        return "\n".join(lines)

    def _format_tree(
        self, tree: dict[str, dict], marker: str, depth: int, path: str = ""
    ) -> list[str]:
        """Recursively format category tree as markdown.

        :param tree: Category tree
        :type tree: Dict[str, Dict]
        :param marker: MUST or SHOULD
        :type marker: str
        :param depth: Current heading depth
        :type depth: int
        :param path: Current category path
        :type path: str
        :returns: List of markdown lines
        :rtype: List[str]
        """
        lines = []

        for key, node in sorted(tree.items()):
            heading = "#" * depth
            current_path = f"{path}.{key}" if path else key
            lines.append(f"{heading} {key}\n")

            for category in node.get("_categories", []):
                lines.append(f"*{category.when}*\n")

                for rule in category.rules:
                    lines.append(f"- **{marker}**: {rule.text}")
                lines.append("")

            children = node.get("_children", {})
            if children:
                lines.extend(self._format_tree(children, marker, depth + 1, current_path))

        return lines

    def _get_category_tags(
        self, commandments: list[Category], suggestions: list[Category]
    ) -> list[str]:
        """Extract unique tags from categories.

        :param commandments: List of commandment categories
        :type commandments: list[Category]
        :param suggestions: List of suggestion categories
        :type suggestions: list[Category]
        :returns: Sorted list of unique tags
        :rtype: list[str]
        """
        all_tags = set()
        for category in commandments:
            all_tags.update(category.tags)
        for category in suggestions:
            all_tags.update(category.tags)
        return sorted(all_tags)

    def _wrap_rule_in_xml_tag(self, rule_text: str, rule_type: str) -> str:
        """Wrap rule text in XML tag if configured.

        :param rule_text: The rule text to wrap
        :type rule_text: str
        :param rule_type: Either "commandments" or "suggestions"
        :type rule_type: str
        :returns: Wrapped rule text or original if no tag configured
        :rtype: str
        """
        if rule_type == "commandments":
            tag = self.settings.get("COMMANDMENTS_XML_TAG", "")
        else:
            tag = self.settings.get("SUGGESTIONS_XML_TAG", "")

        if tag:
            return f"<{tag}>{rule_text}</{tag}>"
        return rule_text

    def _format_aggregated(self, scope: MergedScope) -> list[str]:
        """Format rules without category separation.

        Collects all commandments and suggestions, then displays them
        in two simple sections without hierarchical categories.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: List of markdown lines
        :rtype: list[str]
        """
        lines = []

        all_commandments = []
        for category in scope.commandments.categories.values():
            rendered_rules = self._render_and_prune_rules(category, scope, failure_collector=scope)
            all_commandments.extend(rendered_rules)

        all_suggestions = []
        for category in scope.suggestions.categories.values():
            rendered_rules = self._render_and_prune_rules(category, scope, failure_collector=scope)
            all_suggestions.extend(rendered_rules)

        if all_commandments:
            lines.append("## Commandments\n")
            for rule in all_commandments:
                formatted_rule = self._wrap_rule_in_xml_tag(rule, "commandments")
                lines.append(f"- **MUST**: {formatted_rule}")
            lines.append("")

        if all_suggestions:
            lines.append("## Suggestions\n")
            for rule in all_suggestions:
                formatted_rule = self._wrap_rule_in_xml_tag(rule, "suggestions")
                lines.append(f"- **SHOULD**: {formatted_rule}")
            lines.append("")

        return lines


__all__ = ["MarkdownFormatter"]
