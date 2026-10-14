"""
Templates de prompt para o LLM.
"""


class PromptTemplates:
    """Templates para interação com LLM."""

    SYSTEM_PROMPT = (
        "Você é um assistente especializado em bancos de dados Oracle. "
        "Você responde perguntas sobre a estrutura do banco (tabelas, colunas, índices, "
        "constraints, grants, roles, tablespaces) usando EXCLUSIVAMENTE os dados fornecidos. "
        "Nunca invente informações que não estejam no contexto. "
        "Se não houver informação suficiente, diga claramente. "
        "Responda em português do Brasil de forma concisa e técnica."
    )

    INTENT_CLASSIFICATION_PROMPT = (
        "Classifique a seguinte pergunta sobre um banco de dados Oracle.\n"
        "Categorias possíveis:\n"
        "- list_tables: listar tabelas\n"
        "- columns_of_table: colunas de uma tabela\n"
        "- tables_with_column: tabelas que possuem certa coluna\n"
        "- indexes_of_table: índices de uma tabela\n"
        "- constraints_of_table: constraints de uma tabela\n"
        "- grants_on_table: grants de uma tabela\n"
        "- tables_referencing: tabelas que referenciam outra via FK\n"
        "- list_roles: listar roles\n"
        "- list_tablespaces: listar tablespaces\n"
        "- list_owners: listar owners\n"
        "- search_object: busca genérica\n"
        "- unknown: não classificável\n\n"
        "Pergunta: {question}\n\n"
        "Responda APENAS com o JSON: {{\"intent\": \"<categoria>\", \"params\": {{...}}}}"
    )

    RAG_ANSWER_PROMPT = (
        "Use o contexto abaixo para responder a pergunta do usuário.\n"
        "REGRA: Responda SOMENTE com base no contexto fornecido.\n"
        "Se o contexto não contiver a resposta, diga 'Não encontrei esta informação nos dados indexados.'\n\n"
        "--- CONTEXTO ---\n{context}\n--- FIM DO CONTEXTO ---\n\n"
        "Pergunta: {question}\n\n"
        "Resposta:"
    )

    ENHANCE_RESPONSE_PROMPT = (
        "Reformule a seguinte resposta técnica de forma clara e organizada em português.\n"
        "Mantenha a precisão dos dados. Use markdown para formatação.\n\n"
        "Dados brutos:\n{raw_response}\n\n"
        "Pergunta original: {question}\n\n"
        "Resposta formatada:"
    )

    @classmethod
    def format_intent(cls, question: str) -> str:
        return cls.INTENT_CLASSIFICATION_PROMPT.format(question=question)

    @classmethod
    def format_rag(cls, question: str, context: str) -> str:
        return cls.RAG_ANSWER_PROMPT.format(question=question, context=context)

    @classmethod
    def format_enhance(cls, question: str, raw_response: str) -> str:
        return cls.ENHANCE_RESPONSE_PROMPT.format(
            question=question, raw_response=raw_response
        )
