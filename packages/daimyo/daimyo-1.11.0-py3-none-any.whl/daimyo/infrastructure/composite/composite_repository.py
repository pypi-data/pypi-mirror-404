"""Composite scope repository combining local and remote sources."""

from cachetools import TTLCache  # type: ignore[import-untyped]

from daimyo.domain import Scope, ScopeRepository
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)

SCOPE_LIST_CACHE_TTL = 1200
SCOPE_LIST_CACHE_KEY = "_scope_list_cache_"


class CompositeScopeRepository:
    """Repository that combines local and remote scope sources.

    Implements ScopeRepository protocol by:
    1. Delegating get_scope() to local repository (remote handled by sharding)
    2. Merging list_scopes() results from both local and remote with caching
    """

    def __init__(
        self,
        local_repo: ScopeRepository,
        remote_repo: ScopeRepository | None = None,
    ):
        """Initialize the composite repository.

        :param local_repo: Local filesystem repository
        :type local_repo: ScopeRepository
        :param remote_repo: Optional remote repository
        :type remote_repo: Optional[ScopeRepository]
        """
        self.local_repo = local_repo
        self.remote_repo = remote_repo
        self._cache: TTLCache = TTLCache(maxsize=1, ttl=SCOPE_LIST_CACHE_TTL)
        logger.info(
            f"Initialized CompositeScopeRepository "
            f"(remote={'enabled' if remote_repo else 'disabled'})"
        )

    def get_scope(self, name: str) -> Scope | None:
        """Load a scope from local or remote repository.

        Tries local first, then falls back to remote if not found locally.
        Note: The sharding mechanism in ScopeResolutionService will merge
        local and remote versions when both exist.

        :param name: Scope name
        :type name: str
        :returns: Scope instance if found, None otherwise
        :rtype: Optional[Scope]
        """
        local_scope = self.local_repo.get_scope(name)
        if local_scope is not None:
            logger.debug(f"Scope '{name}' found in local repository")
            return local_scope

        if self.remote_repo:
            logger.debug(f"Scope '{name}' not found locally, trying remote repository")
            remote_scope = self.remote_repo.get_scope(name)
            if remote_scope is not None:
                logger.info(f"Scope '{name}' found in remote repository")
                return remote_scope

        logger.debug(f"Scope '{name}' not found in any repository")
        return None

    def list_scopes(self) -> list[str]:
        """List all available scopes from local and remote sources (cached 20 min).

        :returns: Combined list of unique scope names
        :rtype: list[str]
        """
        cached_result = self._cache.get(SCOPE_LIST_CACHE_KEY)
        if cached_result is not None:
            logger.debug(f"Returning cached scope list ({len(cached_result)} scopes)")
            return list(cached_result)  # type: ignore[arg-type]

        local_scopes = self.local_repo.list_scopes()
        logger.debug(f"Found {len(local_scopes)} local scopes")

        remote_scopes: list[str] = []
        if self.remote_repo:
            remote_scopes = self.remote_repo.list_scopes()
            logger.debug(f"Found {len(remote_scopes)} remote scopes")

        combined = sorted(set(local_scopes) | set(remote_scopes))
        logger.info(
            f"Combined scope list: {len(local_scopes)} local, "
            f"{len(remote_scopes)} remote, {len(combined)} total unique"
        )

        self._cache[SCOPE_LIST_CACHE_KEY] = combined
        return combined


__all__ = ["CompositeScopeRepository"]
