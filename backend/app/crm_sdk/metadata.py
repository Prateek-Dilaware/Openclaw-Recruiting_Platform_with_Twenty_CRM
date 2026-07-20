"""CRM SDK metadata layer (read-only, static registry skeleton).

Phase 1.2 scope: expose only workspace/version and empty-by-default object,
field, and relationship registries. **No schema synchronization** with the live
Twenty instance yet — that is a future phase.

The registries are intentionally minimal containers. They are NOT populated from
the network here and are NOT wired into TwentyService, so no behavior changes.
Future phases will hydrate these (e.g. from `/rest/metadata/objects`) and/or
from the Schema V2 declarative definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# SDK metadata version — bump when the metadata contract changes.
METADATA_VERSION = "0.1.0"


@dataclass
class ObjectEntry:
    """A single CRM object registry entry."""

    name_singular: str
    name_plural: str
    label: Optional[str] = None


@dataclass
class FieldEntry:
    """A single field registry entry, scoped to an object."""

    object_name: str
    name: str
    type: Optional[str] = None


@dataclass
class RelationshipEntry:
    """A single relationship registry entry (source -> target)."""

    source: str
    field: str
    target: str
    inverse_field: Optional[str] = None


@dataclass
class MetadataRegistry:
    """In-memory registries. Empty until a future phase hydrates them."""

    workspace: Optional[str] = None
    version: str = METADATA_VERSION
    objects: Dict[str, ObjectEntry] = field(default_factory=dict)
    fields: Dict[str, List[FieldEntry]] = field(default_factory=dict)
    relationships: List[RelationshipEntry] = field(default_factory=list)

    # -- read-only accessors ------------------------------------------------
    def get_object(self, name: str) -> Optional[ObjectEntry]:
        return self.objects.get(name)

    def list_objects(self) -> List[ObjectEntry]:
        return list(self.objects.values())

    def get_fields(self, object_name: str) -> List[FieldEntry]:
        return list(self.fields.get(object_name, []))

    def list_relationships(self) -> List[RelationshipEntry]:
        return list(self.relationships)


class MetadataProvider:
    """Facade exposing workspace/version and the registries.

    Discovery/synchronization is deliberately unimplemented in this phase.
    """

    def __init__(self, registry: Optional[MetadataRegistry] = None) -> None:
        self.registry = registry or MetadataRegistry()

    @property
    def version(self) -> str:
        return self.registry.version

    @property
    def workspace(self) -> Optional[str]:
        return self.registry.workspace

    def objects(self) -> List[ObjectEntry]:
        return self.registry.list_objects()

    def fields(self, object_name: str) -> List[FieldEntry]:
        return self.registry.get_fields(object_name)

    def relationships(self) -> List[RelationshipEntry]:
        return self.registry.list_relationships()
