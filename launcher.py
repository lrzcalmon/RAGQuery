"""
RAGQuery Launcher - Ponto de entrada principal.
Executa ingestão automática (se necessário), inicia Flask e abre o browser.
"""
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Garantir que o diretório do executável seja o raiz do projeto
if getattr(sys, 'frozen', False):
    # Empacotado pelo PyInstaller
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

os.chdir(str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("launcher")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_free_port(start: int = 5000, end: int = 5100) -> int:
    for port in range(start, end):
        if not is_port_in_use(port):
            return port
    return start


def run_auto_ingest():
    """Executa ingestão automática se o banco não existir e houver DDLs."""
    from src.config import METADATA_DB_PATH, ARQS_TO_RAG_DIR

    if METADATA_DB_PATH.exists():
        log.info("Banco de metadados encontrado. Pulando ingestão.")
        return True

    if not ARQS_TO_RAG_DIR.exists():
        ARQS_TO_RAG_DIR.mkdir(parents=True, exist_ok=True)
        log.warning(
            f"Diretório ArqsToRAG/ criado. Coloque arquivos DDL/SQL/TXT nele "
            f"e reinicie o aplicativo."
        )
        return False

    # Verificar se há arquivos
    from src.config import SUPPORTED_EXTENSIONS
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(ARQS_TO_RAG_DIR.rglob(f"*{ext}"))

    if not files:
        log.warning(
            f"Nenhum arquivo DDL encontrado em {ARQS_TO_RAG_DIR}.\n"
            f"Coloque arquivos .ddl, .sql ou .txt e reinicie."
        )
        return False

    log.info(f"Executando ingestão automática de {len(files)} arquivo(s)...")

    try:
        from scripts.ingest import run_ingest
        run_ingest(ARQS_TO_RAG_DIR, recreate=True, no_vectors=True)
        return True
    except Exception as e:
        log.error(f"Erro na ingestão: {e}")
        return False


def open_browser(port: int, delay: float = 1.5):
    """Abre o browser após um pequeno delay."""
    time.sleep(delay)
    url = f"http://127.0.0.1:{port}"
    log.info(f"Abrindo navegador: {url}")
    webbrowser.open(url)


def main():
    log.info("=" * 50)
    log.info("  RAGQuery - Consulta DDL Oracle")
    log.info("=" * 50)
    log.info(f"Diretório base: {BASE_DIR}")

    # 1. Auto-ingestão
    db_ok = run_auto_ingest()
    if not db_ok:
        log.warning("Sistema iniciando sem dados. Use a interface para instruções.")

    # 2. Encontrar porta livre
    from src.config import settings
    port = settings.web.port
    if is_port_in_use(port):
        port = find_free_port(port + 1)
        log.info(f"Porta {settings.web.port} em uso. Usando {port}.")

    # 3. Criar app Flask
    from src.web.app import create_app
    app = create_app()

    # 4. Abrir browser em thread separada
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()

    # 5. Iniciar servidor
    log.info(f"\nServidor em: http://127.0.0.1:{port}")
    log.info("Feche esta janela para encerrar o RAGQuery.\n")

    try:
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        log.info("Encerrando RAGQuery...")


if __name__ == "__main__":
    main()
