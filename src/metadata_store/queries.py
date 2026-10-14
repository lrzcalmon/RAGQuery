"""
Queries pré-definidas contra o metadata store.
Cada método retorna dados estruturados para um tipo de pergunta.
"""
from .db_manager import MetadataDB


class MetadataQueries:
    """Consultas de alto nível sobre os metadados DDL."""

    def __init__(self, db: MetadataDB):
        self.db = db

    # ----------------------------------------------------------------
    # TABELAS
    # ----------------------------------------------------------------
    def list_tables(self, owner: str | None = None) -> list[dict]:
        if owner:
            return self.db.query(
                "SELECT owner, table_name, tablespace_name FROM ddl_tables "
                "WHERE UPPER(owner) = UPPER(?) ORDER BY table_name",
                (owner,)
            )
        return self.db.query(
            "SELECT owner, table_name, tablespace_name FROM ddl_tables ORDER BY owner, table_name"
        )

    def count_tables(self, owner: str | None = None) -> int:
        if owner:
            return self.db.query_scalar(
                "SELECT COUNT(*) FROM ddl_tables WHERE UPPER(owner) = UPPER(?)",
                (owner,)
            )
        return self.db.query_scalar("SELECT COUNT(*) FROM ddl_tables")

    def tables_in_tablespace(self, tablespace: str) -> list[dict]:
        return self.db.query(
            "SELECT owner, table_name FROM ddl_tables "
            "WHERE UPPER(tablespace_name) = UPPER(?) ORDER BY table_name",
            (tablespace,)
        )

    def tables_with_prefix(self, prefix: str) -> list[dict]:
        return self.db.query(
            "SELECT owner, table_name, tablespace_name FROM ddl_tables "
            "WHERE UPPER(table_name) LIKE UPPER(?) ORDER BY table_name",
            (f"{prefix}%",)
        )

    def table_details(self, table_name: str, owner: str | None = None) -> dict | None:
        if owner:
            rows = self.db.query(
                "SELECT * FROM ddl_tables WHERE UPPER(table_name) = UPPER(?) "
                "AND UPPER(owner) = UPPER(?)",
                (table_name, owner)
            )
        else:
            rows = self.db.query(
                "SELECT * FROM ddl_tables WHERE UPPER(table_name) = UPPER(?)",
                (table_name,)
            )
        return rows[0] if rows else None

    # ----------------------------------------------------------------
    # COLUNAS
    # ----------------------------------------------------------------
    def columns_of_table(self, table_name: str, owner: str | None = None) -> list[dict]:
        if owner:
            return self.db.query(
                "SELECT column_name, data_type, data_length, nullable, position "
                "FROM ddl_columns WHERE UPPER(table_name) = UPPER(?) "
                "AND UPPER(owner) = UPPER(?) ORDER BY position",
                (table_name, owner)
            )
        return self.db.query(
            "SELECT owner, column_name, data_type, data_length, nullable, position "
            "FROM ddl_columns WHERE UPPER(table_name) = UPPER(?) ORDER BY position",
            (table_name,)
        )

    def tables_with_column(self, column_name: str) -> list[dict]:
        return self.db.query(
            "SELECT DISTINCT c.owner, c.table_name, c.data_type, c.data_length "
            "FROM ddl_columns c "
            "WHERE UPPER(c.column_name) = UPPER(?) "
            "ORDER BY c.owner, c.table_name",
            (column_name,)
        )

    def tables_with_column_like(self, pattern: str) -> list[dict]:
        return self.db.query(
            "SELECT DISTINCT c.owner, c.table_name, c.column_name, c.data_type "
            "FROM ddl_columns c "
            "WHERE UPPER(c.column_name) LIKE UPPER(?) "
            "ORDER BY c.owner, c.table_name",
            (f"%{pattern}%",)
        )

    def columns_not_null(self, table_name: str) -> list[dict]:
        return self.db.query(
            "SELECT column_name, data_type FROM ddl_columns "
            "WHERE UPPER(table_name) = UPPER(?) AND nullable = 'N' ORDER BY position",
            (table_name,)
        )

    def columns_by_type(self, data_type: str) -> list[dict]:
        return self.db.query(
            "SELECT owner, table_name, column_name, data_length "
            "FROM ddl_columns WHERE UPPER(data_type) = UPPER(?) "
            "ORDER BY owner, table_name",
            (data_type,)
        )

    # ----------------------------------------------------------------
    # ÍNDICES
    # ----------------------------------------------------------------
    def indexes_of_table(self, table_name: str) -> list[dict]:
        return self.db.query(
            "SELECT i.index_name, i.uniqueness, i.tablespace_name, i.logging, "
            "GROUP_CONCAT(ic.column_name || ' ' || ic.sort_order, ', ') as columns "
            "FROM ddl_indexes i "
            "LEFT JOIN ddl_index_columns ic ON i.owner = ic.owner AND i.index_name = ic.index_name "
            "WHERE UPPER(i.table_name) = UPPER(?) "
            "GROUP BY i.index_name, i.uniqueness, i.tablespace_name, i.logging "
            "ORDER BY i.index_name",
            (table_name,)
        )

    def count_indexes(self) -> int:
        return self.db.query_scalar("SELECT COUNT(*) FROM ddl_indexes")

    def tables_without_index(self) -> list[dict]:
        return self.db.query(
            "SELECT t.owner, t.table_name FROM ddl_tables t "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM ddl_indexes i "
            "  WHERE UPPER(i.table_name) = UPPER(t.table_name) AND i.owner = t.owner"
            ") ORDER BY t.table_name"
        )

    def indexes_with_column(self, column_name: str) -> list[dict]:
        return self.db.query(
            "SELECT i.index_name, i.table_name, ic.column_name, ic.sort_order "
            "FROM ddl_indexes i "
            "JOIN ddl_index_columns ic ON i.owner = ic.owner AND i.index_name = ic.index_name "
            "WHERE UPPER(ic.column_name) = UPPER(?) "
            "ORDER BY i.table_name, i.index_name",
            (column_name,)
        )

    # ----------------------------------------------------------------
    # CONSTRAINTS
    # ----------------------------------------------------------------
    def constraints_of_table(self, table_name: str) -> list[dict]:
        return self.db.query(
            "SELECT constraint_name, constraint_type, columns, "
            "ref_owner, ref_table, ref_columns "
            "FROM ddl_constraints WHERE UPPER(table_name) = UPPER(?) "
            "ORDER BY constraint_type, constraint_name",
            (table_name,)
        )

    def tables_referencing(self, table_name: str) -> list[dict]:
        return self.db.query(
            "SELECT owner, table_name, constraint_name, columns, ref_columns "
            "FROM ddl_constraints "
            "WHERE UPPER(ref_table) = UPPER(?) AND constraint_type = 'FK' "
            "ORDER BY table_name",
            (table_name,)
        )

    def pk_of_table(self, table_name: str) -> list[dict]:
        return self.db.query(
            "SELECT constraint_name, columns FROM ddl_constraints "
            "WHERE UPPER(table_name) = UPPER(?) AND constraint_type = 'PK'",
            (table_name,)
        )

    def fks_of_table(self, table_name: str) -> list[dict]:
        return self.db.query(
            "SELECT constraint_name, columns, ref_owner, ref_table, ref_columns "
            "FROM ddl_constraints "
            "WHERE UPPER(table_name) = UPPER(?) AND constraint_type = 'FK' "
            "ORDER BY constraint_name",
            (table_name,)
        )

    # ----------------------------------------------------------------
    # GRANTS
    # ----------------------------------------------------------------
    def grants_on_table(self, table_name: str) -> list[dict]:
        return self.db.query(
            "SELECT grantee, privileges FROM ddl_grants "
            "WHERE UPPER(table_name) = UPPER(?) ORDER BY grantee",
            (table_name,)
        )

    def tables_for_grantee(self, grantee: str) -> list[dict]:
        return self.db.query(
            "SELECT owner, table_name, privileges FROM ddl_grants "
            "WHERE UPPER(grantee) = UPPER(?) ORDER BY table_name",
            (grantee,)
        )

    def grants_with_privilege(self, privilege: str) -> list[dict]:
        return self.db.query(
            "SELECT owner, table_name, grantee, privileges FROM ddl_grants "
            "WHERE UPPER(privileges) LIKE UPPER(?) ORDER BY table_name",
            (f"%{privilege}%",)
        )

    # ----------------------------------------------------------------
    # TABLESPACES
    # ----------------------------------------------------------------
    def list_tablespaces(self) -> list[dict]:
        return self.db.query(
            "SELECT tablespace_name, logging, extent_management "
            "FROM ddl_tablespaces ORDER BY tablespace_name"
        )

    def count_tables_per_tablespace(self) -> list[dict]:
        return self.db.query(
            "SELECT tablespace_name, COUNT(*) as table_count "
            "FROM ddl_tables WHERE tablespace_name != '' "
            "GROUP BY tablespace_name ORDER BY table_count DESC"
        )

    # ----------------------------------------------------------------
    # ROLES
    # ----------------------------------------------------------------
    def list_roles(self) -> list[dict]:
        return self.db.query("SELECT role_name FROM ddl_roles ORDER BY role_name")

    def roles_with_prefix(self, prefix: str) -> list[dict]:
        return self.db.query(
            "SELECT role_name FROM ddl_roles WHERE UPPER(role_name) LIKE UPPER(?) "
            "ORDER BY role_name",
            (f"{prefix}%",)
        )

    # ----------------------------------------------------------------
    # COMMENTS
    # ----------------------------------------------------------------
    def comments_of_table(self, table_name: str) -> list[dict]:
        return self.db.query(
            "SELECT column_name, comment_text FROM ddl_comments "
            "WHERE UPPER(table_name) = UPPER(?) ORDER BY column_name",
            (table_name,)
        )

    def columns_with_comments(self) -> list[dict]:
        return self.db.query(
            "SELECT owner, table_name, column_name, comment_text "
            "FROM ddl_comments WHERE column_name IS NOT NULL "
            "ORDER BY owner, table_name, column_name"
        )

    # ----------------------------------------------------------------
    # OWNERS
    # ----------------------------------------------------------------
    def list_owners(self) -> list[dict]:
        return self.db.query(
            "SELECT DISTINCT owner, COUNT(*) as table_count "
            "FROM ddl_tables GROUP BY owner ORDER BY owner"
        )

    # ----------------------------------------------------------------
    # GENÉRICO
    # ----------------------------------------------------------------
    def search_object(self, name: str) -> dict:
        """Busca um nome em tabelas, colunas, índices, constraints."""
        results = {
            "tables": self.db.query(
                "SELECT owner, table_name FROM ddl_tables "
                "WHERE UPPER(table_name) LIKE UPPER(?)",
                (f"%{name}%",)
            ),
            "columns": self.db.query(
                "SELECT owner, table_name, column_name FROM ddl_columns "
                "WHERE UPPER(column_name) LIKE UPPER(?)",
                (f"%{name}%",)
            ),
            "indexes": self.db.query(
                "SELECT owner, index_name, table_name FROM ddl_indexes "
                "WHERE UPPER(index_name) LIKE UPPER(?)",
                (f"%{name}%",)
            ),
        }
        return results
