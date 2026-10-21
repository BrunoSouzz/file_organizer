"""Script de compilação automatizada para gerar o executável (.exe) do File Organizer."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Garante suporte a UTF-8 no console do Windows
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def build() -> int:
    project_root = Path(__file__).resolve().parent
    assets_dir = project_root / "assets"
    icon_path = assets_dir / "icon.ico"

    print("==================================================")
    print(" [Build] File Organizer Pro - Compilador Executavel (.exe)")
    print("==================================================")

    if not icon_path.exists():
        print(f"Aviso: Icone nao encontrado em {icon_path}. O app usara o icone padrao.")

    dist_dir = project_root / "dist"

    # Comando PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "FileOrganizer",
        "--add-data",
        f"{assets_dir};assets",
        "--collect-data",
        "ttkbootstrap",
        str(project_root / "main.py"),
    ]

    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    print("\nExecutando PyInstaller...")
    print(" ".join(cmd))
    print("--------------------------------------------------")

    result = subprocess.run(cmd, cwd=str(project_root))
    if result.returncode != 0:
        print(f"\n[Falha] Erro na compilacao. Codigo de saida: {result.returncode}")
        return result.returncode

    exe_path = dist_dir / "FileOrganizer.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n==================================================")
        print(" [Sucesso] Executavel gerado com sucesso!")
        print(f" Local: {exe_path}")
        print(f" Tamanho: {size_mb:.2f} MB")
        print("==================================================")
        return 0
    else:
        print("\n[Erro] Executavel nao encontrado em dist/.")
        return 1


if __name__ == "__main__":
    raise SystemExit(build())
