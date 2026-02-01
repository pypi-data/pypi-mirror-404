"""HTTP client for fetching scopes from remote servers."""

from typing import Any
from urllib.parse import urljoin

import httpx

from daimyo.application.validation import sanitize_error_message
from daimyo.config import settings
from daimyo.domain import RemoteServerError, Scope, YAMLParseError
from daimyo.infrastructure.filesystem.yaml_parser import parse_metadata, parse_rules
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class HttpRemoteScopeClient:
    """HTTP client for fetching scopes from remote Daimyo servers.

    Fetches scopes via the REST API of remote servers.
    """

    def __init__(
        self,
        timeout: int | None = None,
        max_retries: int | None = None,
    ):
        """Initialize the HTTP client.

        :param timeout: Request timeout in seconds (defaults to config setting)
        :type timeout: Optional[int]
        :param max_retries: Maximum number of retries (defaults to config setting)
        :type max_retries: Optional[int]
        """
        self.timeout = timeout or settings.REMOTE_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.REMOTE_MAX_RETRIES

        transport = httpx.HTTPTransport(retries=self.max_retries)
        self.client = httpx.Client(
            transport=transport,
            timeout=self.timeout,
            follow_redirects=True,
        )

    def fetch_scope(self, base_url: str, scope_name: str) -> Scope | None:
        """Fetch a scope from a remote server.

        :param base_url: Base URL of the remote server (e.g., "https://remote.com")
        :type base_url: str
        :param scope_name: Name of the scope to fetch
        :type scope_name: str
        :returns: Scope instance if found, None otherwise
        :rtype: Optional[Scope]
        :raises RemoteServerError: If the remote server is unreachable or returns an error
        """
        try:
            api_url = urljoin(
                base_url.rstrip("/") + "/",
                f"api/v1/scopes/{scope_name}/rules?debug=true",
            )

            logger.debug(f"Fetching scope '{scope_name}' from {api_url}")

            response = self.client.get(api_url, headers={"Accept": "application/json"})

            if response.status_code == 404:
                logger.debug(f"Scope '{scope_name}' not found at {base_url}")
                return None

            if response.status_code != 200:
                raise RemoteServerError(
                    f"Remote server returned status {response.status_code}: "
                    f"{sanitize_error_message(response.text, max_length=200)}"
                )

            json_content = response.json()
            scope = self._parse_json(json_content, scope_name, base_url)

            logger.info(f"Successfully fetched scope '{scope_name}' from {base_url}")
            return scope

        except httpx.TimeoutException as e:
            raise RemoteServerError(
                f"Timeout fetching scope '{scope_name}' from {base_url}: {e}",
                url=base_url,
                status_code=None,
            )
        except httpx.ConnectError as e:
            raise RemoteServerError(
                f"Connection error fetching scope '{scope_name}' from {base_url}: {e}",
                url=base_url,
                status_code=None,
            )
        except httpx.HTTPError as e:
            status_code = getattr(e, "response", None)
            status_code = getattr(status_code, "status_code", None) if status_code else None
            raise RemoteServerError(
                f"HTTP error fetching scope '{scope_name}' from {base_url}: {e}",
                url=base_url,
                status_code=status_code,
            )
        except YAMLParseError as e:
            raise RemoteServerError(
                f"Failed to parse scope '{scope_name}' from {base_url}: {e}",
                url=base_url,
                status_code=200,
            )
        except OSError as e:
            raise RemoteServerError(
                f"I/O error fetching scope '{scope_name}' from {base_url}: {e}",
                url=base_url,
                status_code=None,
            )
        except Exception as e:
            logger.exception(f"Unexpected error fetching scope '{scope_name}' from {base_url}")
            raise RemoteServerError(
                f"Unexpected error fetching scope '{scope_name}' from {base_url}: "
                f"{type(e).__name__}: {e}",
                url=base_url,
                status_code=None,
            )

    def list_scopes(self, base_url: str) -> list[str] | None:
        """List available scopes from a remote server.

        :param base_url: Base URL of the remote server
        :type base_url: str
        :returns: List of scope names if found, None on error
        :rtype: Optional[list[str]]
        :raises RemoteServerError: If the remote server is unreachable or returns an error
        """
        try:
            api_url = urljoin(
                base_url.rstrip("/") + "/",
                "api/v1/scopes",
            )

            logger.debug(f"Listing scopes from {api_url}")

            response = self.client.get(api_url, headers={"Accept": "application/json"})

            if response.status_code == 404:
                logger.debug(f"Scopes endpoint not found at {base_url}")
                return None

            if response.status_code != 200:
                raise RemoteServerError(
                    f"Remote server returned status {response.status_code}: "
                    f"{sanitize_error_message(response.text, max_length=200)}"
                )

            scopes = response.json()

            if not isinstance(scopes, list):
                raise RemoteServerError(
                    f"Invalid response format from {base_url}: expected list, got {type(scopes)}"
                )

            logger.info(f"Successfully listed {len(scopes)} scopes from {base_url}")
            return scopes

        except httpx.TimeoutException as e:
            raise RemoteServerError(
                f"Timeout listing scopes from {base_url}: {e}",
                url=base_url,
                status_code=None,
            )
        except httpx.ConnectError as e:
            raise RemoteServerError(
                f"Connection error listing scopes from {base_url}: {e}",
                url=base_url,
                status_code=None,
            )
        except httpx.HTTPError as e:
            status_code = getattr(e, "response", None)
            status_code = getattr(status_code, "status_code", None) if status_code else None
            raise RemoteServerError(
                f"HTTP error listing scopes from {base_url}: {e}",
                url=base_url,
                status_code=status_code,
            )
        except Exception as e:
            logger.exception(f"Unexpected error listing scopes from {base_url}")
            raise RemoteServerError(
                f"Unexpected error listing scopes from {base_url}: {type(e).__name__}: {e}",
                url=base_url,
                status_code=None,
            )

    def _parse_json(self, json_data: dict, scope_name: str, source_url: str) -> Scope:
        """Parse JSON response into a Scope.

        :param json_data: JSON data dictionary
        :type json_data: dict
        :param scope_name: Name of the scope
        :type scope_name: str
        :param source_url: Source URL for tracking
        :type source_url: str
        :returns: Parsed Scope instance
        :rtype: Scope
        :raises YAMLParseError: If parsing fails
        """
        try:
            from ...domain import RuleType, Scope
            from ..filesystem.yaml_parser import parse_metadata

            metadata_dict = json_data.get("metadata", {})
            metadata = parse_metadata(metadata_dict, scope_name)

            scope = Scope(metadata=metadata, source=source_url)

            commandments_flat = json_data.get("commandments", {})
            if commandments_flat:
                commandments_nested = self._flat_to_nested(commandments_flat)
                from ..filesystem.yaml_parser import parse_rules

                scope.commandments = parse_rules(commandments_nested, RuleType.COMMANDMENT)

            suggestions_flat = json_data.get("suggestions", {})
            if suggestions_flat:
                suggestions_nested = self._flat_to_nested(suggestions_flat)
                from ..filesystem.yaml_parser import parse_rules

                scope.suggestions = parse_rules(suggestions_nested, RuleType.SUGGESTION)

            return scope

        except Exception as e:
            raise YAMLParseError(f"Error parsing remote scope JSON data: {e}")

    def _flat_to_nested(self, flat_dict: dict) -> dict:
        """Convert flat dictionary with dot-notation keys to nested structure.

        Input: {"coding": {"when": "...", "rules": [...]},
                "coding.python": {"when": "...", "rules": [...]}}
        Output: {"coding": {"when": "...", "ruleset": [...],
                           "python": {"when": "...", "ruleset": [...]}}}

        :param flat_dict: Flat dictionary with dot-notation keys
        :type flat_dict: dict
        :returns: Nested dictionary structure
        :rtype: dict
        """
        result: dict[str, Any] = {}

        for key, value in flat_dict.items():
            parts = key.split(".")
            current = result

            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]

            last_part = parts[-1]
            category_data = {
                "when": value.get("when"),
                "tags": value.get("tags", []),
                "ruleset": value.get("rules", []),
            }
            current[last_part] = category_data

        return result

    def _parse_multidoc_yaml(self, yaml_content: str, scope_name: str, source_url: str) -> Scope:
        """Parse multi-document YAML response into a Scope.

        The response should contain 3 documents:
        1. Metadata
        2. Commandments
        3. Suggestions

        :param yaml_content: YAML content string
        :type yaml_content: str
        :param scope_name: Name of the scope
        :type scope_name: str
        :param source_url: Source URL for tracking
        :type source_url: str
        :returns: Parsed Scope instance
        :rtype: Scope
        :raises YAMLParseError: If parsing fails
        """
        try:
            import yaml  # type: ignore[import-untyped]

            documents = list(yaml.safe_load_all(yaml_content))

            if len(documents) != 3:
                raise YAMLParseError(f"Expected 3 YAML documents, got {len(documents)}")

            metadata_doc, commandments_doc, suggestions_doc = documents

            metadata_dict = metadata_doc.get("metadata", {})
            metadata = parse_metadata(metadata_dict, scope_name)

            from ...domain import RuleType, Scope

            scope = Scope(metadata=metadata, source=source_url)

            commandments_dict = commandments_doc.get("commandments", {})
            if commandments_dict:
                scope.commandments = parse_rules(commandments_dict, RuleType.COMMANDMENT)

            suggestions_dict = suggestions_doc.get("suggestions", {})
            if suggestions_dict:
                scope.suggestions = parse_rules(suggestions_dict, RuleType.SUGGESTION)

            return scope

        except yaml.YAMLError as e:
            raise YAMLParseError(f"Failed to parse YAML from remote server: {e}")
        except Exception as e:
            raise YAMLParseError(f"Error parsing remote scope data: {e}")

    def __del__(self) -> None:
        """Close the HTTP client on deletion.

        :rtype: None
        """
        if hasattr(self, "client"):
            self.client.close()


__all__ = ["HttpRemoteScopeClient"]
