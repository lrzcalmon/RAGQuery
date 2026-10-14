"""
Inicia o servidor web do RAGQuery.

Uso:
    python scripts/serve.py [--host HOST] [--port PORT] [--debug]
"""
import argparse
import logging
import sys
from pathlib import Path

# Adicionar raiz ao path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings, METADATA_DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("serve")


def main():
    parser = argparse.ArgumentParser(description="RAGQuery - Servidor Web")
    parser.add_argument("--host", default=settings.web.host, help="Host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=settings.web.port, help="Porta (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Modo debug")
    args = parser.parse_args()

    # Verificar pré-requisitos
    if not METADATA_DB_PATH.exists():
        log.error(
            f"Banco de metadados não encontrado: {METADATA_DB_PATH}\n"
            f"Execute primeiro: python scripts/ingest.py --input-dir ArqsToRAG/"
        )
        sys.exit(1)

    log.info("=" * 50)
    log.info("RAGQuery - Servidor Web")
    log.info("=" * 50)

    from src.web.app import create_app
    app = create_app()

    log.info(f"\nServidor iniciando em: http://{args.host}:{args.port}")
    log.info("Pressione Ctrl+C para parar.\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
