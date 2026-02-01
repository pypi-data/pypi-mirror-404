"""Remote scope repository implementation."""

from daimyo.domain import RemoteScopeClient, Scope
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RemoteScopeRepository:
    """Repository for loading scopes from a remote server.

    Implements ScopeRepository protocol by delegating to RemoteScopeClient.
    """

    def __init__(self, remote_client: RemoteScopeClient, master_url: str):
        """Initialize the remote repository.

        :param remote_client: Client for making remote requests
        :type remote_client: RemoteScopeClient
        :param master_url: URL of the master server
        :type master_url: str
        """
        self.remote_client = remote_client
        self.master_url = master_url
        logger.info(f"Initialized RemoteScopeRepository with URL: {self.master_url}")

    def get_scope(self, name: str) -> Scope | None:
        """Load a scope from the remote server.

        :param name: Scope name
        :type name: str
        :returns: Scope instance if found, None otherwise
        :rtype: Optional[Scope]
        """
        if not self.master_url or self.master_url.strip() == "":
            logger.debug("No master URL configured, cannot fetch remote scope")
            return None

        try:
            return self.remote_client.fetch_scope(self.master_url, name)
        except Exception as e:
            logger.warning(f"Failed to fetch scope '{name}' from remote: {e}")
            return None

    def list_scopes(self) -> list[str]:
        """List all available scope names from the remote server.

        :returns: List of scope names, or empty list on error
        :rtype: list[str]
        """
        if not self.master_url or self.master_url.strip() == "":
            logger.debug("No master URL configured, cannot list remote scopes")
            return []

        try:
            scopes = self.remote_client.list_scopes(self.master_url)
            return scopes if scopes is not None else []
        except Exception as e:
            logger.warning(f"Failed to list scopes from remote: {e}")
            return []


__all__ = ["RemoteScopeRepository"]
