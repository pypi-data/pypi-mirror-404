"""Domain models for Daimyo rules server."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RuleType(Enum):
    """Type of rule - mandatory or suggested."""

    COMMANDMENT = "commandment"
    SUGGESTION = "suggestion"


@dataclass(frozen=True)
class Rule:
    """Individual rule statement.

    :param text: The rule text
    :type text: str
    :param rule_type: Whether this is a commandment (MUST) or suggestion (SHOULD)
    :type rule_type: RuleType
    """

    text: str
    rule_type: RuleType

    def __str__(self) -> str:
        """Format rule with MUST/SHOULD prefix.

        :returns: Formatted rule string with prefix
        :rtype: str
        """
        prefix = "MUST" if self.rule_type == RuleType.COMMANDMENT else "SHOULD"
        return f"{prefix}: {self.text}"


@dataclass(frozen=True)
class TemplateFailure:
    """Information about a template rendering failure.

    :param element_type: Type of element that failed
    :type element_type: str
    :param element_identifier: Human-readable identifier
    :type element_identifier: str
    :param template_text: Original template text (truncated)
    :type template_text: str
    :param error_message: Error message from template engine
    :type error_message: str
    :param variable_name: Undefined variable name if applicable
    :type variable_name: str | None
    """

    element_type: str
    element_identifier: str
    template_text: str
    error_message: str
    variable_name: str | None = None


@dataclass(frozen=True)
class CategoryKey:
    """Represents a category path like 'python.web.testing'.

    Categories form a universal namespace shared across all scopes. Multiple scopes
    can contain rules for the same category, and these rules are merged during
    scope resolution. Categories are hierarchical and used for filtering rules.

    Immutable to allow use as dictionary keys.

    :param parts: Tuple of category path parts
    :type parts: tuple[str, ...]
    """

    parts: tuple[str, ...]

    @classmethod
    def from_string(cls, category: str) -> CategoryKey:
        """Create CategoryKey from dot-separated string.

        :param category: Category path like "python.web.testing"
        :type category: str
        :returns: CategoryKey instance
        :rtype: CategoryKey
        """
        cleaned = category.lstrip("+")
        return cls(parts=tuple(cleaned.split(".")))

    def __str__(self) -> str:
        """Convert back to dot-separated string.

        :returns: Dot-separated category string
        :rtype: str
        """
        return ".".join(self.parts)

    def matches_prefix(self, prefix: CategoryKey) -> bool:
        """Check if this category starts with the given prefix.

        :param prefix: The prefix to check
        :type prefix: CategoryKey
        :returns: True if this category starts with the prefix
        :rtype: bool
        """
        if len(prefix.parts) > len(self.parts):
            return False
        return self.parts[: len(prefix.parts)] == prefix.parts

    def depth(self) -> int:
        """Return the depth of this category.

        :returns: Number of parts in the category path
        :rtype: int
        """
        return len(self.parts)


@dataclass
class Category:
    """A category of rules with applicability description and ruleset.

    :param key: The category key (e.g., python.web.testing)
    :type key: CategoryKey
    :param when: Description of when these rules apply
    :type when: str | None
    :param rules: List of rules for this category
    :type rules: List[Rule]
    :param tags: List of tags for this category
    :type tags: List[str]
    :param append_to_parent: Whether to append to parent category (for suggestions)
    :type append_to_parent: bool
    """

    key: CategoryKey
    when: str | None = None
    rules: list[Rule] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    append_to_parent: bool = False

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to this category.

        :param rule: Rule to add
        :type rule: Rule
        :rtype: None
        """
        self.rules.append(rule)

    def copy(self) -> Category:
        """Create a deep copy of this category.

        :returns: Copied category with new list instance
        :rtype: Category
        """
        return Category(
            key=self.key,
            when=self.when,
            rules=self.rules.copy(),
            tags=self.tags.copy(),
            append_to_parent=self.append_to_parent,
        )


@dataclass
class RuleSet:
    """Collection of rules organized by category.

    Used to represent either commandments or suggestions for a scope.

    :param categories: Dictionary mapping category keys to categories
    :type categories: Dict[CategoryKey, Category]
    """

    categories: dict[CategoryKey, Category] = field(default_factory=dict)

    def add_category(self, category: Category) -> None:
        """Add or update a category.

        :param category: Category to add
        :type category: Category
        :rtype: None
        """
        self.categories[category.key] = category

    def get_category(self, key: CategoryKey) -> Category | None:
        """Get a category by key.

        :param key: Category key to retrieve
        :type key: CategoryKey
        :returns: Category if found, None otherwise
        :rtype: Category | None
        """
        return self.categories.get(key)

    def get_matching_categories(self, prefix: str | None = None) -> list[Category]:
        """Get all categories matching the prefix.

        :param prefix: Optional prefix to filter by (e.g., "python.web").
                       If None, returns all categories
        :type prefix: Optional[str]
        :returns: List of matching categories
        :rtype: List[Category]
        """
        if prefix is None:
            return list(self.categories.values())

        prefix_key = CategoryKey.from_string(prefix)
        return [
            cat
            for cat in self.categories.values()
            if cat.key.matches_prefix(prefix_key) or cat.key == prefix_key
        ]

    def copy(self) -> RuleSet:
        """Create a deep copy of this ruleset.

        :returns: Copied ruleset with new category instances
        :rtype: RuleSet
        """
        new_ruleset = RuleSet()
        for cat in self.categories.values():
            new_ruleset.add_category(cat.copy())
        return new_ruleset


@dataclass
class ScopeMetadata:
    """Metadata for a scope.

    :param name: Scope name (e.g., "team-backend", "project-xyz")
    :type name: str
    :param description: Human-readable description
    :type description: str
    :param parent: Optional parent scope for inheritance (deprecated, use parents)
    :type parent: Optional[str]
    :param parents: Optional list of parent scopes for multiple inheritance
    :type parents: Optional[list[str]]
    :param tags: Optional tags for categorization
    :type tags: Dict[str, str]
    """

    name: str
    description: str
    parent: str | None = None
    parents: list[str] | None = None
    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        from daimyo.domain.exceptions import InvalidScopeError

        if self.parent is not None and self.parents is not None:
            raise InvalidScopeError(
                "Cannot specify both 'parent' and 'parents'. "
                "Use 'parents' for single or multiple parents."
            )

    def get_parent_list(self) -> list[str]:
        if self.parents is not None:
            return self.parents if self.parents else []
        if self.parent is not None:
            return [self.parent]
        return []


@dataclass
class Scope:
    """A scope with metadata and rules.

    Scopes represent organizational contexts (company, team, project).
    Each scope has commandments (mandatory rules) and suggestions (recommended rules).

    :param metadata: Scope metadata
    :type metadata: ScopeMetadata
    :param commandments: Mandatory rules organized by category
    :type commandments: RuleSet
    :param suggestions: Recommended rules organized by category
    :type suggestions: RuleSet
    :param source: Source identifier (e.g., "local" or remote URL)
    :type source: str
    """

    metadata: ScopeMetadata
    commandments: RuleSet = field(default_factory=RuleSet)
    suggestions: RuleSet = field(default_factory=RuleSet)
    source: str = "local"

    def get_all_category_keys(self) -> set[CategoryKey]:
        """Get all unique category keys from both commandments and suggestions.

        :returns: Set of all category keys
        :rtype: set[CategoryKey]
        """
        return set(self.commandments.categories.keys()) | set(self.suggestions.categories.keys())


@dataclass
class MergedScope:
    """A scope after merging with parent and remote shards.

    This represents the final, resolved scope after applying inheritance
    and merging rules from multiple sources.

    :param metadata: Scope metadata (from child scope)
    :type metadata: ScopeMetadata
    :param commandments: Merged commandments
    :type commandments: RuleSet
    :param suggestions: Merged suggestions
    :type suggestions: RuleSet
    :param sources: List of sources that contributed to this merged scope
    :type sources: List[str]
    :param template_failures: List of template rendering failures
    :type template_failures: List[TemplateFailure]
    """

    metadata: ScopeMetadata
    commandments: RuleSet
    suggestions: RuleSet
    sources: list[str] = field(default_factory=list)
    template_failures: list[TemplateFailure] = field(default_factory=list)

    def add_template_failure(
        self,
        element_type: str,
        element_identifier: str,
        template_text: str,
        error: Exception,
        variable_name: str | None = None,
    ) -> None:
        """Record a template rendering failure.

        :param element_type: Type of element that failed
        :type element_type: str
        :param element_identifier: Human-readable identifier
        :type element_identifier: str
        :param template_text: Original template text
        :type template_text: str
        :param error: The exception that was raised
        :type error: Exception
        :param variable_name: Undefined variable name if applicable
        :type variable_name: str | None
        :rtype: None
        """
        failure = TemplateFailure(
            element_type=element_type,
            element_identifier=element_identifier,
            template_text=template_text[:200],
            error_message=str(error),
            variable_name=variable_name,
        )
        self.template_failures.append(failure)

    @classmethod
    def from_scope(cls, scope: Scope) -> MergedScope:
        """Create a MergedScope from a single Scope.

        :param scope: The source scope
        :type scope: Scope
        :returns: MergedScope with the scope's data
        :rtype: MergedScope
        """
        return cls(
            metadata=scope.metadata,
            commandments=scope.commandments.copy(),
            suggestions=scope.suggestions.copy(),
            sources=[scope.source],
        )

    def copy(self) -> MergedScope:
        """Create a deep copy of this merged scope.

        :returns: Copied merged scope with new ruleset instances
        :rtype: MergedScope
        """
        return MergedScope(
            metadata=self.metadata,
            commandments=self.commandments.copy(),
            suggestions=self.suggestions.copy(),
            sources=self.sources.copy(),
            template_failures=self.template_failures.copy(),
        )


__all__ = [
    "Rule",
    "RuleType",
    "TemplateFailure",
    "Category",
    "CategoryKey",
    "RuleSet",
    "Scope",
    "ScopeMetadata",
    "MergedScope",
]
