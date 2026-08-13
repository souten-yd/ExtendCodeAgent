"""Host-neutral diagnostic output port and an offline test implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .contracts import Diagnostic


class DiagnosticSink(Protocol):
    def emit(self, diagnostic: Diagnostic) -> None: ...


@dataclass(slots=True)
class MemoryDiagnosticSink:
    _records: list[Diagnostic] = field(default_factory=list)

    def emit(self, diagnostic: Diagnostic) -> None:
        self._records.append(diagnostic)

    def records(self) -> tuple[Diagnostic, ...]:
        return tuple(self._records)
