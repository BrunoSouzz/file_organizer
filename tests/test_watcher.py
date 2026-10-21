import tempfile
import time
from pathlib import Path
from src.core.models import Rule
from src.core.watcher import FolderWatcher


def test_watcher_lifecycle_and_organization():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        source = base / "watch_src"
        dest = base / "watch_dst"
        source.mkdir()
        dest.mkdir()

        rules = [
            Rule(name="Imagens", rule_type="extension", patterns=[".png"]),
        ]

        organized_batches = []
        logs = []

        watcher = FolderWatcher(
            source=source,
            destination=dest,
            rules_provider=lambda: rules,
            poll_interval=0.2,
            on_log=lambda m: logs.append(m),
            on_change=lambda count: organized_batches.append(count),
        )

        assert not watcher.is_running
        watcher.start()
        assert watcher.is_running

        # Cria um arquivo na pasta vigiada
        test_file = source / "foto_nova.png"
        test_file.write_text("conteudo da foto")

        # Aguarda a detecção pelo watcher (até ~1.5 segundos)
        for _ in range(15):
            if not test_file.exists():
                break
            time.sleep(0.1)

        watcher.stop()
        assert not watcher.is_running

        # Verifica se o arquivo foi movido para o destino
        assert not test_file.exists()
        assert (dest / "Imagens" / "foto_nova.png").exists()
        assert len(organized_batches) > 0
