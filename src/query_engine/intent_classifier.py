"""
Classificador de intenção baseado em padrões regex.
Classifica a pergunta do usuário em uma categoria + parâmetros extraídos.
"""
import re
from dataclasses import dataclass, field
from enum import Enum


class IntentType(Enum):
    # Tabelas
    LIST_TABLES = "list_tables"
    COUNT_TABLES = "count_tables"
    TABLES_IN_TABLESPACE = "tables_in_tablespace"
    TABLES_WITH_PREFIX = "tables_with_prefix"
    TABLE_DETAILS = "table_details"
    TABLE_DDL = "table_ddl"

    # Colunas
    COLUMNS_OF_TABLE = "columns_of_table"
    TABLES_WITH_COLUMN = "tables_with_column"
    COLUMNS_NOT_NULL = "columns_not_null"
    COLUMNS_BY_TYPE = "columns_by_type"

    # Índices
    INDEXES_OF_TABLE = "indexes_of_table"
    COUNT_INDEXES = "count_indexes"
    TABLES_WITHOUT_INDEX = "tables_without_index"
    INDEXES_WITH_COLUMN = "indexes_with_column"

    # Constraints
    CONSTRAINTS_OF_TABLE = "constraints_of_table"
    TABLES_REFERENCING = "tables_referencing"
    PK_OF_TABLE = "pk_of_table"
    FKS_OF_TABLE = "fks_of_table"

    # Grants
    GRANTS_ON_TABLE = "grants_on_table"
    TABLES_FOR_GRANTEE = "tables_for_grantee"
    GRANTS_WITH_PRIVILEGE = "grants_with_privilege"

    # Tablespaces
    LIST_TABLESPACES = "list_tablespaces"
    COUNT_TABLES_PER_TABLESPACE = "count_tables_per_tablespace"

    # Roles
    LIST_ROLES = "list_roles"
    ROLES_WITH_PREFIX = "roles_with_prefix"

    # Comentários
    COMMENTS_OF_TABLE = "comments_of_table"
    COLUMNS_WITH_COMMENTS = "columns_with_comments"

    # Owners
    LIST_OWNERS = "list_owners"

    # Busca genérica
    SEARCH_OBJECT = "search_object"

    # Colunas por padrão (LIKE)
    COLUMNS_LIKE = "columns_like"

    # Conversacional
    WHO_ARE_YOU = "who_are_you"
    HELP = "help"

    # Não classificado (fallback para RAG/LLM)
    UNKNOWN = "unknown"


@dataclass
class Intent:
    intent_type: IntentType
    params: dict = field(default_factory=dict)
    confidence: float = 1.0
    original_question: str = ""


# Padrões regex → (IntentType, grupos nomeados para params)
PATTERNS: list[tuple[re.Pattern, IntentType, list[str]]] = [
    # --- TABELAS ---
    (re.compile(
        r'(?:quais|liste|listar|mostre|mostrar|show)\s+(?:as\s+)?tabelas\s+'
        r'(?:do|de|deste|from|que\s+pertencem\s+ao?)\s+(?:owner|schema|usu[aá]rio)\s+'
        r'(\w+)',
        re.IGNORECASE
    ), IntentType.LIST_TABLES, ["owner"]),

    (re.compile(
        r'(?:quais|liste|listar|mostre|show)\s+(?:as\s+)?tabelas\s+'
        r'(?:do|de|deste|from)\s+(\w+)',
        re.IGNORECASE
    ), IntentType.LIST_TABLES, ["owner"]),

    (re.compile(
        r'(?:quantas|count)\s+tabelas',
        re.IGNORECASE
    ), IntentType.COUNT_TABLES, []),

    (re.compile(
        r'tabelas\s+(?:no|do|que\s+est[aã]o\s+no)\s+tablespace\s+(\w+)',
        re.IGNORECASE
    ), IntentType.TABLES_IN_TABLESPACE, ["tablespace"]),

    (re.compile(
        r'tabelas\s+(?:com|que\s+(?:t[eê]m|possuem))\s+prefixo\s+(\w+)',
        re.IGNORECASE
    ), IntentType.TABLES_WITH_PREFIX, ["prefix"]),

    (re.compile(
        r'(?:detalhes?|describe|descreva|info|informa[çc][oõ]es?)\s+'
        r'(?:da\s+)?tabela\s+(\w+)',
        re.IGNORECASE
    ), IntentType.TABLE_DETAILS, ["table_name"]),

    (re.compile(
        r'(?:ddl|cria[çc][aã]o|create)\s+(?:da\s+)?tabela\s+(\w+)',
        re.IGNORECASE
    ), IntentType.TABLE_DDL, ["table_name"]),

    # --- COLUNAS ---
    (re.compile(
        r'(?:quais|liste|mostre|show)\s+(?:as\s+)?colunas\s+'
        r'(?:que\s+)?(?:possuem|t[eê]m|cont[eé]m)\s+(\w+)\s+'
        r'(?:como\s+parte\s+(?:do\s+)?nome|no\s+nome)',
        re.IGNORECASE
    ), IntentType.COLUMNS_LIKE, ["pattern"]),

    (re.compile(
        r'colunas\s+(?:com|que\s+(?:possuem|t[eê]m|cont[eé]m))\s+(\w+)\s+'
        r'(?:no\s+nome|como\s+parte)',
        re.IGNORECASE
    ), IntentType.COLUMNS_LIKE, ["pattern"]),

    (re.compile(
        r'(?:quais|liste|mostre|show)\s+(?:as\s+)?colunas\s+'
        r'(?:da|de|from)\s+(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.COLUMNS_OF_TABLE, ["table_name"]),

    (re.compile(
        r'(?:quais|liste|mostre)\s+(?:as\s+)?tabelas\s+'
        r'(?:que\s+)?(?:possuem|t[eê]m|cont[eé]m|have|with)\s+'
        r'(?:a\s+)?coluna\s+(\w+)',
        re.IGNORECASE
    ), IntentType.TABLES_WITH_COLUMN, ["column_name"]),

    (re.compile(
        r'(?:quais|onde|em\s+quais?)\s+(?:tabelas?)\s+'
        r'(?:existe|tem|aparece|est[aá])\s+(?:a\s+)?(?:coluna\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.TABLES_WITH_COLUMN, ["column_name"]),

    (re.compile(
        r'colunas\s+(?:not\s+null|obrigat[oó]rias?|n[aã]o\s+nulas?)\s+'
        r'(?:da|de|from)\s+(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.COLUMNS_NOT_NULL, ["table_name"]),

    (re.compile(
        r'colunas\s+(?:do\s+tipo|tipo)\s+(DATE|NUMBER|VARCHAR2?|CHAR|CLOB|BLOB|TIMESTAMP)',
        re.IGNORECASE
    ), IntentType.COLUMNS_BY_TYPE, ["data_type"]),

    # --- ÍNDICES ---
    (re.compile(
        r'(?:quais|liste|mostre|show)\s+(?:os\s+)?[ií]ndices?\s+'
        r'(?:da|de|from)\s+(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.INDEXES_OF_TABLE, ["table_name"]),

    (re.compile(
        r'(?:quantos|count)\s+[ií]ndices',
        re.IGNORECASE
    ), IntentType.COUNT_INDEXES, []),

    (re.compile(
        r'tabelas\s+(?:sem|without|que\s+n[aã]o\s+(?:possuem|t[eê]m))\s+[ií]ndice',
        re.IGNORECASE
    ), IntentType.TABLES_WITHOUT_INDEX, []),

    (re.compile(
        r'[ií]ndices?\s+(?:que\s+)?(?:possuem|t[eê]m|cont[eé]m|incluem|usam|with)\s+'
        r'(?:a\s+)?coluna\s+(\w+)',
        re.IGNORECASE
    ), IntentType.INDEXES_WITH_COLUMN, ["column_name"]),

    # --- CONSTRAINTS ---
    (re.compile(
        r'constraints?\s+(?:da|de|from)\s+(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.CONSTRAINTS_OF_TABLE, ["table_name"]),

    (re.compile(
        r'(?:quais\s+)?(?:tabelas?|quem)\s+(?:que\s+)?(?:referenciam?|faz(?:em)?\s+refer[eê]ncia)\s+'
        r'(?:a\s+)?(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.TABLES_REFERENCING, ["table_name"]),

    (re.compile(
        r'(?:pk|primary\s+key|chave\s+prim[aá]ria)\s+'
        r'(?:da|de|from)\s+(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.PK_OF_TABLE, ["table_name"]),

    (re.compile(
        r'(?:fks?|foreign\s+keys?|chave[s]?\s+estrangeira[s]?)\s+'
        r'(?:da|de|from)\s+(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.FKS_OF_TABLE, ["table_name"]),

    # --- GRANTS ---
    (re.compile(
        r'(?:quais|liste|mostre)\s+(?:os\s+)?(?:grants?|permiss[oõ]es|acessos?)\s+'
        r'(?:da|de|na|from|on)\s+(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.GRANTS_ON_TABLE, ["table_name"]),

    (re.compile(
        r'(?:quais|liste|mostre)\s+(?:as\s+)?(?:tabelas?|grants?|permiss[oõ]es|acessos?)\s+'
        r'(?:da|de|que|para)\s+(?:a\s+)?(?:role\s+)?(\w+)\s+(?:acessa|tem)',
        re.IGNORECASE
    ), IntentType.TABLES_FOR_GRANTEE, ["grantee"]),

    (re.compile(
        r'(?:quem|quais\s+roles?)\s+(?:tem|t[eê]m|possui|possuem)\s+'
        r'(?:acesso|permiss[aã]o|grant)\s+'
        r'(?:[àa]\s+|na\s+)?(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.GRANTS_ON_TABLE, ["table_name"]),

    (re.compile(
        r'(?:quem|quais)\s+(?:tem|t[eê]m)\s+(?:permiss[aã]o\s+de\s+)?'
        r'(SELECT|INSERT|UPDATE|DELETE)',
        re.IGNORECASE
    ), IntentType.GRANTS_WITH_PRIVILEGE, ["privilege"]),

    # --- TABLESPACES ---
    (re.compile(
        r'(?:quais|liste|mostre|show)\s+(?:os\s+)?tablespaces?',
        re.IGNORECASE
    ), IntentType.LIST_TABLESPACES, []),

    (re.compile(
        r'(?:quantas|count)\s+tabelas\s+(?:por|per)\s+tablespace',
        re.IGNORECASE
    ), IntentType.COUNT_TABLES_PER_TABLESPACE, []),

    # --- ROLES ---
    (re.compile(
        r'(?:quais|liste|mostre|show)\s+(?:as\s+)?roles?',
        re.IGNORECASE
    ), IntentType.LIST_ROLES, []),

    (re.compile(
        r'roles?\s+(?:que\s+)?(?:come[çc]am?|iniciam?|with\s+prefix)\s+'
        r'(?:com\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.ROLES_WITH_PREFIX, ["prefix"]),

    # --- COMENTÁRIOS ---
    (re.compile(
        r'(?:coment[aá]rios?|comments?)\s+(?:da|de|from)\s+(?:tabela\s+)?(\w+)',
        re.IGNORECASE
    ), IntentType.COMMENTS_OF_TABLE, ["table_name"]),

    (re.compile(
        r'colunas?\s+(?:com|que\s+(?:possuem|t[eê]m))\s+coment[aá]rios?',
        re.IGNORECASE
    ), IntentType.COLUMNS_WITH_COMMENTS, []),

    # --- OWNERS ---
    (re.compile(
        r'(?:quais|liste|mostre|show)\s+(?:os\s+)?owners?',
        re.IGNORECASE
    ), IntentType.LIST_OWNERS, []),

    # --- CONVERSACIONAL ---
    (re.compile(
        r'(?:quem\s+[eé]\s+voc[eê]|quem\s+(?:es\s+)?tu|o\s+que\s+(?:voc[eê]\s+)?[eé]|'
        r'voc[eê]\s+[eé]\s+(?:quem|o\s+qu[eê])|se\s+apresente|me\s+diga\s+quem)',
        re.IGNORECASE
    ), IntentType.WHO_ARE_YOU, []),

    (re.compile(
        r'(?:como\s+(?:voc[eê]\s+)?(?:pode|consegu[ei]|vai)\s+(?:me\s+)?ajudar|'
        r'o\s+que\s+(?:voc[eê]\s+)?(?:faz|consegue|pode\s+fazer|sabe\s+fazer)|'
        r'(?:quais|que)\s+(?:tipo\s+de\s+)?perguntas?\s+(?:eu\s+)?(?:posso|consigo)\s+fazer|'
        r'me\s+ajud[ea]|help|ajuda)',
        re.IGNORECASE
    ), IntentType.HELP, []),
]


class IntentClassifier:
    """Classifica a intenção de uma pergunta do usuário."""

    def classify(self, question: str) -> Intent:
        """Tenta classificar a pergunta usando padrões regex."""
        question = question.strip()

        for pattern, intent_type, param_names in PATTERNS:
            m = pattern.search(question)
            if m:
                params = {}
                for i, name in enumerate(param_names):
                    val = m.group(i + 1)
                    if val:
                        params[name] = val.strip().upper()
                return Intent(
                    intent_type=intent_type,
                    params=params,
                    confidence=0.9,
                    original_question=question,
                )

        # Fallback: tentar extrair nomes de objetos conhecidos
        return Intent(
            intent_type=IntentType.UNKNOWN,
            params={},
            confidence=0.0,
            original_question=question,
        )
