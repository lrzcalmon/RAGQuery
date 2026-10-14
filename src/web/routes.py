"""
Rotas da API e páginas web.
"""
import logging
import time

from flask import Blueprint, render_template, request, jsonify

from .app import state
from ..query_engine.intent_classifier import IntentType

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Página principal com interface de chat."""
    db_ready = state.db is not None
    llm_ready = state.llm is not None and state.llm.available
    stats = state.db.get_stats() if db_ready else {}
    return render_template(
        "chat.html",
        db_ready=db_ready,
        llm_ready=llm_ready,
        stats=stats,
    )


@bp.route("/api/ask", methods=["POST"])
def ask():
    """Endpoint principal: recebe pergunta, retorna resposta."""
    if state.db is None:
        return jsonify({
            "error": "Banco de metadados não inicializado. Execute o script de ingestão.",
            "answer": "",
        }), 503

    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Pergunta vazia.", "answer": ""}), 400

    start = time.time()

    # 1. Classificar intenção
    intent = state.classifier.classify(question)
    logger.info(f"Intent: {intent.intent_type.value} | Params: {intent.params}")

    # 2. Se classificado com confiança, executar via SQL direto
    if intent.intent_type != IntentType.UNKNOWN:
        try:
            result = state.sql_gen.execute(intent)
            answer = state.response_builder.build(result)

            # Enriquecer respostas conversacionais com LLM quando disponível
            if (intent.intent_type in (IntentType.WHO_ARE_YOU, IntentType.HELP)
                    and state.llm and state.llm.available):
                try:
                    llm_answer = state.llm.generate(
                        f"O usuário perguntou: {question}\n\n"
                        f"Informação base:\n{answer}\n\n"
                        f"Reescreva de forma amigável e natural em português. "
                        f"Mantenha TODOS os dados técnicos. Use markdown. Seja conciso.",
                        max_tokens=300,
                    )
                    if llm_answer and len(llm_answer) > 20:
                        answer = llm_answer
                except Exception as e:
                    logger.warning(f"LLM enhancement falhou: {e}")

        except Exception as e:
            logger.error(f"Erro na execução SQL: {e}")
            answer = f"Erro ao processar consulta: {e}"

        elapsed = time.time() - start
        return jsonify({
            "answer": answer,
            "intent": intent.intent_type.value,
            "params": intent.params,
            "source": "structured",
            "elapsed_ms": round(elapsed * 1000),
        })

    # 3. Fallback: tentar com LLM para classificar
    if state.llm and state.llm.available:
        llm_intent = state.llm.classify_intent_with_llm(question)
        if llm_intent and llm_intent.get("intent") != "unknown":
            # Tentar mapear o intent do LLM
            try:
                it = IntentType(llm_intent["intent"])
                from ..query_engine.intent_classifier import Intent
                mapped = Intent(
                    intent_type=it,
                    params=llm_intent.get("params", {}),
                    confidence=0.7,
                    original_question=question,
                )
                result = state.sql_gen.execute(mapped)
                answer = state.response_builder.build(result)

                elapsed = time.time() - start
                return jsonify({
                    "answer": answer,
                    "intent": it.value,
                    "params": llm_intent.get("params", {}),
                    "source": "llm_classified",
                    "elapsed_ms": round(elapsed * 1000),
                })
            except (ValueError, KeyError):
                pass

    # 4. Fallback final: busca genérica por palavras-chave
    answer = _fallback_search(question)

    elapsed = time.time() - start
    return jsonify({
        "answer": answer,
        "intent": "fallback",
        "params": {},
        "source": "fallback",
        "elapsed_ms": round(elapsed * 1000),
    })


def _fallback_search(question: str) -> str:
    """Busca genérica extraindo palavras-chave da pergunta."""
    # Extrair possíveis nomes de objetos (palavras em maiúsculo ou com underscore)
    import re
    words = re.findall(r'[A-Z_]{3,}', question.upper())

    if not words:
        words = re.findall(r'\b\w{4,}\b', question)

    results_parts = []
    for word in words[:3]:
        search = state.mq.search_object(word)
        has_results = any(v for v in search.values() if v)
        if has_results:
            builder = state.response_builder
            results_parts.append(builder._fmt_search_object(search, {"name": word}))

    if results_parts:
        return "\n\n---\n\n".join(results_parts)

    return (
        "Não consegui interpretar sua pergunta. Tente perguntas como:\n\n"
        "- Quais as tabelas do owner LOJA?\n"
        "- Quais tabelas possuem a coluna COD_LOJA?\n"
        "- Quais os índices da tabela VENDA_PEDIDO?\n"
        "- Quais roles existem?\n"
        "- Quais grants na tabela AUD_INCONSISTENCIA?\n"
        "- Quais tabelas referenciam VENDA_LOJA?"
    )


@bp.route("/api/stats")
def stats():
    """Retorna estatísticas do banco de metadados."""
    if state.db is None:
        return jsonify({"error": "DB não inicializado"}), 503
    return jsonify(state.db.get_stats())


@bp.route("/api/health")
def health():
    """Health check."""
    return jsonify({
        "status": "ok",
        "db_ready": state.db is not None,
        "llm_ready": state.llm is not None and state.llm.available,
    })


@bp.route("/api/llm/status")
def llm_status():
    """Status detalhado do LLM."""
    from ..config import settings, MODELS_DIR
    from pathlib import Path

    model_path = Path(settings.llm.model_path)
    model_exists = model_path.exists()
    model_size_mb = round(model_path.stat().st_size / (1024 * 1024), 1) if model_exists else 0

    return jsonify({
        "available": state.llm is not None and state.llm.available,
        "enabled": settings.llm.enabled,
        "model_path": str(model_path),
        "model_exists": model_exists,
        "model_size_mb": model_size_mb,
        "model_name": model_path.name,
        "error": state.llm.error_message if state.llm else "",
    })


@bp.route("/api/llm/download", methods=["POST"])
def llm_download():
    """Inicia download do modelo LLM em background."""
    from ..config import MODELS_DIR, settings
    from pathlib import Path
    import threading

    model_path = Path(settings.llm.model_path)
    if model_path.exists():
        return jsonify({"status": "exists", "message": "Modelo já existe."})

    # Verificar se já está baixando
    if getattr(state, '_llm_downloading', False):
        return jsonify({"status": "downloading", "message": "Download em andamento..."})

    state._llm_downloading = True
    state._llm_download_progress = 0
    state._llm_download_error = None
    state._llm_download_done = False

    def _download():
        try:
            import urllib.request
            url = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            temp_path = model_path.with_suffix('.tmp')

            req = urllib.request.Request(url, headers={"User-Agent": "RAGQuery/1.0"})
            response = urllib.request.urlopen(req)
            total = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            block_size = 1024 * 1024  # 1 MB

            with open(temp_path, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        state._llm_download_progress = round(downloaded / total * 100, 1)

            temp_path.rename(model_path)
            state._llm_download_done = True
            state._llm_download_progress = 100
            logger.info(f"Modelo LLM baixado: {model_path}")
        except Exception as e:
            state._llm_download_error = str(e)
            logger.error(f"Erro no download do LLM: {e}")
        finally:
            state._llm_downloading = False

    t = threading.Thread(target=_download, daemon=True)
    t.start()

    return jsonify({"status": "started", "message": "Download iniciado..."})


@bp.route("/api/llm/download/progress")
def llm_download_progress():
    """Progresso do download do LLM."""
    return jsonify({
        "downloading": getattr(state, '_llm_downloading', False),
        "progress": getattr(state, '_llm_download_progress', 0),
        "done": getattr(state, '_llm_download_done', False),
        "error": getattr(state, '_llm_download_error', None),
    })


@bp.route("/api/llm/activate", methods=["POST"])
def llm_activate():
    """Tenta ativar o LLM após download."""
    from ..llm.llm_manager import LLMManager
    state.llm = LLMManager()
    ok = state.llm.initialize()
    if ok:
        return jsonify({"status": "ok", "message": "LLM ativado com sucesso!"})
    else:
        return jsonify({
            "status": "error",
            "message": state.llm.error_message,
        }), 500
