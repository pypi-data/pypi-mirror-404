"""Scopes API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from daimyo.application.error_handling import ErrorMapper
from daimyo.application.filtering import CategoryFilterService
from daimyo.application.formatters import (
    IndexMarkdownFormatter,
    JsonFormatter,
    MarkdownFormatter,
    YamlMultiDocFormatter,
)
from daimyo.application.scope_service import ScopeResolutionService
from daimyo.application.validation import (
    ValidationError,
    sanitize_for_logging,
    validate_categories,
    validate_scope_name,
)
from daimyo.infrastructure.di import get_container
from daimyo.infrastructure.logging import get_logger
from daimyo.presentation.rest.dependencies import (
    get_category_filter_service,
    get_scope_service,
)
from daimyo.presentation.rest.models import CategorySummary, ErrorResponse, IndexResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/scopes", tags=["scopes"])


@router.get(
    "",
    response_model=list[str],
    responses={
        200: {
            "description": "List of available scope names",
            "content": {
                "application/json": {"example": ["python-general", "team-backend", "team-frontend"]}
            },
        },
        500: {"model": ErrorResponse},
    },
    summary="List all available scopes",
    description="Returns a list of all scope names available on this server.",
)
async def list_scopes(
    scope_service: Annotated[ScopeResolutionService, Depends(get_scope_service)],
) -> list[str]:
    """List all available scopes.

    :param scope_service: Scope resolution service
    :type scope_service: ScopeResolutionService
    :returns: List of scope names
    :rtype: list[str]
    """
    try:
        logger.info("GET /api/v1/scopes")
        repository = scope_service.get_repository()
        scopes = repository.list_scopes()
        return scopes
    except Exception as e:
        raise ErrorMapper.map_to_http_exception(e, context="list_scopes")


@router.get(
    "/{name}/index",
    response_model=None,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "scope_name": "python-general",
                        "description": "General Python rules",
                        "commandments": [],
                        "suggestions": [],
                        "sources": ["local"],
                    }
                },
                "text/markdown": {
                    "example": (
                        "# Index of rule categories for scope python-general\n\n"
                        "- `python`\n  - `python.web`: When building web applications"
                    )
                },
            },
        },
        404: {"model": ErrorResponse},
        406: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get category index for a scope",
    description=(
        "Returns a summary of all categories in the scope with their descriptions "
        "via Accept header. Supports application/json and text/markdown. "
        "Helps agents determine which categories are relevant before requesting full rules."
    ),
)
async def get_scope_index(
    request: Request,
    name: str,
    scope_service: Annotated[ScopeResolutionService, Depends(get_scope_service)],
    debug: Annotated[
        bool,
        Query(description="Skip template expansion and return raw content (default: false)"),
    ] = False,
) -> Response | IndexResponse:
    """Get category index for a scope.

    :param request: HTTP request object
    :type request: Request
    :param name: Scope name
    :type name: str
    :param scope_service: Scope resolution service
    :type scope_service: ScopeResolutionService
    :param debug: Skip template expansion (default: False)
    :type debug: bool
    :returns: Index with all categories and descriptions in JSON or Markdown format
    :rtype: Response | IndexResponse
    """
    try:
        validate_scope_name(name)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    accept_header = request.headers.get("accept", "application/json")

    format_type = "json"
    if "text/markdown" in accept_header:
        format_type = "markdown"
    elif "application/json" not in accept_header:
        raise HTTPException(
            status_code=406,
            detail="Not Acceptable. Supported media types: application/json, text/markdown",
        )

    try:
        logger.info(
            f"GET /api/v1/scopes/{sanitize_for_logging(name)}/index"
            f"?debug={debug} Accept={sanitize_for_logging(accept_header, max_length=100)}"
        )
        merged_scope = scope_service.resolve_scope(name)

        if format_type == "markdown":
            container = get_container()
            template_renderer = None if debug else container.template_renderer()

            formatter = IndexMarkdownFormatter(template_renderer=template_renderer)
            content = formatter.format(merged_scope)
            return Response(content=content, media_type="text/markdown")
        else:
            commandment_summaries = [
                CategorySummary(
                    category=str(cat.key), when=cat.when, rule_count=len(cat.rules), tags=cat.tags
                )
                for cat in merged_scope.commandments.categories.values()
            ]

            suggestion_summaries = [
                CategorySummary(
                    category=str(cat.key), when=cat.when, rule_count=len(cat.rules), tags=cat.tags
                )
                for cat in merged_scope.suggestions.categories.values()
            ]

            return IndexResponse(
                scope_name=name,
                description=merged_scope.metadata.description,
                commandments=commandment_summaries,
                suggestions=suggestion_summaries,
                sources=merged_scope.sources,
            )

    except Exception as e:
        raise ErrorMapper.map_to_http_exception(e, context=name)


@router.get(
    "/{name}/rules",
    response_model=None,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "metadata": {
                            "name": "python-general",
                            "description": "General Python rules",
                        },
                        "commandments": {},
                        "suggestions": {},
                    }
                },
                "application/x-yaml": {
                    "example": (
                        "---\nmetadata:\n  name: python-general\n---\n"
                        "commandments: {}\n---\nsuggestions: {}"
                    )
                },
                "text/markdown": {
                    "example": (
                        "# Rules for python-general\n\n## python\n\n"
                        "- **MUST**: Use type hints\n- **SHOULD**: Add docstrings"
                    )
                },
            },
        },
        404: {"model": ErrorResponse},
        406: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get rules for a scope",
    description=(
        "Returns rules for a scope in the requested format via Accept header. "
        "Supports application/json, application/x-yaml, and text/markdown."
    ),
)
async def get_scope_rules(
    request: Request,
    name: str,
    scope_service: Annotated[ScopeResolutionService, Depends(get_scope_service)],
    filter_service: Annotated[CategoryFilterService, Depends(get_category_filter_service)],
    categories: Annotated[
        str | None,
        Query(description="Comma-separated category filters (e.g., 'python.web,python.testing')"),
    ] = None,
    debug: Annotated[
        bool,
        Query(description="Skip template expansion and return raw content (default: false)"),
    ] = False,
) -> Response | dict:
    """Get rules for a scope.

    :param request: HTTP request object
    :type request: Request
    :param name: Scope name
    :type name: str
    :param scope_service: Scope resolution service
    :type scope_service: ScopeResolutionService
    :param filter_service: Category filter service
    :type filter_service: CategoryFilterService
    :param categories: Comma-separated list of category prefixes (uses prefix matching)
    :type categories: str | None
    :param debug: Skip template expansion (default: False)
    :type debug: bool
    :returns: YAML multi-document, JSON, or Markdown with structured data
    :rtype: Response | dict
    """
    try:
        validate_scope_name(name)
        validate_categories(categories)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    accept_header = request.headers.get("accept", "application/x-yaml")

    content_type_map = {
        "application/json": ("json", JsonFormatter, "application/json"),
        "application/x-yaml": ("yaml", YamlMultiDocFormatter, "application/x-yaml"),
        "application/yaml": ("yaml", YamlMultiDocFormatter, "application/x-yaml"),
        "text/markdown": ("markdown", MarkdownFormatter, "text/markdown"),
    }

    formatter_info = None
    for mime_type, info in content_type_map.items():
        if mime_type in accept_header:
            formatter_info = info
            break

    if formatter_info is None:
        raise HTTPException(
            status_code=406,
            detail=f"Not Acceptable. Supported media types: {', '.join(content_type_map.keys())}",
        )

    format_name, formatter_class, content_type = formatter_info

    try:
        logger.info(
            f"GET /api/v1/scopes/{sanitize_for_logging(name)}/rules"
            f"?categories={sanitize_for_logging(categories, max_length=500, is_comma_list=True)}"
            f"&debug={debug} Accept={sanitize_for_logging(accept_header, max_length=100)}"
        )

        merged_scope = scope_service.resolve_scope(name)
        merged_scope = filter_service.filter_from_string(merged_scope, categories)

        container = get_container()
        template_renderer = None if debug else container.template_renderer()

        formatter = formatter_class(template_renderer=template_renderer)  # type: ignore[operator]
        content = formatter.format(merged_scope)  # type: ignore[attr-defined]

        if format_name == "json":
            return content  # type: ignore[no-any-return]
        else:
            return Response(content=content, media_type=content_type)

    except Exception as e:
        raise ErrorMapper.map_to_http_exception(e, context=name)


__all__ = ["router"]
