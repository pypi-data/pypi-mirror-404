"""Input validation and sanitization for security.

This module provides centralized validation and sanitization functions
to prevent injection attacks and ensure safe logging practices.
"""

from __future__ import annotations

import re


class ValidationError(Exception):
    """Raised when input validation fails."""


SCOPE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
CATEGORY_PATTERN = re.compile(r"^[a-zA-Z0-9_.\-]+$")
MAX_SCOPE_NAME_LENGTH = 200
MAX_CATEGORIES_LENGTH = 10000


def sanitize_for_logging(
    value: str | None, max_length: int = 200, is_comma_list: bool = False
) -> str:
    """Sanitize user input for safe logging by removing control characters.

    Removes newlines, carriage returns, tabs, and other control characters
    that could be used for log injection attacks. Truncates long values
    to prevent log pollution.

    :param value: The value to sanitize
    :type value: str | None
    :param max_length: Maximum length before truncation
    :type max_length: int
    :param is_comma_list: If True, truncate by removing last comma-separated items
    :type is_comma_list: bool
    :returns: Sanitized string safe for logging
    :rtype: str
    """
    if value is None:
        return "None"
    sanitized = re.sub(r"[\n\r\t\x00-\x1f\x7f-\x9f]", "", str(value))

    if len(sanitized) <= max_length:
        return sanitized

    if is_comma_list:
        items = [item.strip() for item in sanitized.split(",")]
        result_items: list[str] = []
        current_length = 0

        for item in items:
            item_length = len(item) + (2 if result_items else 0)
            if current_length + item_length > max_length:
                break
            result_items.append(item)
            current_length += item_length

        return ", ".join(result_items)

    return sanitized[:max_length] + "..."


def validate_scope_name(scope_name: str | None) -> None:
    """Validate scope name format to prevent injection attacks.

    Ensures scope names contain only safe characters (alphanumeric,
    hyphens, underscores) and are not excessively long.

    :param scope_name: The scope name to validate
    :type scope_name: str | None
    :raises ValidationError: If scope name is invalid
    :returns: None
    :rtype: None
    """
    if scope_name is None:
        return

    if len(scope_name) > MAX_SCOPE_NAME_LENGTH:
        raise ValidationError(f"Scope name too long (max {MAX_SCOPE_NAME_LENGTH} characters)")

    if not SCOPE_NAME_PATTERN.match(scope_name):
        raise ValidationError(
            "Scope name must contain only alphanumeric characters, hyphens, and underscores"
        )


def validate_categories(categories: str | None) -> None:
    """Validate categories format to prevent injection attacks.

    Ensures category strings contain only safe characters and are
    properly formatted as comma-separated lists.

    :param categories: Comma-separated category list to validate
    :type categories: str | None
    :raises ValidationError: If categories string is invalid
    :returns: None
    :rtype: None
    """
    if categories is None:
        return

    if len(categories) > MAX_CATEGORIES_LENGTH:
        raise ValidationError(
            f"Categories string too long (max {MAX_CATEGORIES_LENGTH} characters)"
        )

    category_list = [c.strip() for c in categories.split(",")]
    for category in category_list:
        if not category or not CATEGORY_PATTERN.match(category):
            raise ValidationError(f"Invalid category format: {category}")
        if ".." in category:
            raise ValidationError(f"Invalid category format: {category}")


def sanitize_error_message(message: str | None, max_length: int = 200) -> str:
    """Sanitize error messages to prevent information disclosure.

    Removes sensitive information like file paths, line numbers,
    and internal details while keeping the message useful for debugging.

    :param message: The error message to sanitize
    :type message: str | None
    :param max_length: Maximum length before truncation
    :type max_length: int
    :returns: Sanitized error message
    :rtype: str
    """
    if message is None:
        return "Unknown error"

    sanitized = str(message)
    sanitized = re.sub(r"[\n\r\t\x00-\x1f\x7f-\x9f]", " ", sanitized)
    sanitized = re.sub(r"/[a-zA-Z0-9_\-./]+\.py", "[file]", sanitized)
    sanitized = re.sub(r"line \d+", "line [X]", sanitized)
    sanitized = re.sub(r'File "[^"]*"', 'File "[...]"', sanitized)

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized.strip()


__all__ = [
    "ValidationError",
    "sanitize_for_logging",
    "validate_scope_name",
    "validate_categories",
    "sanitize_error_message",
]
