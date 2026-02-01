"""Tests for rule and category pruning after template rendering."""



from daimyo.application.formatters import (
    JsonFormatter,
    MarkdownFormatter,
    YamlMultiDocFormatter,
)
from daimyo.domain import Category, CategoryKey, MergedScope, Rule, RuleSet, RuleType, ScopeMetadata


class MockTemplateRenderer:
    """Mock template renderer that returns empty strings for specific rules."""

    def __init__(self, empty_rules: set[str]):
        """Initialize with set of rule texts that should render as empty.

        :param empty_rules: Set of rule texts to render as empty strings
        """
        self.empty_rules = empty_rules

    def render_rule_text(
        self, text: str, scope, category=None, failure_collector=None, rule_index=None
    ) -> str:
        """Render rule text, returning empty string for configured rules."""
        if text in self.empty_rules:
            return ""
        return text

    def render_category_when(
        self, when_text: str, scope, category, failure_collector=None
    ) -> str:
        """Render category when description, returning empty string for configured texts."""
        if when_text in self.empty_rules:
            return ""
        return when_text

    def render_prologue_epilogue(
        self, text: str, scope, context_type: str = "unknown", failure_collector=None
    ) -> str:
        """Render prologue/epilogue, returning empty string for configured texts."""
        if text in self.empty_rules:
            return ""
        return text

    def render_default_category_description(
        self, text: str, scope, category_key, failure_collector=None
    ) -> str:
        """Render default category description, returning empty string for configured texts."""
        if text in self.empty_rules:
            return ""
        return text


class TestJsonFormatterPruning:
    """Tests for JSON formatter pruning."""

    def test_prunes_empty_rules(self):
        """Test that empty rules after rendering are pruned."""
        metadata = ScopeMetadata(name="test", description="Test")
        ruleset = RuleSet()

        cat = Category(CategoryKey.from_string("python"), when="Python")
        cat.add_rule(Rule("Keep this rule", RuleType.COMMANDMENT))
        cat.add_rule(Rule("{% if false %}Remove this{% endif %}", RuleType.COMMANDMENT))
        cat.add_rule(Rule("Keep this too", RuleType.COMMANDMENT))
        ruleset.add_category(cat)

        merged = MergedScope(
            metadata=metadata,
            commandments=ruleset,
            suggestions=RuleSet(),
            sources=["local"],
        )

        # Mock renderer that returns empty string for the second rule
        renderer = MockTemplateRenderer({"{% if false %}Remove this{% endif %}"})
        formatter = JsonFormatter(template_renderer=renderer)
        result = formatter.format(merged)

        # Check that only 2 rules remain
        assert len(result["commandments"]["python"]["rules"]) == 2
        assert "Keep this rule" in result["commandments"]["python"]["rules"]
        assert "Keep this too" in result["commandments"]["python"]["rules"]

    def test_prunes_empty_categories(self):
        """Test that categories with no rules after pruning are removed."""
        metadata = ScopeMetadata(name="test", description="Test")
        ruleset = RuleSet()

        # Category with all empty rules
        cat1 = Category(CategoryKey.from_string("python"), when="Python")
        cat1.add_rule(Rule("{% if false %}Empty 1{% endif %}", RuleType.COMMANDMENT))
        cat1.add_rule(Rule("{% if false %}Empty 2{% endif %}", RuleType.COMMANDMENT))
        ruleset.add_category(cat1)

        # Category with at least one non-empty rule
        cat2 = Category(CategoryKey.from_string("python.web"), when="Web")
        cat2.add_rule(Rule("Keep this", RuleType.COMMANDMENT))
        ruleset.add_category(cat2)

        merged = MergedScope(
            metadata=metadata,
            commandments=ruleset,
            suggestions=RuleSet(),
            sources=["local"],
        )

        # Mock renderer that returns empty for cat1's rules
        renderer = MockTemplateRenderer(
            {"{% if false %}Empty 1{% endif %}", "{% if false %}Empty 2{% endif %}"}
        )
        formatter = JsonFormatter(template_renderer=renderer)
        result = formatter.format(merged)

        # Check that python category is pruned but python.web remains
        assert "python" not in result["commandments"]
        assert "python.web" in result["commandments"]

    def test_handles_whitespace_only_rules(self):
        """Test that rules with only whitespace are pruned."""
        metadata = ScopeMetadata(name="test", description="Test")
        ruleset = RuleSet()

        cat = Category(CategoryKey.from_string("python"), when="Python")
        cat.add_rule(Rule("Keep this", RuleType.COMMANDMENT))
        cat.add_rule(Rule("whitespace_only", RuleType.COMMANDMENT))
        ruleset.add_category(cat)

        merged = MergedScope(
            metadata=metadata,
            commandments=ruleset,
            suggestions=RuleSet(),
            sources=["local"],
        )

        # Mock renderer that returns whitespace for second rule
        class WhitespaceRenderer:
            def render_rule_text(
                self, text, scope, category=None, failure_collector=None, rule_index=None
            ):
                if text == "whitespace_only":
                    return "   \n\t  "
                return text

        formatter = JsonFormatter(template_renderer=WhitespaceRenderer())
        result = formatter.format(merged)

        # Only the non-empty rule should remain
        assert len(result["commandments"]["python"]["rules"]) == 1
        assert result["commandments"]["python"]["rules"][0] == "Keep this"


class TestMarkdownFormatterPruning:
    """Tests for Markdown formatter pruning."""

    def test_prunes_empty_rules(self):
        """Test that empty rules after rendering are pruned from markdown."""
        metadata = ScopeMetadata(name="test", description="Test")
        ruleset = RuleSet()

        cat = Category(CategoryKey.from_string("python"), when="Python")
        cat.add_rule(Rule("Keep this rule", RuleType.COMMANDMENT))
        cat.add_rule(Rule("{% if false %}Remove this{% endif %}", RuleType.COMMANDMENT))
        ruleset.add_category(cat)

        merged = MergedScope(
            metadata=metadata,
            commandments=ruleset,
            suggestions=RuleSet(),
            sources=["local"],
        )

        renderer = MockTemplateRenderer({"{% if false %}Remove this{% endif %}"})
        formatter = MarkdownFormatter(template_renderer=renderer)
        result = formatter.format(merged)

        # Check that only the kept rule appears in markdown
        assert "Keep this rule" in result
        assert "Remove this" not in result

    def test_prunes_empty_categories(self):
        """Test that categories with no rules are not shown in markdown."""
        metadata = ScopeMetadata(name="test", description="Test")
        ruleset = RuleSet()

        # Category with all empty rules
        cat1 = Category(CategoryKey.from_string("empty"), when="Empty category")
        cat1.add_rule(Rule("{% if false %}Empty{% endif %}", RuleType.COMMANDMENT))
        ruleset.add_category(cat1)

        # Category with non-empty rules
        cat2 = Category(CategoryKey.from_string("python"), when="Python")
        cat2.add_rule(Rule("Keep this", RuleType.COMMANDMENT))
        ruleset.add_category(cat2)

        merged = MergedScope(
            metadata=metadata,
            commandments=ruleset,
            suggestions=RuleSet(),
            sources=["local"],
        )

        renderer = MockTemplateRenderer({"{% if false %}Empty{% endif %}"})
        formatter = MarkdownFormatter(template_renderer=renderer)
        result = formatter.format(merged)

        # Empty category heading should not appear
        assert "## empty" not in result
        assert "Empty category" not in result
        # But python category should appear
        assert "## python" in result
        assert "Keep this" in result

    def test_prunes_empty_subcategories(self):
        """Test that parent categories with only empty children are pruned."""
        metadata = ScopeMetadata(name="test", description="Test")
        ruleset = RuleSet()

        # Parent category with no rules
        cat1 = Category(CategoryKey.from_string("python"), when="Python")
        ruleset.add_category(cat1)

        # Child category with all empty rules
        cat2 = Category(CategoryKey.from_string("python.web"), when="Web")
        cat2.add_rule(Rule("{% if false %}Empty{% endif %}", RuleType.COMMANDMENT))
        ruleset.add_category(cat2)

        merged = MergedScope(
            metadata=metadata,
            commandments=ruleset,
            suggestions=RuleSet(),
            sources=["local"],
        )

        renderer = MockTemplateRenderer({"{% if false %}Empty{% endif %}"})
        formatter = MarkdownFormatter(template_renderer=renderer)
        result = formatter.format(merged)

        # Both parent and child should be pruned
        assert "## python" not in result
        assert "### web" not in result


class TestYamlFormatterPruning:
    """Tests for YAML formatter pruning."""

    def test_prunes_empty_rules(self):
        """Test that empty rules are pruned from YAML output."""
        metadata = ScopeMetadata(name="test", description="Test")
        ruleset = RuleSet()

        cat = Category(CategoryKey.from_string("python"), when="Python")
        cat.add_rule(Rule("Keep this", RuleType.COMMANDMENT))
        cat.add_rule(Rule("{% if false %}Remove{% endif %}", RuleType.COMMANDMENT))
        ruleset.add_category(cat)

        merged = MergedScope(
            metadata=metadata,
            commandments=ruleset,
            suggestions=RuleSet(),
            sources=["local"],
        )

        renderer = MockTemplateRenderer({"{% if false %}Remove{% endif %}"})
        formatter = YamlMultiDocFormatter(template_renderer=renderer)
        result = formatter.format(merged)

        # Parse the YAML and check
        import yaml

        docs = list(yaml.safe_load_all(result))
        commandments = docs[1]["commandments"]

        assert len(commandments["python"]["ruleset"]) == 1
        assert commandments["python"]["ruleset"][0] == "Keep this"

    def test_prunes_empty_categories(self):
        """Test that categories with no rules are pruned from YAML."""
        metadata = ScopeMetadata(name="test", description="Test")
        ruleset = RuleSet()

        # Category with all empty rules
        cat1 = Category(CategoryKey.from_string("empty"), when="Empty")
        cat1.add_rule(Rule("{% if false %}Empty{% endif %}", RuleType.COMMANDMENT))
        ruleset.add_category(cat1)

        # Category with non-empty rules
        cat2 = Category(CategoryKey.from_string("python"), when="Python")
        cat2.add_rule(Rule("Keep this", RuleType.COMMANDMENT))
        ruleset.add_category(cat2)

        merged = MergedScope(
            metadata=metadata,
            commandments=ruleset,
            suggestions=RuleSet(),
            sources=["local"],
        )

        renderer = MockTemplateRenderer({"{% if false %}Empty{% endif %}"})
        formatter = YamlMultiDocFormatter(template_renderer=renderer)
        result = formatter.format(merged)

        import yaml

        docs = list(yaml.safe_load_all(result))
        commandments = docs[1]["commandments"]

        # Empty category should not be in output
        assert "empty" not in commandments
        assert "python" in commandments


class TestCrossCategoryPruning:
    """Test pruning across commandments and suggestions."""

    def test_prunes_across_commandments_and_suggestions(self):
        """Test that pruning works independently for commandments and suggestions."""
        metadata = ScopeMetadata(name="test", description="Test")

        # Commandments with empty category
        commandments = RuleSet()
        cmd_cat = Category(CategoryKey.from_string("python"), when="Python")
        cmd_cat.add_rule(Rule("{% if false %}Empty{% endif %}", RuleType.COMMANDMENT))
        commandments.add_category(cmd_cat)

        # Suggestions with non-empty category
        suggestions = RuleSet()
        sug_cat = Category(CategoryKey.from_string("python"), when="Python")
        sug_cat.add_rule(Rule("Keep this suggestion", RuleType.SUGGESTION))
        suggestions.add_category(sug_cat)

        merged = MergedScope(
            metadata=metadata,
            commandments=commandments,
            suggestions=suggestions,
            sources=["local"],
        )

        renderer = MockTemplateRenderer({"{% if false %}Empty{% endif %}"})
        formatter = JsonFormatter(template_renderer=renderer)
        result = formatter.format(merged)

        # Python should be pruned from commandments but not suggestions
        assert "python" not in result["commandments"]
        assert "python" in result["suggestions"]
        assert len(result["suggestions"]["python"]["rules"]) == 1


__all__ = [
    "TestJsonFormatterPruning",
    "TestMarkdownFormatterPruning",
    "TestYamlFormatterPruning",
    "TestCrossCategoryPruning",
]
