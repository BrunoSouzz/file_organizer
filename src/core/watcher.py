"""Modo Sentinela: Monitoramento contínuo em segundo plano para automação total."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from .engine import is_file_ready, organize
from .history import HistoryManager
from .models import Rule


class FolderWatcher:
    """Monitor de pastas em background com detecção segura de download concluído."""

    def __init__(
        self,
        source: Path,
        destination: Path,
        rules_provider: Callable[[], list[Rule]],
        history_manager: HistoryManager | None = None,
        poll_interval: float = 3.0,
        on_log: Callable[[str], None] | None = None,
        on_change: Callable[[int], None] | None = None,
    ) -> None:
        self.source = source
        self.destination = destination
        self.rules_provider = rules_provider
        self.history_manager = history_manager
        self.poll_interval = poll_interval
        self.on_log = on_log or (lambda _: None)
        self.on_change = on_change or (lambda _: None)

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Inicia a thread de monitoramento contínuo."""
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="SentinelThread")
        self._thread.start()
        self.on_log(f"🛡️ Sentinela ativado para: {self.source}")

    def stop(self) -> None:
        """Para a thread de monitoramento com segurança."""
        if not self.is_running:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self.on_log("🛑 Sentinela desativado.")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self.source.exists() and self.source.is_dir():
                    self._check_folder()
            except Exception as exc:
                self.on_log(f"Aviso no Sentinela: {exc}")

            # Espera fracionada para responder rapidamente ao comando de stop
            for _ in range(int(self.poll_interval * 10)):
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)

    def _check_folder(self) -> None:
        rules = self.rules_provider()
        # Encontra apenas arquivos prontos (ignora .tmp / .crdownload)
        ready_files = [f for f in self.source.iterdir() if f.is_file() and is_file_ready(f)]
        if not ready_files:
            return

        # Executa a organização de arquivos pendentes
        result = organize(
            source=self.source,
            destination=self.destination,
            rules=rules,
            recursive=False,
            dry_run=False,
            reporter=self.on_log,
            history_manager=self.history_manager,
        )

        if result.moved:
            self.on_change(len(result.moved))
