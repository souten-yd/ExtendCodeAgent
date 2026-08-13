from typing import TYPE_CHECKING

from .contracts import (
    BlueprintElement,
    BlueprintError,
    BlueprintRevision,
    BlueprintScope,
    BlueprintStatus,
    BlueprintView,
)
from .service import BlueprintRepository, BlueprintService, InMemoryBlueprintRepository

if TYPE_CHECKING:
    from .storage import SqliteBlueprintRepository


def __getattr__(name: str) -> object:
    if name == "SqliteBlueprintRepository":
        from .storage import SqliteBlueprintRepository

        return SqliteBlueprintRepository
    raise AttributeError(name)


__all__ = [
    "BlueprintElement",
    "BlueprintError",
    "BlueprintRepository",
    "BlueprintRevision",
    "BlueprintScope",
    "BlueprintService",
    "BlueprintStatus",
    "BlueprintView",
    "InMemoryBlueprintRepository",
    "SqliteBlueprintRepository",
]
