"""
Script de ingestão: parseia DDL e popula SQLite + ChromaDB.

Uso:
    python scripts/ingest.py --input-dir ArqsToRAG/ [--recreate] [--no-vectors]
"""
import argparse
import logging
import sys
import time
from pathlib import Path

# Adicionar raiz ao path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ARQS_TO_RAG_DIR, METADATA_DB_PATH, SUPPORTED_EXTENSIONS
from src.ddl_parser.oracle_parser import OracleDDLParser
from src.metadata_store.db_manager import MetadataDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ingest")


def find_ddl_files(input_dir: Path) -> list[Path]:
    """Encontra todos os arquivos DDL/SQL/TXT recursivamente."""
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(input_dir.rglob(f"*{ext}"))
    # Ordenar por nome
    return sorted(files)


def run_ingest(input_dir: Path, recreate: bool = False, no_vectors: bool = False):
    start = time.time()

    log.info("=" * 60)
    log.info("RAGQuery - Pipeline de Ingestão")
    log.info("=" * 60)
    log.info(f"Diretório de entrada: {input_dir}")
    log.info(f"Banco de metadados: {METADATA_DB_PATH}")
    log.info(f"Modo: {'RECRIAR' if recreate else 'INCREMENTAL'}")

    # 1. Encontrar arquivos
    files = find_ddl_files(input_dir)
    if not files:
        log.error(f"Nenhum arquivo suportado encontrado em {input_dir}")
        log.info(f"Extensões suportadas: {SUPPORTED_EXTENSIONS}")
        sys.exit(1)

    log.info(f"\nArquivos encontrados: {len(files)}")
    for f in files:
        log.info(f"  - {f.name} ({f.stat().st_size / 1024:.0f} KB)")

    # 2. Inicializar banco
    db = MetadataDB(METADATA_DB_PATH)
    db.connect()

    if recreate:
        log.info("\nRecriando banco de metadados...")
        db.recreate()
    else:
        db.create_schema()

    # 3. Parsear cada arquivo
    parser = OracleDDLParser()
    total_stats = {
        "tables": 0, "columns": 0, "indexes": 0, "constraints": 0,
        "grants": 0, "tablespaces": 0, "roles": 0, "comments": 0,
    }

    for file_path in files:
        log.info(f"\n{'─' * 40}")
        log.info(f"Processando: {file_path.name}")

        # Verificar se já foi ingerido (modo incremental)
        if not recreate and db.is_file_ingested(file_path):
            log.info(f"  → Arquivo já ingerido (hash igual). Pulando.")
            continue

        try:
            result = parser.parse_file(file_path)

            log.info(f"  Tabelas:      {len(result.tables)}")
            log.info(f"  Colunas:      {len(result.columns)}")
            log.info(f"  Índices:      {len(result.indexes)}")
            log.info(f"  Constraints:  {len(result.constraints)}")
            log.info(f"  Grants:       {len(result.grants)}")
            log.info(f"  Tablespaces:  {len(result.tablespaces)}")
            log.info(f"  Roles:        {len(result.roles)}")
            log.info(f"  Comentários:  {len(result.comments)}")

            # Inserir no banco
            db.insert_parse_result(result, file_path)

            total_stats["tables"] += len(result.tables)
            total_stats["columns"] += len(result.columns)
            total_stats["indexes"] += len(result.indexes)
            total_stats["constraints"] += len(result.constraints)
            total_stats["grants"] += len(result.grants)
            total_stats["tablespaces"] += len(result.tablespaces)
            total_stats["roles"] += len(result.roles)
            total_stats["comments"] += len(result.comments)

        except Exception as e:
            log.error(f"  ERRO ao processar {file_path.name}: {e}")
            import traceback
            traceback.print_exc()

    # 4. Gerar embeddings (opcional)
    if not no_vectors:
        try:
            log.info(f"\n{'─' * 40}")
            log.info("Gerando embeddings para busca semântica...")
            _generate_vectors(db, recreate)
        except ImportError as e:
            log.warning(f"Embeddings não gerados (dependência faltando): {e}")
            log.warning("Execute: pip install sentence-transformers chromadb")
        except Exception as e:
            log.warning(f"Erro ao gerar embeddings: {e}")

    # 5. Resumo
    elapsed = time.time() - start
    final_stats = db.get_stats()
    db.close()

    log.info(f"\n{'=' * 60}")
    log.info("INGESTÃO CONCLUÍDA COM SUCESSO")
    log.info(f"{'=' * 60}")
    log.info(f"Tempo total: {elapsed:.1f}s")
    log.info(f"\nEstatísticas finais do banco:")
    for key, val in final_stats.items():
        name = key.replace("ddl_", "").replace("_", " ").title()
        log.info(f"  {name}: {val}")
    log.info(f"\nBanco salvo em: {METADATA_DB_PATH}")


def _generate_vectors(db: MetadataDB, recreate: bool):
    """Gera embeddings e salva no ChromaDB."""
    from src.vector_store.embedder import DDLEmbedder
    from src.vector_store.chroma_manager import ChromaManager

    embedder = DDLEmbedder(db)

    log.info("  Construindo documentos a partir dos metadados...")
    documents = embedder.build_documents()
    log.info(f"  Documentos criados: {len(documents)}")

    if not documents:
        log.warning("  Nenhum documento para gerar embeddings.")
        return

    log.info("  Gerando embeddings (pode demorar na primeira vez)...")
    documents = embedder.generate_embeddings(documents)

    log.info("  Salvando no ChromaDB...")
    chroma = ChromaManager()
    if recreate:
        chroma.recreate_collection()
    chroma.add_documents(documents)
    chroma.persist()

    log.info(f"  ChromaDB: {chroma.count()} documentos indexados.")


def main():
    parser = argparse.ArgumentParser(description="RAGQuery - Ingestão de DDL")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=ARQS_TO_RAG_DIR,
        help=f"Diretório com arquivos DDL/SQL/TXT (default: {ARQS_TO_RAG_DIR})",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recriar banco (apaga dados anteriores)",
    )
    parser.add_argument(
        "--no-vectors",
        action="store_true",
        help="Pular geração de embeddings/ChromaDB",
    )
    args = parser.parse_args()

    if not args.input_dir.exists():
        log.error(f"Diretório não encontrado: {args.input_dir}")
        sys.exit(1)

    run_ingest(args.input_dir, args.recreate, args.no_vectors)


if __name__ == "__main__":
    main()
