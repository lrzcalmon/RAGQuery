"""
Flask application factory.
"""
import logging
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from ..config import settings, METADATA_DB_PATH
from ..metadata_store.db_manager import MetadataDB
from ..metadata_store.queries import MetadataQueries
from ..query_engine.intent_classifier import IntentClassifier
from ..query_engine.sql_generator import SQLGenerator
from ..query_engine.response_builder import ResponseBuilder
from ..llm.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class AppState:
    """Estado global da aplicação."""
    db: MetadataDB | None = None
    mq: MetadataQueries | None = None
    classifier: IntentClassifier | None = None
    sql_gen: SQLGenerator | None = None
    response_builder: ResponseBuilder | None = None
    llm: LLMManager | None = None
    embedder_model = None


state = AppState()


def create_app() -> Flask:
    """Cria e configura a aplicação Flask."""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.config["SECRET_KEY"] = "ragquery-local-only"
    CORS(app)

    # Inicializar componentes
    _init_components()

    # Registrar rotas
    from .routes import bp
    app.register_blueprint(bp)

    return app


def _init_components():
    """Inicializa todos os componentes do sistema."""
    # Metadata DB
    if not METADATA_DB_PATH.exists():
        logger.warning(
            f"Banco de metadados não encontrado: {METADATA_DB_PATH}\n"
            "Execute 'python scripts/ingest.py' primeiro."
        )
        return

    state.db = MetadataDB(METADATA_DB_PATH)
    state.db.connect()

    state.mq = MetadataQueries(state.db)
    state.classifier = IntentClassifier()
    state.sql_gen = SQLGenerator(state.mq)
    state.response_builder = ResponseBuilder()

    # LLM (opcional)
    state.llm = LLMManager()
    llm_ok = state.llm.initialize()
    if llm_ok:
        logger.info("LLM carregado com sucesso.")
    else:
        logger.info(f"LLM não disponível: {state.llm.error_message}")
        logger.info("Sistema operando em modo determinístico.")

    # Estatísticas
    stats = state.db.get_stats()
    logger.info(f"Metadata DB stats: {stats}")
