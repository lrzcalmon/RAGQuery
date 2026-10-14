"""
Gera e executa queries SQL contra o metadata store
baseado na intenção classificada.
"""
from .intent_classifier import Intent, IntentType
from ..metadata_store.queries import MetadataQueries


class SQLGenerator:
    """Mapeia Intent → execução de query no MetadataQueries."""

    def __init__(self, mq: MetadataQueries):
        self.mq = mq

    def execute(self, intent: Intent) -> dict:
        """
        Executa a query correspondente à intenção.
        Retorna: {"data": list|dict, "query_type": str, "params": dict}
        """
        it = intent.intent_type
        p = intent.params

        handler = self._HANDLERS.get(it)
        if not handler:
            return {"data": None, "query_type": it.value, "params": p}

        data = handler(self, p)
        return {"data": data, "query_type": it.value, "params": p}

    # ----------------------------------------------------------------
    # Handlers por tipo de intent
    # ----------------------------------------------------------------
    def _list_tables(self, p):
        return self.mq.list_tables(p.get("owner"))

    def _count_tables(self, p):
        return self.mq.count_tables(p.get("owner"))

    def _tables_in_tablespace(self, p):
        return self.mq.tables_in_tablespace(p["tablespace"])

    def _tables_with_prefix(self, p):
        return self.mq.tables_with_prefix(p["prefix"])

    def _table_details(self, p):
        return self.mq.table_details(p["table_name"], p.get("owner"))

    def _table_ddl(self, p):
        detail = self.mq.table_details(p["table_name"], p.get("owner"))
        if detail:
            return {"ddl": detail.get("full_ddl", "")}
        return None

    def _columns_of_table(self, p):
        return self.mq.columns_of_table(p["table_name"], p.get("owner"))

    def _tables_with_column(self, p):
        return self.mq.tables_with_column(p["column_name"])

    def _columns_not_null(self, p):
        return self.mq.columns_not_null(p["table_name"])

    def _columns_by_type(self, p):
        return self.mq.columns_by_type(p["data_type"])

    def _indexes_of_table(self, p):
        return self.mq.indexes_of_table(p["table_name"])

    def _count_indexes(self, p):
        return self.mq.count_indexes()

    def _tables_without_index(self, p):
        return self.mq.tables_without_index()

    def _indexes_with_column(self, p):
        return self.mq.indexes_with_column(p["column_name"])

    def _constraints_of_table(self, p):
        return self.mq.constraints_of_table(p["table_name"])

    def _tables_referencing(self, p):
        return self.mq.tables_referencing(p["table_name"])

    def _pk_of_table(self, p):
        return self.mq.pk_of_table(p["table_name"])

    def _fks_of_table(self, p):
        return self.mq.fks_of_table(p["table_name"])

    def _grants_on_table(self, p):
        return self.mq.grants_on_table(p["table_name"])

    def _tables_for_grantee(self, p):
        return self.mq.tables_for_grantee(p["grantee"])

    def _grants_with_privilege(self, p):
        return self.mq.grants_with_privilege(p["privilege"])

    def _list_tablespaces(self, p):
        return self.mq.list_tablespaces()

    def _count_tables_per_tablespace(self, p):
        return self.mq.count_tables_per_tablespace()

    def _list_roles(self, p):
        return self.mq.list_roles()

    def _roles_with_prefix(self, p):
        return self.mq.roles_with_prefix(p["prefix"])

    def _comments_of_table(self, p):
        return self.mq.comments_of_table(p["table_name"])

    def _columns_with_comments(self, p):
        return self.mq.columns_with_comments()

    def _list_owners(self, p):
        return self.mq.list_owners()

    def _search_object(self, p):
        return self.mq.search_object(p.get("name", ""))

    def _columns_like(self, p):
        return self.mq.tables_with_column_like(p["pattern"])

    def _who_are_you(self, p):
        return {"type": "conversational", "intent": "who_are_you"}

    def _help(self, p):
        return {"type": "conversational", "intent": "help"}

    # Mapa de handlers
    _HANDLERS = {
        IntentType.LIST_TABLES: _list_tables,
        IntentType.COUNT_TABLES: _count_tables,
        IntentType.TABLES_IN_TABLESPACE: _tables_in_tablespace,
        IntentType.TABLES_WITH_PREFIX: _tables_with_prefix,
        IntentType.TABLE_DETAILS: _table_details,
        IntentType.TABLE_DDL: _table_ddl,
        IntentType.COLUMNS_OF_TABLE: _columns_of_table,
        IntentType.TABLES_WITH_COLUMN: _tables_with_column,
        IntentType.COLUMNS_NOT_NULL: _columns_not_null,
        IntentType.COLUMNS_BY_TYPE: _columns_by_type,
        IntentType.INDEXES_OF_TABLE: _indexes_of_table,
        IntentType.COUNT_INDEXES: _count_indexes,
        IntentType.TABLES_WITHOUT_INDEX: _tables_without_index,
        IntentType.INDEXES_WITH_COLUMN: _indexes_with_column,
        IntentType.CONSTRAINTS_OF_TABLE: _constraints_of_table,
        IntentType.TABLES_REFERENCING: _tables_referencing,
        IntentType.PK_OF_TABLE: _pk_of_table,
        IntentType.FKS_OF_TABLE: _fks_of_table,
        IntentType.GRANTS_ON_TABLE: _grants_on_table,
        IntentType.TABLES_FOR_GRANTEE: _tables_for_grantee,
        IntentType.GRANTS_WITH_PRIVILEGE: _grants_with_privilege,
        IntentType.LIST_TABLESPACES: _list_tablespaces,
        IntentType.COUNT_TABLES_PER_TABLESPACE: _count_tables_per_tablespace,
        IntentType.LIST_ROLES: _list_roles,
        IntentType.ROLES_WITH_PREFIX: _roles_with_prefix,
        IntentType.COMMENTS_OF_TABLE: _comments_of_table,
        IntentType.COLUMNS_WITH_COMMENTS: _columns_with_comments,
        IntentType.LIST_OWNERS: _list_owners,
        IntentType.SEARCH_OBJECT: _search_object,
        IntentType.COLUMNS_LIKE: _columns_like,
        IntentType.WHO_ARE_YOU: _who_are_you,
        IntentType.HELP: _help,
    }
