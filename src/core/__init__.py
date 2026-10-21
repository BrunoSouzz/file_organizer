"""Núcleo de processamento do File Organizer."""

from .engine import is_file_ready, organize, unique_destination
from .history import HistoryManager
from .models import BatchOperation, MovedFile, OrganizationResult, Rule, UndoResult
from .rules import DEFAULT_RULES, RuleManager, match_file_rule
from .watcher import FolderWatcher

__all__ = [
    "DEFAULT_RULES",
    "BatchOperation",
    "FolderWatcher",
    "HistoryManager",
    "MovedFile",
    "OrganizationResult",
    "Rule",
    "RuleManager",
    "UndoResult",
    "is_file_ready",
    "match_file_rule",
    "organize",
    "unique_destination",
]
