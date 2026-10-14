"""
Configurações centrais do RAGQuery v2.
"""
import sys
from pathlib import Path
from pydantic import BaseModel, Field


# Paths base — detecta se empacotado pelo PyInstaller
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARQS_TO_RAG_DIR = PROJECT_ROOT / "ArqsToRAG"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Criar diretórios se não existem
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

METADATA_DB_PATH = DATA_DIR / "metadata.db"
CHROMA_STORE_PATH = DATA_DIR / "chroma_store"

SUPPORTED_EXTENSIONS = {".ddl", ".sql", ".txt"}


class EmbeddingSettings(BaseModel):
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 64
    device: str = "cpu"


class LLMSettings(BaseModel):
    model_path: str = str(MODELS_DIR / "Phi-3-mini-4k-instruct-q4.gguf")
    n_ctx: int = 4096
    n_threads: int = 4
    n_gpu_layers: int = 0
    temperature: float = 0.3
    max_tokens: int = 2048
    enabled: bool = True


class WebSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False


class Settings(BaseModel):
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    web: WebSettings = Field(default_factory=WebSettings)
    supported_extensions: set[str] = Field(default_factory=lambda: SUPPORTED_EXTENSIONS)
    log_level: str = "INFO"


settings = Settings()
