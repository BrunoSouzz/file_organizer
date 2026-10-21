import tempfile
from pathlib import Path
from src.core.models import Rule
from src.core.rules import RuleManager, match_file_rule


def test_rule_matching_extension():
    rules = [
        Rule(name="Imagens", rule_type="extension", patterns=[".jpg", ".png"]),
        Rule(name="Documentos", rule_type="extension", patterns=[".pdf"]),
    ]
    
    img_path = Path("foto.JPG")
    pdf_path = Path("documento.pdf")
    other_path = Path("video.mp4")
    
    assert match_file_rule(img_path, rules).name == "Imagens"
    assert match_file_rule(pdf_path, rules).name == "Documentos"
    assert match_file_rule(other_path, rules) is None


def test_rule_matching_pattern():
    rules = [
        Rule(name="Notas Fiscais", rule_type="pattern", patterns=["*nf*", "*fatura*"]),
        Rule(name="Documentos", rule_type="extension", patterns=[".pdf"]),
    ]
    
    # Pattern deve ter prioridade sobre extensão geral
    nf_file = Path("nf_102030.pdf")
    fatura_file = Path("Fatura_Internet_Outubro.pdf")
    normal_pdf = Path("apostila.pdf")
    
    assert match_file_rule(nf_file, rules).name == "Notas Fiscais"
    assert match_file_rule(fatura_file, rules).name == "Notas Fiscais"
    assert match_file_rule(normal_pdf, rules).name == "Documentos"


def test_rule_manager_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_rules.json"
        manager = RuleManager(config_path)
        
        custom_rules = [
            Rule(name="Projetos", rule_type="pattern", patterns=["*projeto*"], enabled=True)
        ]
        manager.save_rules(custom_rules)
        
        loaded = manager.load_rules()
        assert len(loaded) == 1
        assert loaded[0].name == "Projetos"
        assert loaded[0].patterns == ["*projeto*"]
