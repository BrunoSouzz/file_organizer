"""Organizador de arquivos automatizado com interface gráfica moderna e linha de comando."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.core.engine import organize
from src.core.history import HistoryManager
from src.core.models import Rule
from src.core.rules import RuleManager, normalize_pattern
from src.core.watcher import FolderWatcher


def build_parser() -> argparse.ArgumentParser:
    """Configura e retorna o analisador de argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="File Organizer Pro: Organizador automático de arquivos por extensão, nome e sentinela."
    )
    parser.add_argument("--source", type=Path, help="Pasta de origem a ser organizada.")
    parser.add_argument("--destination", type=Path, help="Pasta de destino onde as categorias serão criadas.")
    parser.add_argument("--rules", type=Path, help="Caminho para arquivo JSON de regras personalizado.")
    parser.add_argument("--recursive", action="store_true", help="Inclui subpastas da origem.")
    parser.add_argument("--dry-run", action="store_true", help="Simula a operação sem mover nenhum arquivo.")
    parser.add_argument("--sentinel", action="store_true", help="Inicia o monitoramento contínuo em background via terminal.")
    parser.add_argument("--undo", action="store_true", help="Reverte a última operação de organização realizada.")
    parser.add_argument("--cli", action="store_true", help="Força a execução via terminal interativo.")
    return parser


def run_cli(args: argparse.Namespace) -> int:
    """Executa a aplicação em modo linha de comando."""
    rule_mgr = RuleManager(args.rules)
    history_mgr = HistoryManager()

    if args.undo:
        print("Revertendo última organização...")
        res = history_mgr.undo_latest(reporter=print)
        print(f"Restauração finalizada: {len(res.restored)} restaurado(s), {len(res.errors)} erro(s).")
        return 1 if res.errors else 0

    rules = rule_mgr.load_rules()

    source = args.source or Path(input("Pasta de origem: ").strip().strip('"'))
    destination = args.destination or Path(input("Pasta de destino: ").strip().strip('"'))

    if args.sentinel:
        print(f"🛡️ Iniciando Modo Sentinela em {source} -> {destination}")
        print("Pressione Ctrl+C para encerrar.")
        watcher = FolderWatcher(
            source=source,
            destination=destination,
            rules_provider=lambda: rules,
            history_manager=history_mgr,
            on_log=print,
            on_change=lambda count: print(f"✨ {count} arquivo(s) organizado(s) automaticamente!"),
        )
        watcher.start()
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.stop()
            print("\nSentinela finalizado.")
        return 0

    try:
        result = organize(
            source=source,
            destination=destination,
            rules=rules,
            recursive=args.recursive,
            dry_run=args.dry_run,
            reporter=print,
            history_manager=history_mgr,
        )
    except (ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(
        f"\nConcluído: {len(result.moved)} movido(s), "
        f"{len(result.skipped)} ignorado(s), {len(result.errors)} erro(s)."
    )
    return 1 if result.errors else 0


def launch_gui() -> None:
    """Inicia a interface gráfica moderna."""
    from src.ui.main_window import MainWindow
    app = MainWindow()
    app.run()


def main() -> int:
    """Ponto de entrada do programa."""
    args = build_parser().parse_args()

    # Se flags de terminal ou parâmetros de pasta foram informados, roda no CLI
    if args.cli or args.undo or args.sentinel:
        return run_cli(args)
    if args.source or args.destination:
        if not args.source or not args.destination:
            print("Aviso: --source e --destination devem ser informados juntos.", file=sys.stderr)
            return 2
        return run_cli(args)

    # Caso contrário, inicia a interface gráfica
    launch_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
