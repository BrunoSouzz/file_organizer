"""Gerenciamento e correspondência de regras de organização."""

from __future__ import annotations

import fnmatch
import json
import os
from pathlib import Path
from typing import Iterable

from .models import Rule


def get_default_storage_dir() -> Path:
    """Retorna o diretório padrão para configurações e histórico."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        base = Path(appdata) / "FileOrganizer"
    else:
        base = Path.home() / ".file_organizer"
    base.mkdir(parents=True, exist_ok=True)
    return base


DEFAULT_RULES: list[Rule] = [
    Rule(
        name="Imagens",
        rule_type="extension",
        patterns=[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico"],
    ),
    Rule(
        name="Documentos",
        rule_type="extension",
        patterns=[".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
    ),
    Rule(
        name="Planilhas",
        rule_type="extension",
        patterns=[".xls", ".xlsx", ".csv", ".ods"],
    ),
    Rule(
        name="Apresentações",
        rule_type="extension",
        patterns=[".ppt", ".pptx", ".odp"],
    ),
    Rule(
        name="Áudios",
        rule_type="extension",
        patterns=[".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    ),
    Rule(
        name="Vídeos",
        rule_type="extension",
        patterns=[".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"],
    ),
    Rule(
        name="Compactados",
        rule_type="extension",
        patterns=[".zip", ".rar", ".tar", ".gz", ".7z", ".bz2"],
    ),
    Rule(
        name="Programas",
        rule_type="extension",
        patterns=[".exe", ".msi", ".bat", ".cmd", ".ps1", ".apk"],
    ),
    Rule(
        name="Código & Dev",
        rule_type="extension",
        patterns=[".py", ".js", ".ts", ".html", ".css", ".json", ".sql", ".java", ".cpp", ".c", ".php", ".sh"],
    ),
]


class RuleManager:
    """Carrega, persiste e manipula regras de organização."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or (get_default_storage_dir() / "rules.json")

    def get_default_rules(self) -> list[Rule]:
        return [Rule.from_dict(r.to_dict()) for r in DEFAULT_RULES]

    def load_rules(self) -> list[Rule]:
        if not self.config_path.exists():
            return self.get_default_rules()
        try:
            raw_data = json.loads(self.config_path.read_text(encoding="utf-8"))
            if isinstance(raw_data, list):
                return [Rule.from_dict(item) for item in raw_data if isinstance(item, dict)]
            # Compatibilidade com formato legado: dict[str, list[str]]
            if isinstance(raw_data, dict):
                rules: list[Rule] = []
                for cat, exts in raw_data.items():
                    if isinstance(exts, list):
                        rules.append(Rule(name=cat, rule_type="extension", patterns=exts))
                return rules
        except Exception:
            return self.get_default_rules()
        return self.get_default_rules()

    def save_rules(self, rules: list[Rule]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = [rule.to_dict() for rule in rules]
        self.config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_pattern(pattern: str, rule_type: str) -> str:
    """Normaliza o padrão ou extensão de acordo com o tipo."""
    pat = pattern.strip()
    if rule_type == "extension":
        pat = pat.lower()
        if not pat.startswith("."):
            pat = f".{pat}"
    return pat


def match_file_rule(file_path: Path, rules: Iterable[Rule]) -> Rule | None:
    """
    Encontra a primeira regra aplicável ao arquivo.
    Prioriza regras por 'pattern' (nome específico/wildcard) antes de 'extension'.
    """
    enabled_rules = [r for r in rules if r.enabled]
    filename_lower = file_path.name.lower()
    suffix_lower = file_path.suffix.lower()

    # 1. Checa padrões de nome primeiro (ex: '*fatura*', 'recibo_*')
    for rule in enabled_rules:
        if rule.rule_type == "pattern":
            for pat in rule.patterns:
                pat_lower = pat.lower()
                # Se não tem wildcard '*', adiciona busca parcial
                if "*" not in pat_lower and "?" not in pat_lower:
                    if pat_lower in filename_lower:
                        return rule
                elif fnmatch.fnmatch(filename_lower, pat_lower):
                    return rule

    # 2. Checa extensões
    for rule in enabled_rules:
        if rule.rule_type == "extension":
            for ext in rule.patterns:
                if suffix_lower == ext.lower():
                    return rule

    return None
