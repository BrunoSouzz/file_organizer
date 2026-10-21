"""Interface gráfica moderna, responsiva e fluida para o File Organizer."""

from __future__ import annotations

import os
import queue
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    HAS_TTKBOOTSTRAP = True
except ImportError:
    HAS_TTKBOOTSTRAP = False

from ..core.engine import organize
from ..core.history import HistoryManager
from ..core.models import Rule
from ..core.rules import RuleManager, get_default_storage_dir
from ..core.watcher import FolderWatcher


def get_asset_path(filename: str) -> Path:
    """Localiza arquivos de recursos (ícones/assets) de forma compatível com PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS) / "assets"
    else:
        base = Path(__file__).resolve().parent.parent.parent / "assets"
    return base / filename


class MainWindow:
    """Janela principal da aplicação com abas funcionais e operações assíncronas."""

    def __init__(self) -> None:
        self.theme_name = "cosmo"
        if HAS_TTKBOOTSTRAP:
            self.root = tb.Window(
                title="File Organizer Pro",
                themename=self.theme_name,
                size=(820, 640),
                minsize=(740, 520),
            )
        else:
            self.root = tk.Tk()
            self.root.title("File Organizer Pro")
            self.root.geometry("820x640")

        # Configura ícone da janela
        icon_path = get_asset_path("icon.ico")
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.rule_manager = RuleManager()
        self.history_manager = HistoryManager()
        self.rules: list[Rule] = self.rule_manager.load_rules()
        self.watcher: FolderWatcher | None = None
        self.msg_queue: queue.Queue[tuple[str, any]] = queue.Queue()

        self._init_variables()
        self._build_ui()
        self._check_queue()

    def _init_variables(self) -> None:
        self.source_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.destination_var = tk.StringVar(value=str(Path.home() / "Documents" / "Organizados"))
        self.recursive_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Pronto para organizar.")
        self.is_processing = False

        # Sentinela
        self.sentinel_source_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.sentinel_dest_var = tk.StringVar(value=str(Path.home() / "Documents" / "Organizados"))
        self.sentinel_status_var = tk.StringVar(value="Sentinela Desativado")

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Header principal com alternador de tema
        header = ttk.Frame(self.root, padding=(16, 12, 16, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        title_lbl = ttk.Label(header, text="📁 File Organizer", font=("Segoe UI", 16, "bold"))
        title_lbl.grid(row=0, column=0, sticky="w")
        subtitle_lbl = ttk.Label(
            header,
            text="Automação inteligente para organizar seus arquivos com rapidez e segurança.",
            font=("Segoe UI", 9),
        )
        subtitle_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))

        if HAS_TTKBOOTSTRAP:
            theme_btn = tb.Button(
                header,
                text="🌓 Alternar Tema",
                bootstyle="secondary-outline",
                command=self._toggle_theme,
            )
            theme_btn.grid(row=0, column=2, rowspan=2, sticky="e")

        # Notebook (Abas)
        notebook_frame = ttk.Frame(self.root, padding=(16, 6, 16, 16))
        notebook_frame.grid(row=1, column=0, sticky="nsew")
        self.root.rowconfigure(1, weight=1)
        notebook_frame.columnconfigure(0, weight=1)
        notebook_frame.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Aba 1: Organizar
        self.tab_organize = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(self.tab_organize, text="⚡ Organizar")
        self._build_tab_organize()

        # Aba 2: Regras
        self.tab_rules = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(self.tab_rules, text="🎯 Regras e Pastas")
        self._build_tab_rules()

        # Aba 3: Sentinela
        self.tab_sentinel = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(self.tab_sentinel, text="🛡️ Modo Sentinela")
        self._build_tab_sentinel()

        # Aba 4: Histórico
        self.tab_history = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(self.tab_history, text="⏪ Histórico & Desfazer")
        self._build_tab_history()

    # -------------------------------------------------------------
    # ABA 1: ORGANIZAR
    # -------------------------------------------------------------
    def _build_tab_organize(self) -> None:
        self.tab_organize.columnconfigure(1, weight=1)
        self.tab_organize.rowconfigure(6, weight=1)

        # Origem
        ttk.Label(self.tab_organize, text="Origem (De):", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=6
        )
        src_entry = ttk.Entry(self.tab_organize, textvariable=self.source_var)
        src_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        src_btn = ttk.Button(
            self.tab_organize,
            text="Buscar...",
            command=lambda: self._choose_directory(self.source_var),
        )
        src_btn.grid(row=0, column=2, padx=(0, 4), pady=6)

        # Destino
        ttk.Label(self.tab_organize, text="Destino (Para):", font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky="w", pady=6
        )
        dst_entry = ttk.Entry(self.tab_organize, textvariable=self.destination_var)
        dst_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        dst_btn = ttk.Button(
            self.tab_organize,
            text="Buscar...",
            command=lambda: self._choose_directory(self.destination_var),
        )
        dst_btn.grid(row=1, column=2, padx=(0, 4), pady=6)

        # Atalhos rápidos de pastas
        quick_frame = ttk.Frame(self.tab_organize)
        quick_frame.grid(row=2, column=1, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(quick_frame, text="Atalhos rápidos:", font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            quick_frame,
            text="Downloads",
            style="secondary.TButton" if not HAS_TTKBOOTSTRAP else "secondary-link",
            command=lambda: self.source_var.set(str(Path.home() / "Downloads")),
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            quick_frame,
            text="Área de Trabalho",
            style="secondary.TButton" if not HAS_TTKBOOTSTRAP else "secondary-link",
            command=lambda: self.source_var.set(str(Path.home() / "Desktop")),
        ).pack(side=tk.LEFT, padx=4)

        # Opções
        opts_frame = ttk.Frame(self.tab_organize)
        opts_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 12))
        ttk.Checkbutton(opts_frame, text="Incluir subpastas (Recursivo)", variable=self.recursive_var).pack(
            side=tk.LEFT, padx=(0, 20)
        )
        ttk.Checkbutton(
            opts_frame,
            text="Simulação prévia (não move nenhum arquivo)",
            variable=self.dry_run_var,
        ).pack(side=tk.LEFT)

        # Botão Principal de Ação
        btn_frame = ttk.Frame(self.tab_organize)
        btn_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        btn_frame.columnconfigure(0, weight=3)
        btn_frame.columnconfigure(1, weight=1)

        if HAS_TTKBOOTSTRAP:
            self.run_btn = tb.Button(
                btn_frame,
                text="🚀 Organizar Arquivos Agora",
                bootstyle="success",
                command=self._start_organization,
            )
            self.undo_btn = tb.Button(
                btn_frame,
                text="⏪ Desfazer Última",
                bootstyle="warning-outline",
                command=self._undo_last_operation,
            )
        else:
            self.run_btn = ttk.Button(btn_frame, text="🚀 Organizar Arquivos Agora", command=self._start_organization)
            self.undo_btn = ttk.Button(btn_frame, text="⏪ Desfazer Última", command=self._undo_last_operation)

        self.run_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=6)
        self.undo_btn.grid(row=0, column=1, sticky="ew", ipady=6)

        # Barra de Progresso e Status
        prog_frame = ttk.Frame(self.tab_organize)
        prog_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(4, 8))
        prog_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky="ew")

        status_lbl = ttk.Label(prog_frame, textvariable=self.status_var, font=("Segoe UI", 9))
        status_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Log ScrolledText
        log_frame = ttk.LabelFrame(self.tab_organize, text="Registro de Atividades (Log)", padding=8)
        log_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(6, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word", height=8, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        clear_btn = ttk.Button(log_frame, text="Limpar Log", command=self._clear_log)
        clear_btn.grid(row=1, column=0, columnspan=2, sticky="e", pady=(6, 0))

    # -------------------------------------------------------------
    # ABA 2: REGRAS E PASTAS
    # -------------------------------------------------------------
    def _build_tab_rules(self) -> None:
        self.tab_rules.columnconfigure(0, weight=1)
        self.tab_rules.rowconfigure(1, weight=1)

        header_frame = ttk.Frame(self.tab_rules)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(
            header_frame,
            text="Personalize suas categorias, filtros por extensão ou nome específico e destinos.",
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        # Treeview de Regras
        columns = ("name", "type", "patterns", "destination")
        self.rules_tree = ttk.Treeview(self.tab_rules, columns=columns, show="headings", height=10)
        self.rules_tree.heading("name", text="Categoria / Regra")
        self.rules_tree.heading("type", text="Tipo")
        self.rules_tree.heading("patterns", text="Extensões ou Padrão")
        self.rules_tree.heading("destination", text="Destino Customizado")

        self.rules_tree.column("name", width=140)
        self.rules_tree.column("type", width=90)
        self.rules_tree.column("patterns", width=280)
        self.rules_tree.column("destination", width=220)

        self.rules_tree.grid(row=1, column=0, sticky="nsew")
        rules_scroll = ttk.Scrollbar(self.tab_rules, orient="vertical", command=self.rules_tree.yview)
        rules_scroll.grid(row=1, column=1, sticky="ns")
        self.rules_tree.configure(yscrollcommand=rules_scroll.set)

        # Botões de Ação de Regras
        actions = ttk.Frame(self.tab_rules)
        actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Button(actions, text="➕ Nova Regra", command=self._add_rule_dialog).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(actions, text="✏️ Editar Regra", command=self._edit_selected_rule).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(actions, text="🗑️ Excluir Regra", command=self._delete_selected_rule).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(actions, text="🔄 Restaurar Padrões", command=self._reset_default_rules).pack(side=tk.RIGHT)

        self._refresh_rules_tree()

    # -------------------------------------------------------------
    # ABA 3: SENTINELA (MONITORAMENTO EM BACKGROUND)
    # -------------------------------------------------------------
    def _build_tab_sentinel(self) -> None:
        self.tab_sentinel.columnconfigure(1, weight=1)
        self.tab_sentinel.rowconfigure(5, weight=1)

        ttk.Label(
            self.tab_sentinel,
            text="Automação Contínua (Sentinela)",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        ttk.Label(
            self.tab_sentinel,
            text="O Sentinela vigia pastas automaticamente. Assim que um download termina, ele é organizado.",
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 16))

        # Origem do Sentinela
        ttk.Label(self.tab_sentinel, text="Vigiar Pasta:", font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky="w", pady=6
        )
        ttk.Entry(self.tab_sentinel, textvariable=self.sentinel_source_var).grid(
            row=2, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Button(
            self.tab_sentinel,
            text="Buscar...",
            command=lambda: self._choose_directory(self.sentinel_source_var),
        ).grid(row=2, column=2, pady=6)

        # Destino do Sentinela
        ttk.Label(self.tab_sentinel, text="Organizar Em:", font=("Segoe UI", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=6
        )
        ttk.Entry(self.tab_sentinel, textvariable=self.sentinel_dest_var).grid(
            row=3, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Button(
            self.tab_sentinel,
            text="Buscar...",
            command=lambda: self._choose_directory(self.sentinel_dest_var),
        ).grid(row=3, column=2, pady=6)

        # Painel de Controle e Status
        control_frame = ttk.Frame(self.tab_sentinel, padding=(0, 12, 0, 12))
        control_frame.grid(row=4, column=0, columnspan=3, sticky="ew")
        control_frame.columnconfigure(1, weight=1)

        if HAS_TTKBOOTSTRAP:
            self.sentinel_btn = tb.Button(
                control_frame,
                text="▶ Ativar Sentinela",
                bootstyle="info",
                command=self._toggle_sentinel,
            )
        else:
            self.sentinel_btn = ttk.Button(control_frame, text="▶ Ativar Sentinela", command=self._toggle_sentinel)

        self.sentinel_btn.grid(row=0, column=0, padx=(0, 16), ipady=5)

        self.sentinel_status_lbl = ttk.Label(
            control_frame,
            textvariable=self.sentinel_status_var,
            font=("Segoe UI", 10, "bold"),
        )
        self.sentinel_status_lbl.grid(row=0, column=1, sticky="w")

        # Log do Sentinela
        sentinel_log_frame = ttk.LabelFrame(self.tab_sentinel, text="Atividades do Sentinela", padding=8)
        sentinel_log_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        sentinel_log_frame.columnconfigure(0, weight=1)
        sentinel_log_frame.rowconfigure(0, weight=1)

        self.sentinel_log_text = tk.Text(sentinel_log_frame, wrap="word", height=8, font=("Consolas", 9))
        self.sentinel_log_text.grid(row=0, column=0, sticky="nsew")
        sent_scroll = ttk.Scrollbar(sentinel_log_frame, orient="vertical", command=self.sentinel_log_text.yview)
        sent_scroll.grid(row=0, column=1, sticky="ns")
        self.sentinel_log_text.configure(yscrollcommand=sent_scroll.set)

    # -------------------------------------------------------------
    # ABA 4: HISTÓRICO & DESFAZER
    # -------------------------------------------------------------
    def _build_tab_history(self) -> None:
        self.tab_history.columnconfigure(0, weight=1)
        self.tab_history.rowconfigure(1, weight=1)

        ttk.Label(
            self.tab_history,
            text="Lotes de Organizações Recentes (Reversão Rápida)",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        columns = ("id", "timestamp", "count", "source", "dest")
        self.history_tree = ttk.Treeview(self.tab_history, columns=columns, show="headings", height=10)
        self.history_tree.heading("id", text="ID Lote")
        self.history_tree.heading("timestamp", text="Data / Hora")
        self.history_tree.heading("count", text="Qtd. Arquivos")
        self.history_tree.heading("source", text="Pasta Origem")
        self.history_tree.heading("dest", text="Pasta Destino")

        self.history_tree.column("id", width=80)
        self.history_tree.column("timestamp", width=140)
        self.history_tree.column("count", width=90)
        self.history_tree.column("source", width=200)
        self.history_tree.column("dest", width=200)

        self.history_tree.grid(row=1, column=0, sticky="nsew")
        hist_scroll = ttk.Scrollbar(self.tab_history, orient="vertical", command=self.history_tree.yview)
        hist_scroll.grid(row=1, column=1, sticky="ns")
        self.history_tree.configure(yscrollcommand=hist_scroll.set)

        hist_actions = ttk.Frame(self.tab_history)
        hist_actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Button(hist_actions, text="⏪ Desfazer Lote Selecionado", command=self._undo_selected_history_batch).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(hist_actions, text="🧹 Limpar Histórico", command=self._clear_history_data).pack(side=tk.RIGHT)

        self._refresh_history_tree()

    # -------------------------------------------------------------
    # CONTROLADORES E LOGICA DE EVENTOS
    # -------------------------------------------------------------
    def _toggle_theme(self) -> None:
        if not HAS_TTKBOOTSTRAP:
            return
        current = self.root.style.theme.name
        new_theme = "darkly" if current == "cosmo" else "cosmo"
        self.root.style.theme_use(new_theme)

    def _choose_directory(self, target_var: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=target_var.get() or Path.home())
        if selected:
            target_var.set(selected)

    def _log(self, text: str) -> None:
        self.msg_queue.put(("log", text))

    def _clear_log(self) -> None:
        self.log_text.delete("1.0", tk.END)

    def _check_queue(self) -> None:
        """Processa mensagens da fila em segundo plano sem travar a interface."""
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == "log":
                    self.log_text.insert(tk.END, f"{data}\n")
                    self.log_text.see(tk.END)
                elif msg_type == "sentinel_log":
                    self.sentinel_log_text.insert(tk.END, f"{data}\n")
                    self.sentinel_log_text.see(tk.END)
                elif msg_type == "progress":
                    current, total, filename = data
                    percent = int((current / total) * 100) if total > 0 else 0
                    self.progress_bar["value"] = percent
                    self.status_var.set(f"Organizando {current}/{total} ({percent}%): {filename}")
                elif msg_type == "done":
                    result = data
                    self.is_processing = False
                    self.run_btn.configure(state=tk.NORMAL)
                    self.status_var.set(
                        f"Finalizado: {len(result.moved)} movido(s), {len(result.skipped)} ignorado(s), {len(result.errors)} erro(s)."
                    )
                    self._refresh_history_tree()
                    messagebox.showinfo(
                        "Organização Concluída",
                        f"Operação finalizada!\n\n"
                        f"• Movidos: {len(result.moved)}\n"
                        f"• Ignorados: {len(result.skipped)}\n"
                        f"• Erros: {len(result.errors)}",
                    )
                elif msg_type == "error":
                    self.is_processing = False
                    self.run_btn.configure(state=tk.NORMAL)
                    self.status_var.set(f"Erro: {data}")
                    messagebox.showerror("Erro na Organização", str(data))
                elif msg_type == "undo_done":
                    result = data
                    self.is_processing = False
                    self.run_btn.configure(state=tk.NORMAL)
                    self.status_var.set(f"Restauração finalizada: {len(result.restored)} arquivo(s) restaurado(s).")
                    self._refresh_history_tree()
                    messagebox.showinfo(
                        "Desfazer Concluído",
                        f"Restauração realizada com sucesso!\n\n"
                        f"• Arquivos restaurados: {len(result.restored)}\n"
                        f"• Erros: {len(result.errors)}",
                    )
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._check_queue)

    def _start_organization(self) -> None:
        if self.is_processing:
            return
        source = Path(self.source_var.get())
        dest = Path(self.destination_var.get())

        if not source.exists():
            messagebox.showerror("Origem Inválida", "A pasta de origem especificada não existe.")
            return

        self.is_processing = True
        self.run_btn.configure(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.status_var.set("Iniciando organização...")
        self._log(f"--- Iniciando operação em {source} ---")

        def worker() -> None:
            try:
                result = organize(
                    source=source,
                    destination=dest,
                    rules=self.rules,
                    recursive=self.recursive_var.get(),
                    dry_run=self.dry_run_var.get(),
                    progress_callback=lambda c, t, f: self.msg_queue.put(("progress", (c, t, f))),
                    reporter=self._log,
                    history_manager=self.history_manager,
                )
                self.msg_queue.put(("done", result))
            except Exception as exc:
                self.msg_queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _undo_last_operation(self) -> None:
        if self.is_processing:
            return
        self.is_processing = True
        self.run_btn.configure(state=tk.DISABLED)
        self.status_var.set("Revertendo última organização...")

        def worker() -> None:
            try:
                result = self.history_manager.undo_latest(reporter=self._log)
                self.msg_queue.put(("undo_done", result))
            except Exception as exc:
                self.msg_queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    # -------------------------------------------------------------
    # MODO SENTINELA CONTROLLER
    # -------------------------------------------------------------
    def _toggle_sentinel(self) -> None:
        if self.watcher and self.watcher.is_running:
            self.watcher.stop()
            self.watcher = None
            self.sentinel_status_var.set("⚪ Sentinela Desativado")
            self.sentinel_btn.configure(text="▶ Ativar Sentinela")
            if HAS_TTKBOOTSTRAP:
                self.sentinel_btn.configure(bootstyle="info")
        else:
            source = Path(self.sentinel_source_var.get())
            dest = Path(self.sentinel_dest_var.get())
            if not source.exists():
                messagebox.showerror("Erro Sentinela", "A pasta vigiada não existe.")
                return

            self.watcher = FolderWatcher(
                source=source,
                destination=dest,
                rules_provider=lambda: self.rules,
                history_manager=self.history_manager,
                on_log=lambda msg: self.msg_queue.put(("sentinel_log", msg)),
                on_change=lambda count: self.msg_queue.put(
                    ("sentinel_log", f"✨ {count} novo(s) arquivo(s) organizado(s) automaticamente!")
                ),
            )
            self.watcher.start()
            self.sentinel_status_var.set("🟢 Sentinela Ativo e Vigiando")
            self.sentinel_btn.configure(text="⏹ Parar Sentinela")
            if HAS_TTKBOOTSTRAP:
                self.sentinel_btn.configure(bootstyle="danger")

    # -------------------------------------------------------------
    # REGRAS CONTROLLER
    # -------------------------------------------------------------
    def _refresh_rules_tree(self) -> None:
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        for r in self.rules:
            tipo_label = "Extensão" if r.rule_type == "extension" else "Nome / Padrão"
            pats = ", ".join(r.patterns)
            dest = r.custom_destination or "[Pasta Padrão do Destino]"
            self.rules_tree.insert("", tk.END, values=(r.name, tipo_label, pats, dest))

    def _add_rule_dialog(self) -> None:
        self._open_rule_editor(None)

    def _edit_selected_rule(self) -> None:
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Seleção", "Selecione uma regra para editar.")
            return
        item_idx = self.rules_tree.index(selected[0])
        self._open_rule_editor(item_idx)

    def _delete_selected_rule(self) -> None:
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Seleção", "Selecione uma regra para excluir.")
            return
        item_idx = self.rules_tree.index(selected[0])
        del self.rules[item_idx]
        self.rule_manager.save_rules(self.rules)
        self._refresh_rules_tree()

    def _reset_default_rules(self) -> None:
        if messagebox.askyesno("Restaurar", "Deseja restaurar as regras padrões originais?"):
            self.rules = self.rule_manager.get_default_rules()
            self.rule_manager.save_rules(self.rules)
            self._refresh_rules_tree()

    def _open_rule_editor(self, index: int | None) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Adicionar Regra" if index is None else "Editar Regra")
        dialog.geometry("520x360")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        rule = self.rules[index] if index is not None else None

        name_var = tk.StringVar(value=rule.name if rule else "")
        type_var = tk.StringVar(value=rule.rule_type if rule else "extension")
        pats_var = tk.StringVar(value=", ".join(rule.patterns) if rule else "")
        dest_var = tk.StringVar(value=rule.custom_destination or "" if rule else "")

        pad = {"padx": 16, "pady": 6}
        container = ttk.Frame(dialog, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Nome da Categoria / Regra:").pack(anchor=tk.W)
        ttk.Entry(container, textvariable=name_var).pack(fill=tk.X, pady=(2, 10))

        ttk.Label(container, text="Tipo de Correspondência:").pack(anchor=tk.W)
        type_frame = ttk.Frame(container)
        type_frame.pack(fill=tk.X, pady=(2, 10))
        ttk.Radiobutton(type_frame, text="Extensão (.pdf, .png)", value="extension", variable=type_var).pack(
            side=tk.LEFT, padx=(0, 20)
        )
        ttk.Radiobutton(type_frame, text="Nome ou Padrão (*fatura*, nota_*)", value="pattern", variable=type_var).pack(
            side=tk.LEFT
        )

        ttk.Label(container, text="Extensões ou Padrões (separados por vírgula):").pack(anchor=tk.W)
        ttk.Entry(container, textvariable=pats_var).pack(fill=tk.X, pady=(2, 10))

        ttk.Label(container, text="Pasta Destino Específica (Opcional):").pack(anchor=tk.W)
        dst_row = ttk.Frame(container)
        dst_row.pack(fill=tk.X, pady=(2, 16))
        ttk.Entry(dst_row, textvariable=dest_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(dst_row, text="Buscar...", command=lambda: self._choose_directory(dest_var)).pack(side=tk.RIGHT)

        def save() -> None:
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Erro", "O nome da regra é obrigatório.", parent=dialog)
                return
            pats = [p.strip() for p in pats_var.get().split(",") if p.strip()]
            if not pats:
                messagebox.showerror("Erro", "Informe ao menos um padrão ou extensão.", parent=dialog)
                return

            cust_dest = dest_var.get().strip() or None
            new_rule = Rule(
                name=name,
                rule_type=type_var.get(),
                patterns=pats,
                custom_destination=cust_dest,
            )

            if index is None:
                self.rules.append(new_rule)
            else:
                self.rules[index] = new_rule

            self.rule_manager.save_rules(self.rules)
            self._refresh_rules_tree()
            dialog.destroy()

        btn_box = ttk.Frame(container)
        btn_box.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_box, text="Salvar Regra", command=save).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btn_box, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT)

    # -------------------------------------------------------------
    # HISTORICO CONTROLLER
    # -------------------------------------------------------------
    def _refresh_history_tree(self) -> None:
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        history = self.history_manager.load_history()
        for batch in history:
            self.history_tree.insert(
                "",
                tk.END,
                values=(
                    batch.id,
                    batch.timestamp,
                    f"{len(batch.files)} arquivo(s)",
                    batch.source_dir,
                    batch.destination_dir,
                ),
            )

    def _undo_selected_history_batch(self) -> None:
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("Histórico", "Selecione um lote no histórico para reverter.")
            return
        item_values = self.history_tree.item(selected[0], "values")
        batch_id = item_values[0]

        if not messagebox.askyesno("Confirmar Reversão", f"Deseja realmente desfazer o lote {batch_id}?"):
            return

        def worker() -> None:
            try:
                res = self.history_manager.undo_by_id(batch_id, reporter=self._log)
                self.msg_queue.put(("undo_done", res))
            except Exception as exc:
                self.msg_queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _clear_history_data(self) -> None:
        if messagebox.askyesno("Limpar Histórico", "Deseja apagar todo o registro de histórico de operações?"):
            self.history_manager.clear_history()
            self._refresh_history_tree()

    def run(self) -> None:
        self.root.mainloop()
