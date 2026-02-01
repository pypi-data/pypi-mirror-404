"""FastMCP server for Daimyo rules."""

from fastmcp import FastMCP

from daimyo.application.error_handling import ErrorMapper
from daimyo.application.formatters import IndexMarkdownFormatter, MarkdownFormatter
from daimyo.application.validation import (
    ValidationError,
    sanitize_for_logging,
    validate_categories,
    validate_scope_name,
)
from daimyo.config.settings import settings
from daimyo.infrastructure.di import get_container
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)

_container = get_container()
_scope_service = _container.scope_service()
_filter_service = _container.category_filter_service()
_scope_repository = _container.scope_repository()
_template_renderer = _container.template_renderer()

mcp = FastMCP("Daimyo Rules Server")


@mcp.tool()
def get_rules(scope_name: str | None = None, categories: str | None = None) -> str:
    """Get rules for a scope in markdown format.

    The rules of a given category include also the rules of all its subcategories.\f

    :param scope_name: Name of the scope to retrieve (e.g., 'python-general', 'team-backend').
                       If not provided and a DEFAULT_SCOPE is configured, uses the default scope.
    :type scope_name: str | None
    :param categories: Optional comma-separated category filters (e.g., 'python.web,python.testing')
    :type categories: str | None
    :returns: Markdown-formatted rules with hierarchy, MUST/SHOULD markers, and descriptions
    :rtype: str

    Examples::

        get_rules("python-general")
        get_rules("team-backend", "python.web")
        get_rules()  # Uses default scope if configured
    """
    try:
        used_default = False
        if scope_name is None:
            scope_name = settings.DEFAULT_SCOPE
            if not scope_name:
                return (
                    "Error: No scope name provided and no default scope configured. "
                    "Please provide a scope_name parameter or configure DEFAULT_SCOPE."
                )
            used_default = True

        try:
            validate_scope_name(scope_name)
            validate_categories(categories)
        except ValidationError as e:
            return f"Error: {e}"

        logger.info(
            f"MCP get_rules: scope={sanitize_for_logging(scope_name)}, "
            f"categories={sanitize_for_logging(categories, max_length=500, is_comma_list=True)}, "
            f"used_default={used_default}"
        )

        merged_scope = _scope_service.resolve_scope(scope_name)
        merged_scope = _filter_service.filter_from_string(merged_scope, categories)

        formatter = MarkdownFormatter(template_renderer=_template_renderer)
        result = formatter.format(merged_scope)

        if used_default:
            result = f"> **Note:** Using default scope: `{scope_name}`\n\n{result}"

        logger.info(f"Successfully retrieved rules for scope '{sanitize_for_logging(scope_name)}'")
        return result

    except Exception as e:
        return ErrorMapper.map_to_error_string(e, context=scope_name if scope_name else "default")


@mcp.tool()
def get_category_index(scope_name: str | None = None) -> str:
    """Get a hierarchical index of all available categories in a scope.

    Returns a list of all categories with their descriptions to help determine
    which categories are relevant before requesting specific rules.\f

    :param scope_name: Name of the scope to retrieve categories from.
                       If not provided and a DEFAULT_SCOPE is configured, uses the default scope.
    :type scope_name: str | None
    :returns: Markdown-formatted hierarchical list of categories with descriptions
    :rtype: str

    Examples::

        get_category_index("python-general")
        get_category_index("team-backend")
        get_category_index()  # Uses default scope if configured
    """
    try:
        used_default = False
        if scope_name is None:
            scope_name = settings.DEFAULT_SCOPE
            if not scope_name:
                return (
                    "Error: No scope name provided and no default scope configured. "
                    "Please provide a scope_name parameter or configure DEFAULT_SCOPE."
                )
            used_default = True

        try:
            validate_scope_name(scope_name)
        except ValidationError as e:
            return f"Error: {e}"

        logger.info(
            f"MCP get_category_index: scope={sanitize_for_logging(scope_name)}, "
            f"used_default={used_default}"
        )

        merged_scope = _scope_service.resolve_scope(scope_name)

        formatter = IndexMarkdownFormatter(template_renderer=_template_renderer)
        result = formatter.format(merged_scope)

        if used_default:
            result = f"> **Note:** Using default scope: `{scope_name}`\n\n{result}"

        logger.info(
            f"Successfully retrieved category index for scope '{sanitize_for_logging(scope_name)}'"
        )
        return result

    except Exception as e:
        return ErrorMapper.map_to_error_string(e, context=scope_name if scope_name else "default")


@mcp.prompt()
def apply_scope_rules(scope_name: str | None = None, categories: str | None = None) -> str:
    """Prompt template to apply scope rules to an agent.\f

    :param scope_name: Name of the scope to apply.
                       If not provided and a DEFAULT_SCOPE is configured, uses the default scope.
    :type scope_name: str | None
    :param categories: Optional comma-separated category filters
    :type categories: str | None
    :returns: Formatted prompt with rules for the agent to follow
    :rtype: str
    """
    try:
        if scope_name is None:
            scope_name = settings.DEFAULT_SCOPE
            if not scope_name:
                return (
                    "Error: No scope name provided and no default scope configured. "
                    "Please provide a scope_name parameter or configure DEFAULT_SCOPE."
                )

        try:
            validate_scope_name(scope_name)
            validate_categories(categories)
        except ValidationError as e:
            return f"Error: {e}"

        logger.info(
            f"MCP apply_scope_rules: scope={sanitize_for_logging(scope_name)}, "
            f"categories={sanitize_for_logging(categories, max_length=500, is_comma_list=True)}"
        )
        rules = get_rules.fn(scope_name, categories)

        prompt = f"""You are an AI agent that must follow these rules from the '{scope_name}' scope.

{rules}

Instructions:
1. **MUST rules (Commandments)**: These are mandatory and cannot be violated
2. **SHOULD rules (Suggestions)**: These are strong recommendations you should
   follow unless you have a good reason not to

Apply these rules to all your actions, recommendations, and code generation.
When rules conflict, commandments take precedence over suggestions.
"""
        return prompt

    except Exception as e:
        error_msg = f"Error generating prompt: {str(e)}"
        logger.exception(error_msg)
        return error_msg


__all__ = ["mcp"]
