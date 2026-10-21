"""Sistema de histórico e reversão (desfazer) de operações."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Callable

from .models import BatchOperation, UndoResult
from .rules import get_default_storage_dir


class HistoryManager:
    """Registra movimentações e permite reverter operações anteriores."""

    def __init__(self, history_file: Path | None = None, max_entries: int = 50) -> None:
        self.history_file = history_file or (get_default_storage_dir() / "history.json")
        self.max_entries = max_entries

    def load_history(self) -> list[BatchOperation]:
        if not self.history_file.exists():
            return []
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [BatchOperation.from_dict(item) for item in data]
        except Exception:
            return []
        return []

    def record_batch(self, batch: BatchOperation) -> None:
        """Salva uma nova operação no topo do histórico."""
        history = self.load_history()
        history.insert(0, batch)
        history = history[: self.max_entries]
        self._save(history)

    def undo_latest(self, reporter: Callable[[str], None] | None = None) -> UndoResult:
        """Desfaz a última operação registrada."""
        history = self.load_history()
        if not history:
            return UndoResult([], [("", "Nenhum histórico disponível para desfazer.")])

        latest_batch = history.pop(0)
        result = self._revert_batch(latest_batch, reporter)
        self._save(history)
        return result

    def undo_by_id(self, batch_id: str, reporter: Callable[[str], None] | None = None) -> UndoResult:
        """Desfaz um lote específico pelo ID."""
        history = self.load_history()
        target_index = next((i for i, b in enumerate(history) if b.id == batch_id), None)
        if target_index is None:
            return UndoResult([], [("", f"Lote com ID {batch_id} não encontrado.")])

        batch = history.pop(target_index)
        result = self._revert_batch(batch, reporter)
        self._save(history)
        return result

    def clear_history(self) -> None:
        """Limpa o arquivo de histórico."""
        if self.history_file.exists():
            try:
                self.history_file.unlink()
            except OSError:
                pass

    def _revert_batch(self, batch: BatchOperation, reporter: Callable[[str], None] | None) -> UndoResult:
        report = reporter or (lambda _: None)
        result = UndoResult()

        # Reverte em ordem inversa para evitar conflitos
        for record in reversed(batch.files):
            src_path = Path(record.source)
            dest_path = Path(record.destination)

            if not dest_path.exists():
                err_msg = f"Arquivo não encontrado no destino para restauração: {dest_path.name}"
                result.errors.append((dest_path, err_msg))
                report(f"[Erro] {err_msg}")
                continue

            try:
                src_path.parent.mkdir(parents=True, exist_ok=True)
                # Se o destino original já existir, cria nome seguro
                final_src = self._safe_path(src_path)
                shutil.move(str(dest_path), str(final_src))
                result.restored.append((dest_path, final_src))
                report(f"[Restaurado] {dest_path.name} -> {final_src.parent}")

                # Limpa pasta de categoria se ficou vazia
                self._remove_dir_if_empty(dest_path.parent, stop_at=Path(batch.destination_dir))
            except OSError as exc:
                result.errors.append((dest_path, str(exc)))
                report(f"[Falha] Erro ao restaurar {dest_path.name}: {exc}")

        return result

    def _save(self, history: list[BatchOperation]) -> None:
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            data = [batch.to_dict() for batch in history]
            self.history_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    @staticmethod
    def _safe_path(path: Path) -> Path:
        if not path.exists():
            return path
        counter = 1
        while True:
            candidate = path.with_name(f"{path.stem} (restaurado {counter}){path.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    @staticmethod
    def _remove_dir_if_empty(folder: Path, stop_at: Path) -> None:
        try:
            if folder.resolve() != stop_at.resolve() and folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
        except OSError:
            pass
