"""
Build script para RAGQuery.
Gera dois instaladores:
  - Versão A (Light): sem modelo LLM (~50-80 MB)
  - Versão C (Full):  com modelo LLM (~2.8 GB)

Uso:
    python installer/build.py [--version A|C|all] [--skip-pyinstaller]
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTALLER_DIR = PROJECT_ROOT / "installer"
DIST_DIR = INSTALLER_DIR / "dist"
BUILD_DIR = INSTALLER_DIR / "build"
OUTPUT_DIR = INSTALLER_DIR / "output"

MODEL_FILE = PROJECT_ROOT / "models" / "Phi-3-mini-4k-instruct-q4.gguf"
SPEC_FILE = INSTALLER_DIR / "ragquery.spec"

APP_VERSION = "2.0.0"


def step(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def run_pyinstaller():
    """Empacota o app com PyInstaller."""
    step("PyInstaller: Empacotando RAGQuery")

    # Limpar builds anteriores
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--noconfirm",
        str(SPEC_FILE),
    ]

    print(f"  Comando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        print("ERRO: PyInstaller falhou!")
        sys.exit(1)

    app_dir = DIST_DIR / "RAGQuery"
    if not app_dir.exists():
        print(f"ERRO: Diretório de saída não encontrado: {app_dir}")
        sys.exit(1)

    # Copiar ArqsToRAG/ de exemplo
    arqs_src = PROJECT_ROOT / "ArqsToRAG"
    arqs_dst = app_dir / "ArqsToRAG"
    if arqs_src.exists():
        step("Copiando DDLs de exemplo")
        shutil.copytree(arqs_src, arqs_dst, dirs_exist_ok=True)
        print(f"  {sum(1 for _ in arqs_dst.rglob('*'))} arquivos copiados")

    # Criar diretórios necessários
    (app_dir / "data").mkdir(exist_ok=True)
    (app_dir / "models").mkdir(exist_ok=True)
    (app_dir / "logs").mkdir(exist_ok=True)

    print(f"\n  Build concluído: {app_dir}")
    total_size = sum(f.stat().st_size for f in app_dir.rglob('*') if f.is_file())
    print(f"  Tamanho total: {total_size / (1024*1024):.1f} MB")

    return app_dir


def build_version_a(app_dir: Path):
    """Gera instalador Versão A (Light - sem modelo LLM)."""
    step("Versão A (Light): Gerando instalador sem LLM")

    iss_file = INSTALLER_DIR / "ragquery_light.iss"
    if not iss_file.exists():
        print(f"AVISO: {iss_file} não encontrado. Pulando Inno Setup.")
        print("  O build PyInstaller está em:", app_dir)
        return

    _run_inno_setup(iss_file, "RAGQuery-Light-Setup")


def build_version_c(app_dir: Path):
    """Gera instalador Versão C (Full - com modelo LLM)."""
    step("Versão C (Full): Gerando instalador com LLM")

    if not MODEL_FILE.exists():
        print(f"AVISO: Modelo LLM não encontrado: {MODEL_FILE}")
        print("  Baixe com: python -c \"from huggingface_hub import hf_hub_download; ...")
        print("  Pulando Versão C.")
        return

    # Copiar modelo para o dist
    model_dst = app_dir / "models" / MODEL_FILE.name
    if not model_dst.exists():
        print(f"  Copiando modelo LLM ({MODEL_FILE.stat().st_size / (1024*1024):.0f} MB)...")
        shutil.copy2(MODEL_FILE, model_dst)

    iss_file = INSTALLER_DIR / "ragquery_full.iss"
    if not iss_file.exists():
        print(f"AVISO: {iss_file} não encontrado. Pulando Inno Setup.")
        print("  O build PyInstaller (com modelo) está em:", app_dir)
        return

    _run_inno_setup(iss_file, "RAGQuery-Full-Setup")


def _run_inno_setup(iss_file: Path, output_name: str):
    """Executa Inno Setup Compiler."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Tentar encontrar ISCC.exe
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    ]

    iscc = None
    for p in iscc_paths:
        if os.path.exists(p):
            iscc = p
            break

    if not iscc:
        print("  AVISO: Inno Setup (ISCC.exe) não encontrado.")
        print("  Instale de: https://jrsoftware.org/isdl.php")
        print(f"  Depois execute: ISCC.exe {iss_file}")
        return

    cmd = [iscc, str(iss_file)]
    print(f"  Comando: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"  Instalador gerado em: {OUTPUT_DIR}")
    else:
        print(f"  ERRO: Inno Setup falhou com código {result.returncode}")


def main():
    parser = argparse.ArgumentParser(description="RAGQuery - Build Installer")
    parser.add_argument(
        "--version", choices=["A", "C", "all"], default="all",
        help="Versão a construir: A (light), C (full), all (ambas)",
    )
    parser.add_argument(
        "--skip-pyinstaller", action="store_true",
        help="Pular PyInstaller (usa build anterior)",
    )
    args = parser.parse_args()

    step(f"RAGQuery Installer Builder v{APP_VERSION}")
    print(f"  Projeto: {PROJECT_ROOT}")
    print(f"  Versão:  {args.version}")

    # 1. PyInstaller
    app_dir = DIST_DIR / "RAGQuery"
    if not args.skip_pyinstaller:
        app_dir = run_pyinstaller()
    else:
        if not app_dir.exists():
            print(f"ERRO: Build anterior não encontrado: {app_dir}")
            print("  Execute sem --skip-pyinstaller primeiro.")
            sys.exit(1)
        print(f"  Usando build anterior: {app_dir}")

    # 2. Gerar instaladores
    if args.version in ("A", "all"):
        build_version_a(app_dir)

    if args.version in ("C", "all"):
        build_version_c(app_dir)

    step("Build concluído!")
    print(f"  Dist: {DIST_DIR}")
    print(f"  Instaladores: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
