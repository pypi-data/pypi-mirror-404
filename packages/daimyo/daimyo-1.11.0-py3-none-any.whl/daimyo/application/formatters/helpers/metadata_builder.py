"""Metadata building utilities for formatters."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from daimyo.domain import MergedScope


class MetadataBuilderMixin:
    """Mixin providing metadata dictionary construction."""

    def _build_metadata_dict(self, scope: "MergedScope") -> dict[str, Any]:
        """Build standard metadata dictionary from scope.

        :param scope: The merged scope
        :type scope: MergedScope
        :returns: Metadata dictionary with name, description, parent, tags, sources
        :rtype: dict[str, Any]
        """
        return {
            "name": scope.metadata.name,
            "description": scope.metadata.description,
            "parent": scope.metadata.parent,
            "tags": scope.metadata.tags,
            "sources": scope.sources,
        }


__all__ = ["MetadataBuilderMixin"]
