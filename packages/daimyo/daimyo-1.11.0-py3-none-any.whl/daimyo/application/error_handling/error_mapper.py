"""Error mapping service for converting domain exceptions to presentation layer responses."""

from __future__ import annotations

from fastapi import HTTPException

from daimyo.domain import DaimyoError, ScopeNotFoundError, TemplateRenderingError
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ErrorMapper:
    """Maps domain exceptions to presentation layer responses.

    Provides centralized error handling logic for both REST and MCP endpoints,
    ensuring consistent error messages and logging across the application.
    """

    @staticmethod
    def map_to_http_exception(error: Exception, context: str = "") -> HTTPException:
        """Map domain exception to HTTP exception with safe error messages.

        Always returns generic error messages to clients while logging
        detailed errors server-side for debugging.

        :param error: Exception to map
        :type error: Exception
        :param context: Additional context for logging (e.g., scope name)
        :type context: str
        :returns: HTTP exception with appropriate status code and generic message
        :rtype: HTTPException

        Examples::

            try:
                business_logic()
            except Exception as e:
                raise ErrorMapper.map_to_http_exception(e, context=scope_name)
        """
        if isinstance(error, ScopeNotFoundError):
            logger.warning(f"Scope not found: {context}")
            return HTTPException(status_code=404, detail=str(error))
        elif isinstance(error, TemplateRenderingError):
            logger.warning(f"Template rendering error: {context} - {error}")
            return HTTPException(status_code=422, detail="Template rendering failed")
        elif isinstance(error, DaimyoError):
            logger.error(f"Daimyo error: {context} - {error}")
            return HTTPException(status_code=500, detail="Internal error occurred")
        else:
            logger.exception(f"Unexpected error: {context}")
            return HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def map_to_error_string(error: Exception, context: str = "") -> str:
        """Map domain exception to error string for MCP/CLI.

        Always returns generic error messages while logging detailed errors.

        :param error: Exception to map
        :type error: Exception
        :param context: Additional context for logging (e.g., scope name)
        :type context: str
        :returns: Generic error message string
        :rtype: str

        Examples::

            try:
                business_logic()
            except Exception as e:
                return ErrorMapper.map_to_error_string(e, context=scope_name)
        """
        if isinstance(error, ScopeNotFoundError):
            logger.warning(f"Scope not found: {context}")
            return f"Scope Error: {str(error)}"
        elif isinstance(error, TemplateRenderingError):
            logger.warning(f"Template rendering error: {context} - {error}")
            return "Template Error: Template rendering failed"
        elif isinstance(error, DaimyoError):
            logger.error(f"Daimyo error: {context} - {error}")
            return "Daimyo Error: Internal error occurred"
        else:
            logger.exception(f"Unexpected error: {context}")
            return "Error: An unexpected error occurred"


__all__ = ["ErrorMapper"]
