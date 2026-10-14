"""
Gerenciador do LLM local (Phi-3-mini via llama-cpp-python).
Funciona com ou sem modelo instalado (graceful degradation).
"""
import json
import logging
from pathlib import Path

from ..config import settings
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


class LLMManager:
    """Gerencia LLM local via llama-cpp-python."""

    def __init__(self):
        self._llm = None
        self._available = False
        self._error_msg = ""

    @property
    def available(self) -> bool:
        return self._available

    @property
    def error_message(self) -> str:
        return self._error_msg

    def initialize(self) -> bool:
        """
        Tenta carregar o modelo LLM.
        Retorna True se sucesso, False se falha (sistema continua sem LLM).
        """
        if not settings.llm.enabled:
            self._error_msg = "LLM desabilitado na configuração."
            logger.info(self._error_msg)
            return False

        model_path = Path(settings.llm.model_path)
        if not model_path.exists():
            self._error_msg = (
                f"Modelo LLM não encontrado em: {model_path}\n"
                f"Baixe o modelo Phi-3-mini GGUF e coloque em: {model_path.parent}/\n"
                f"O sistema funcionará sem LLM (modo determinístico)."
            )
            logger.warning(self._error_msg)
            return False

        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=settings.llm.n_ctx,
                n_threads=settings.llm.n_threads,
                n_gpu_layers=settings.llm.n_gpu_layers,
                verbose=False,
            )
            self._available = True
            logger.info(f"LLM carregado: {model_path.name}")
            return True
        except ImportError:
            self._error_msg = (
                "llama-cpp-python não instalado. "
                "Instale com: pip install llama-cpp-python"
            )
            logger.warning(self._error_msg)
            return False
        except Exception as e:
            self._error_msg = f"Erro ao carregar LLM: {e}"
            logger.error(self._error_msg)
            return False

    def generate(self, prompt: str, system_prompt: str | None = None,
                 max_tokens: int | None = None) -> str:
        """
        Gera texto usando o LLM.
        Se LLM não disponível, retorna string vazia.
        """
        if not self._available or self._llm is None:
            return ""

        sys_prompt = system_prompt or PromptTemplates.SYSTEM_PROMPT
        mt = max_tokens or settings.llm.max_tokens
        stop_tokens = ["</s>"]

        try:
            response = self._llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=mt,
                temperature=settings.llm.temperature,
                stop=stop_tokens,
            )
            content = response["choices"][0]["message"]["content"]
            return content.strip()
        except Exception as e:
            logger.error(f"Erro na geração LLM: {e}")
            return ""

    def classify_intent_with_llm(self, question: str) -> dict | None:
        """
        Usa o LLM para classificar a intenção da pergunta.
        Retorna dict com 'intent' e 'params' ou None se falhar.
        """
        if not self._available:
            return None

        prompt = PromptTemplates.format_intent(question)
        response = self.generate(prompt, max_tokens=256)

        if not response:
            return None

        try:
            # Extrair JSON da resposta
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            logger.debug(f"LLM retornou JSON inválido: {response}")

        return None

    def answer_with_context(self, question: str, context: str) -> str:
        """
        Gera resposta usando contexto RAG.
        """
        prompt = PromptTemplates.format_rag(question, context)
        return self.generate(prompt)

    def enhance_response(self, question: str, raw_response: str) -> str:
        """
        Usa LLM para melhorar a formatação de uma resposta.
        Se LLM não disponível, retorna a resposta original.
        """
        if not self._available:
            return raw_response

        prompt = PromptTemplates.format_enhance(question, raw_response)
        enhanced = self.generate(prompt, max_tokens=1024)
        return enhanced if enhanced else raw_response
