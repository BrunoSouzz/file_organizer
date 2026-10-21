import tempfile
from pathlib import Path
from src.core.engine import organize, unique_destination
from src.core.models import Rule
from src.core.history import HistoryManager


def test_unique_destination():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file1 = base / "arquivo.txt"
        file1.write_text("teste 1")
        
        target = unique_destination(file1)
        assert target.name == "arquivo (1).txt"
        
        target.write_text("teste 2")
        target2 = unique_destination(file1)
        assert target2.name == "arquivo (2).txt"


def test_organize_basic_and_undo():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        source = base / "source"
        dest = base / "dest"
        source.mkdir()
        dest.mkdir()
        
        # Cria arquivos de teste
        (source / "foto.png").write_text("img")
        (source / "doc.pdf").write_text("pdf")
        (source / "ignorado.xyz").write_text("xyz")
        
        rules = [
            Rule(name="Imagens", rule_type="extension", patterns=[".png"]),
            Rule(name="Documentos", rule_type="extension", patterns=[".pdf"]),
        ]
        
        history_mgr = HistoryManager(base / "history.json")
        result = organize(source, dest, rules, history_manager=history_mgr)
        
        assert len(result.moved) == 2
        assert len(result.skipped) == 1
        assert (dest / "Imagens" / "foto.png").exists()
        assert (dest / "Documentos" / "doc.pdf").exists()
        assert not (source / "foto.png").exists()
        
        # Testa a reversão (Undo)
        undo_res = history_mgr.undo_latest()
        assert len(undo_res.restored) == 2
        assert (source / "foto.png").exists()
        assert (source / "doc.pdf").exists()
        assert not (dest / "Imagens" / "foto.png").exists()
