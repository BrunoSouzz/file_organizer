"""Motor principal de organização de arquivos."""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable

from .history import HistoryManager
from .models import BatchOperation, MovedFile, OrganizationResult, Rule
from .rules import match_file_rule


def unique_destination(path: Path) -> Path:
    """Gera um caminho alternativo caso já exista um arquivo com o mesmo nome no destino."""
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def is_file_ready(file_path: Path) -> bool:
    """
    Verifica se o arquivo está livre para ser movido (não está em gravação por navegador/app).
    Ignora arquivos temporários típicos de download como .crdownload, .part, .tmp.
    """
    temp_extensions = {".crdownload", ".part", ".tmp", ".download", ".aria2"}
    if file_path.suffix.lower() in temp_extensions or file_path.name.startswith("~$"):
        return False
    try:
        # Tenta abrir em modo append sem alterar nada para checar trava do sistema
        with file_path.open("a+b"):
            pass
        return True
    except (PermissionError, OSError):
        return False


def organize(
    source: Path,
    destination: Path,
    rules: list[Rule],
    *,
    recursive: bool = False,
    dry_run: bool = False,
    progress_callback: Callable[[int, int, str], None] | None = None,
    reporter: Callable[[str], None] | None = None,
    history_manager: HistoryManager | None = None,
) -> OrganizationResult:
    """
    Organiza os arquivos da origem para o destino baseando-se nas regras fornecidas.
    Suporta callback de progresso para atualização fluida da interface gráfica.
    """
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()

    if not source.is_dir():
        raise ValueError(f"A pasta de origem informada não existe: {source}")
    if source == destination:
        raise ValueError("A pasta de destino não pode ser igual à pasta de origem.")
    if destination.is_relative_to(source):
        raise ValueError("A pasta de destino não pode estar dentro da pasta de origem.")

    report = reporter or (lambda _: None)
    update_progress = progress_callback or (lambda _c, _t, _f: None)

    # 1. Coleta a lista de arquivos para calcular o progresso total
    if recursive:
        candidate_files = [p for p in source.rglob("*") if p.is_file()]
    else:
        candidate_files = [p for p in source.iterdir() if p.is_file()]

    total_files = len(candidate_files)
    result = OrganizationResult()
    moved_records: list[MovedFile] = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report(f"Iniciando análise de {total_files} arquivo(s)...")

    for idx, item in enumerate(candidate_files, start=1):
        update_progress(idx, total_files, item.name)

        # Checa se o arquivo não está sendo baixado no momento
        if not is_file_ready(item):
            result.skipped.append(item)
            report(f"[Ignorado - Em gravação] {item.name}")
            continue

        matched_rule = match_file_rule(item, rules)
        if not matched_rule:
            result.skipped.append(item)
            continue

        # Determina pasta de destino (específica da regra ou categoria padrão)
        if matched_rule.custom_destination:
            target_dir = Path(matched_rule.custom_destination).expanduser().resolve()
        else:
            target_dir = destination / matched_rule.name

        target = unique_destination(target_dir / item.name)

        try:
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(target))
                moved_records.append(
                    MovedFile(
                        source=str(item),
                        destination=str(target),
                        timestamp=current_time,
                        rule_name=matched_rule.name,
                    )
                )

            result.moved.append((item, target))
            prefix = "[Simulação] " if dry_run else "✔ "
            report(f"{prefix}{item.name} -> {target.parent.name}/{target.name}")

        except OSError as exc:
            result.errors.append((item, str(exc)))
            report(f"❌ Erro ao mover {item.name}: {exc}")

    # Salva histórico caso arquivos tenham sido movidos
    if not dry_run and moved_records and history_manager is not None:
        batch = BatchOperation(
            id=str(uuid.uuid4())[:8],
            timestamp=current_time,
            source_dir=str(source),
            destination_dir=str(destination),
            files=moved_records,
        )
        history_manager.record_batch(batch)

    report(
        f"Concluído: {len(result.moved)} movido(s), "
        f"{len(result.skipped)} ignorado(s), {len(result.errors)} erro(s)."
    )
    return result
