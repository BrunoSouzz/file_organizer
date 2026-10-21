"""Modelos de dados para o File Organizer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


RuleType = Literal["extension", "pattern"]


@dataclass
class Rule:
    """Representa uma regra de organização."""
    name: str
    rule_type: RuleType  # 'extension' ou 'pattern' (glob/wildcard)
    patterns: list[str]  # Ex: ['.jpg', '.png'] ou ['*fatura*', 'recibo_*']
    custom_destination: str | None = None  # Destino específico opcional
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        return cls(
            name=data["name"],
            rule_type=data.get("rule_type", "extension"),
            patterns=list(data.get("patterns", [])),
            custom_destination=data.get("custom_destination"),
            enabled=data.get("enabled", True),
        )


@dataclass
class MovedFile:
    """Registro individual de um arquivo movido para histórico e reversão."""
    source: str
    destination: str
    timestamp: str
    rule_name: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> MovedFile:
        return cls(**data)


@dataclass
class BatchOperation:
    """Lote de arquivos movidos em uma única operação."""
    id: str
    timestamp: str
    source_dir: str
    destination_dir: str
    files: list[MovedFile] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "source_dir": self.source_dir,
            "destination_dir": self.destination_dir,
            "files": [f.to_dict() for f in self.files],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchOperation:
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            source_dir=data["source_dir"],
            destination_dir=data["destination_dir"],
            files=[MovedFile.from_dict(f) for f in data.get("files", [])],
        )


@dataclass
class OrganizationResult:
    """Resultado retornado ao final da organização de arquivos."""
    moved: list[tuple[Path, Path]] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return len(self.moved) + len(self.skipped) + len(self.errors)


@dataclass
class UndoResult:
    """Resultado da reversão (desfazer) de uma operação anterior."""
    restored: list[tuple[Path, Path]] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)
