"""Organizador de arquivos com interface gráfica e linha de comando."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


DEFAULT_RULES: dict[str, list[str]] = {
    "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
    "Documentos": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
    "Áudios": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
    "Vídeos": [".mp4", ".avi", ".mov", ".mkv", ".webm"],
    "Compactados": [".zip", ".rar", ".tar", ".gz", ".7z"],
    "Programas": [".exe", ".msi", ".bat", ".cmd", ".sh"],
}


@dataclass
class OrganizationResult:
    moved: list[tuple[Path, Path]]
    skipped: list[Path]
    errors: list[tuple[Path, str]]


def normalize_rules(rules: dict[str, Iterable[str]]) -> dict[str, list[str]]:
    """Normaliza extensões e rejeita regras vazias ou malformadas."""
    normalized: dict[str, list[str]] = {}
    for category, extensions in rules.items():
        category = category.strip()
        if not category:
            raise ValueError("O nome de uma categoria não pode ser vazio.")
        values = []
        for extension in extensions:
            extension = extension.strip().lower()
            if not extension:
                continue
            if not extension.startswith(".") or len(extension) == 1:
                raise ValueError(f"Extensão inválida: {extension!r}. Use, por exemplo, .pdf.")
            values.append(extension)
        if not values:
            raise ValueError(f"A categoria {category!r} não possui extensões.")
        normalized[category] = sorted(set(values))
    if not normalized:
        raise ValueError("Informe pelo menos uma categoria.")
    return normalized


def load_rules(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        return normalize_rules(DEFAULT_RULES)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Não foi possível ler as regras: {exc}") from exc
    if not isinstance(data, dict) or not all(isinstance(v, list) for v in data.values()):
        raise ValueError("O arquivo de regras deve ser um JSON no formato {\"Categoria\": [\".ext\"]}.")
    return normalize_rules(data)


def unique_destination(path: Path) -> Path:
    """Evita sobrescrever um arquivo já existente no destino."""
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def organize(
    source: Path,
    destination: Path,
    rules: dict[str, list[str]],
    *,
    recursive: bool = False,
    dry_run: bool = False,
    reporter: Callable[[str], None] | None = None,
) -> OrganizationResult:
    """Organiza arquivos por extensão e retorna um resumo da operação."""
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"A origem não é uma pasta válida: {source}")
    if source == destination or destination.is_relative_to(source):
        raise ValueError("O destino deve ser diferente e não pode ficar dentro da origem.")

    report = reporter or (lambda _message: None)
    extensions = {extension: category for category, values in rules.items() for extension in values}
    files = source.rglob("*") if recursive else source.iterdir()
    result = OrganizationResult([], [], [])

    for item in files:
        if not item.is_file() or item.suffix.lower() not in extensions:
            if item.is_file():
                result.skipped.append(item)
            continue
        category = extensions[item.suffix.lower()]
        target = unique_destination(destination / category / item.name)
        try:
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(target))
            result.moved.append((item, target))
            report(f"{'[simulação] ' if dry_run else ''}{item.name} -> {target}")
        except OSError as exc:
            result.errors.append((item, str(exc)))
            report(f"Erro ao mover {item.name}: {exc}")
    return result


def parse_rule_lines(text: str) -> dict[str, list[str]]:
    """Lê linhas no formato Categoria=.ext,.outraext usado pela GUI."""
    rules: dict[str, list[str]] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"Linha {line_number}: use o formato Categoria=.ext,.ext.")
        category, extensions = line.split("=", 1)
        rules[category] = [value.strip() for value in extensions.split(",")]
    return normalize_rules(rules)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Organiza arquivos por extensão.")
    parser.add_argument("--source", type=Path, help="Pasta de origem.")
    parser.add_argument("--destination", type=Path, help="Pasta onde as categorias serão criadas.")
    parser.add_argument("--rules", type=Path, help="JSON de regras personalizado.")
    parser.add_argument("--recursive", action="store_true", help="Inclui subpastas da origem.")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria movido sem alterar arquivos.")
    parser.add_argument("--cli", action="store_true", help="Usa o modo interativo no terminal.")
    return parser


def run_cli(args: argparse.Namespace) -> int:
    source = args.source or Path(input("Pasta de origem: ").strip().strip('"'))
    destination = args.destination or Path(input("Pasta de destino: ").strip().strip('"'))
    try:
        rules = load_rules(args.rules)
        result = organize(source, destination, rules, recursive=args.recursive, dry_run=args.dry_run, reporter=print)
    except (ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"\nConcluído: {len(result.moved)} movido(s), {len(result.skipped)} ignorado(s), {len(result.errors)} erro(s).")
    return 1 if result.errors else 0


def launch_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext

    try:
        import ttkbootstrap as ttk

        root = ttk.Window(themename="flatly")
        bootstrap = True
    except ImportError:
        from tkinter import ttk

        root = tk.Tk()
        bootstrap = False

    root.title("File Organizer")
    root.geometry("700x330")
    root.minsize(620, 300)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    source_var, destination_var = tk.StringVar(), tk.StringVar()
    recursive_var, dry_run_var = tk.BooleanVar(), tk.BooleanVar()
    outline_button = {"bootstyle": "outline"} if bootstrap else {}
    link_button = {"bootstyle": "link"} if bootstrap else {}
    success_button = {"bootstyle": "success"} if bootstrap else {}
    container = ttk.Frame(root, padding=20)
    container.grid(row=0, column=0, sticky="nsew")
    container.columnconfigure(1, weight=1)

    ttk.Label(container, text="File Organizer", font=("Segoe UI", 18, "bold")).grid(
        row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 2)
    )
    ttk.Label(container, text="Organize seus arquivos em poucos cliques.").grid(
        row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 18)
    )

    def choose_folder(variable: tk.StringVar) -> None:
        selected = filedialog.askdirectory()
        if selected:
            variable.set(selected)

    ttk.Label(container, text="De:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=6)
    ttk.Entry(container, textvariable=source_var).grid(row=2, column=1, sticky="ew", pady=6)
    ttk.Button(container, text="Selecionar", command=lambda: choose_folder(source_var),
               **outline_button).grid(row=2, column=2, padx=(10, 0), pady=6)
    ttk.Label(container, text="Para:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=6)
    ttk.Entry(container, textvariable=destination_var).grid(row=3, column=1, sticky="ew", pady=6)
    ttk.Button(container, text="Selecionar", command=lambda: choose_folder(destination_var),
               **outline_button).grid(row=3, column=2, padx=(10, 0), pady=6)

    advanced = ttk.Frame(container)
    advanced.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 0))
    advanced.columnconfigure(0, weight=1)
    rules_box = scrolledtext.ScrolledText(advanced, width=70, height=7)
    rules_box.insert(tk.END, "\n".join(f"{category}={','.join(values)}" for category, values in DEFAULT_RULES.items()))
    ttk.Checkbutton(advanced, text="Incluir subpastas", variable=recursive_var).pack(side=tk.LEFT, padx=(0, 20))
    ttk.Checkbutton(advanced, text="Simular", variable=dry_run_var).pack(side=tk.LEFT)

    def toggle_advanced() -> None:
        if advanced.winfo_ismapped():
            advanced.grid_remove()
            options_button.configure(text="Opções")
        else:
            advanced.grid()
            options_button.configure(text="Ocultar opções")

    options_button = ttk.Button(container, text="Opções", command=toggle_advanced, **link_button)
    options_button.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(4, 0))
    advanced.grid_remove()

    def start() -> None:
        try:
            rules = parse_rule_lines(rules_box.get("1.0", "end"))
            organize(Path(source_var.get()), Path(destination_var.get()), rules,
                     recursive=recursive_var.get(), dry_run=dry_run_var.get())
            messagebox.showinfo("Tudo certo", "Arquivos organizados com sucesso.")
        except (ValueError, OSError) as exc:
            messagebox.showerror("Não foi possível organizar", str(exc))

    action = ttk.Button(container, text="Organizar arquivos", command=start, **success_button)
    action.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(22, 0), ipady=5)
    root.mainloop()


def main() -> int:
    args = build_parser().parse_args()
    if args.cli:
        return run_cli(args)
    if args.source or args.destination:
        if not args.source or not args.destination:
            print("--source e --destination devem ser informados juntos.", file=sys.stderr)
            return 2
        return run_cli(args)
    launch_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
