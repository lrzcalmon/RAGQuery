"""
Formata os resultados das queries em texto legível para o chat.
"""
import json
from .intent_classifier import IntentType


class ResponseBuilder:
    """Formata resultados do SQLGenerator em respostas de chat."""

    def build(self, query_result: dict) -> str:
        """Formata resultado em texto Markdown."""
        data = query_result.get("data")
        query_type = query_result.get("query_type", "")
        params = query_result.get("params", {})

        if data is None:
            return "Não consegui processar esta pergunta. Tente reformulá-la."

        formatter = self._FORMATTERS.get(query_type)
        if formatter:
            return formatter(self, data, params)

        return self._format_generic(data, params)

    # ----------------------------------------------------------------
    # Formatters específicos
    # ----------------------------------------------------------------
    def _fmt_list_tables(self, data, params):
        if not data:
            owner = params.get("owner", "")
            return f"Nenhuma tabela encontrada{' para o owner ' + owner if owner else ''}."

        owner = params.get("owner", data[0].get("owner", ""))
        lines = [f"**Tabelas do owner {owner}** ({len(data)} tabelas):\n"]
        for i, row in enumerate(data, 1):
            ts = row.get("tablespace_name", "")
            ts_info = f" (tablespace: {ts})" if ts else ""
            lines.append(f"{i}. `{row['table_name']}`{ts_info}")
        return "\n".join(lines)

    def _fmt_count_tables(self, data, params):
        owner = params.get("owner", "")
        if owner:
            return f"O owner **{owner}** possui **{data}** tabelas."
        return f"Total de tabelas no banco: **{data}**."

    def _fmt_tables_in_tablespace(self, data, params):
        ts = params.get("tablespace", "")
        if not data:
            return f"Nenhuma tabela encontrada no tablespace {ts}."
        lines = [f"**Tabelas no tablespace {ts}** ({len(data)}):\n"]
        for row in data:
            lines.append(f"- `{row['owner']}.{row['table_name']}`")
        return "\n".join(lines)

    def _fmt_tables_with_prefix(self, data, params):
        prefix = params.get("prefix", "")
        if not data:
            return f"Nenhuma tabela com prefixo '{prefix}'."
        lines = [f"**Tabelas com prefixo {prefix}** ({len(data)}):\n"]
        for row in data:
            lines.append(f"- `{row['owner']}.{row['table_name']}`")
        return "\n".join(lines)

    def _fmt_table_details(self, data, params):
        if not data:
            return f"Tabela `{params.get('table_name', '')}` não encontrada."
        return (
            f"**Tabela: {data['owner']}.{data['table_name']}**\n\n"
            f"- **Tablespace:** {data.get('tablespace_name', 'N/A')}\n"
            f"- **PCTFREE:** {data.get('pctfree', 'N/A')}\n"
            f"- **PCTUSED:** {data.get('pctused', 'N/A')}\n"
            f"- **Logging:** {data.get('logging', 'N/A')}"
        )

    def _fmt_table_ddl(self, data, params):
        if not data or not data.get("ddl"):
            return f"DDL da tabela `{params.get('table_name', '')}` não encontrado."
        return f"**DDL da tabela {params.get('table_name', '')}:**\n\n```sql\n{data['ddl']}\n```"

    def _fmt_columns_of_table(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhuma coluna encontrada para a tabela `{tbl}`."

        lines = [f"**Colunas da tabela {tbl}** ({len(data)} colunas):\n"]
        lines.append("| # | Coluna | Tipo | Tamanho | Nullable |")
        lines.append("|---|--------|------|---------|----------|")
        for row in data:
            pos = row.get("position", 0) + 1
            length = row.get("data_length", "") or ""
            nullable = "NOT NULL" if row.get("nullable") == "N" else "NULL"
            lines.append(
                f"| {pos} | `{row['column_name']}` | {row['data_type']} | "
                f"{length} | {nullable} |"
            )
        return "\n".join(lines)

    def _fmt_tables_with_column(self, data, params):
        col = params.get("column_name", "")
        if not data:
            return f"Nenhuma tabela possui a coluna `{col}`."
        lines = [f"**Tabelas que possuem a coluna `{col}`** ({len(data)}):\n"]
        lines.append("| Tabela | Tipo | Tamanho |")
        lines.append("|--------|------|---------|")
        for row in data:
            length = row.get("data_length", "") or ""
            lines.append(
                f"| `{row['owner']}.{row['table_name']}` | "
                f"{row['data_type']} | {length} |"
            )
        return "\n".join(lines)

    def _fmt_columns_not_null(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhuma coluna NOT NULL na tabela `{tbl}`."
        lines = [f"**Colunas NOT NULL da tabela {tbl}** ({len(data)}):\n"]
        for row in data:
            lines.append(f"- `{row['column_name']}` ({row['data_type']})")
        return "\n".join(lines)

    def _fmt_columns_by_type(self, data, params):
        dt = params.get("data_type", "")
        if not data:
            return f"Nenhuma coluna do tipo `{dt}`."
        lines = [f"**Colunas do tipo {dt}** ({len(data)}):\n"]
        for row in data:
            lines.append(f"- `{row['owner']}.{row['table_name']}.{row['column_name']}`")
        return "\n".join(lines)

    def _fmt_indexes_of_table(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhum índice encontrado para a tabela `{tbl}`."
        lines = [f"**Índices da tabela {tbl}** ({len(data)}):\n"]
        lines.append("| Índice | Tipo | Colunas | Tablespace |")
        lines.append("|--------|------|---------|------------|")
        for row in data:
            cols = row.get("columns", "") or ""
            lines.append(
                f"| `{row['index_name']}` | {row['uniqueness']} | "
                f"{cols} | {row.get('tablespace_name', '')} |"
            )
        return "\n".join(lines)

    def _fmt_count_indexes(self, data, params):
        return f"Total de índices no banco: **{data}**."

    def _fmt_tables_without_index(self, data, params):
        if not data:
            return "Todas as tabelas possuem pelo menos um índice."
        lines = [f"**Tabelas sem índice** ({len(data)}):\n"]
        for row in data:
            lines.append(f"- `{row['owner']}.{row['table_name']}`")
        return "\n".join(lines)

    def _fmt_indexes_with_column(self, data, params):
        col = params.get("column_name", "")
        if not data:
            return f"Nenhum índice utiliza a coluna `{col}`."
        lines = [f"**Índices que incluem a coluna `{col}`** ({len(data)}):\n"]
        for row in data:
            lines.append(
                f"- `{row['index_name']}` na tabela `{row['table_name']}` "
                f"({row['sort_order']})"
            )
        return "\n".join(lines)

    def _fmt_constraints_of_table(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhuma constraint na tabela `{tbl}`."
        lines = [f"**Constraints da tabela {tbl}** ({len(data)}):\n"]
        for row in data:
            cols = row.get("columns", "")
            ref = ""
            if row.get("ref_table"):
                ref = f" → `{row.get('ref_owner', '')}.{row['ref_table']}`({row.get('ref_columns', '')})"
            lines.append(
                f"- **{row['constraint_type']}** `{row['constraint_name']}` "
                f"({cols}){ref}"
            )
        return "\n".join(lines)

    def _fmt_tables_referencing(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhuma tabela referencia `{tbl}` via FK."
        lines = [f"**Tabelas que referenciam `{tbl}`** ({len(data)}):\n"]
        for row in data:
            lines.append(
                f"- `{row['owner']}.{row['table_name']}` via `{row['constraint_name']}`"
            )
        return "\n".join(lines)

    def _fmt_pk_of_table(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhuma PK definida para a tabela `{tbl}`."
        pk = data[0]
        return (
            f"**Primary Key da tabela {tbl}:**\n\n"
            f"- Nome: `{pk['constraint_name']}`\n"
            f"- Colunas: {pk['columns']}"
        )

    def _fmt_fks_of_table(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhuma FK definida para a tabela `{tbl}`."
        lines = [f"**Foreign Keys da tabela {tbl}** ({len(data)}):\n"]
        for row in data:
            lines.append(
                f"- `{row['constraint_name']}` ({row['columns']}) → "
                f"`{row.get('ref_owner', '')}.{row['ref_table']}`({row.get('ref_columns', '')})"
            )
        return "\n".join(lines)

    def _fmt_grants_on_table(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhum grant encontrado para a tabela `{tbl}`."
        lines = [f"**Grants na tabela {tbl}** ({len(data)}):\n"]
        lines.append("| Grantee | Privilégios |")
        lines.append("|---------|-------------|")
        for row in data:
            lines.append(f"| `{row['grantee']}` | {row['privileges']} |")
        return "\n".join(lines)

    def _fmt_tables_for_grantee(self, data, params):
        grantee = params.get("grantee", "")
        if not data:
            return f"Nenhuma tabela com grants para `{grantee}`."
        lines = [f"**Tabelas acessíveis por `{grantee}`** ({len(data)}):\n"]
        lines.append("| Tabela | Privilégios |")
        lines.append("|--------|-------------|")
        for row in data:
            lines.append(f"| `{row['owner']}.{row['table_name']}` | {row['privileges']} |")
        return "\n".join(lines)

    def _fmt_grants_with_privilege(self, data, params):
        priv = params.get("privilege", "")
        if not data:
            return f"Nenhum grant com privilégio `{priv}`."
        lines = [f"**Grants com privilégio `{priv}`** ({len(data)}):\n"]
        for row in data:
            lines.append(
                f"- `{row['grantee']}` → `{row['owner']}.{row['table_name']}` ({row['privileges']})"
            )
        return "\n".join(lines)

    def _fmt_list_tablespaces(self, data, params):
        if not data:
            return "Nenhum tablespace encontrado."
        lines = [f"**Tablespaces** ({len(data)}):\n"]
        for row in data:
            lines.append(
                f"- `{row['tablespace_name']}` (logging: {row.get('logging', 'N/A')})"
            )
        return "\n".join(lines)

    def _fmt_count_tables_per_tablespace(self, data, params):
        if not data:
            return "Nenhum dado de tablespace encontrado."
        lines = ["**Tabelas por tablespace:**\n"]
        lines.append("| Tablespace | Qtd Tabelas |")
        lines.append("|------------|-------------|")
        for row in data:
            lines.append(f"| `{row['tablespace_name']}` | {row['table_count']} |")
        return "\n".join(lines)

    def _fmt_list_roles(self, data, params):
        if not data:
            return "Nenhuma role encontrada."
        lines = [f"**Roles** ({len(data)}):\n"]
        for row in data:
            lines.append(f"- `{row['role_name']}`")
        return "\n".join(lines)

    def _fmt_roles_with_prefix(self, data, params):
        prefix = params.get("prefix", "")
        if not data:
            return f"Nenhuma role com prefixo `{prefix}`."
        lines = [f"**Roles com prefixo `{prefix}`** ({len(data)}):\n"]
        for row in data:
            lines.append(f"- `{row['role_name']}`")
        return "\n".join(lines)

    def _fmt_comments_of_table(self, data, params):
        tbl = params.get("table_name", "")
        if not data:
            return f"Nenhum comentário na tabela `{tbl}`."
        lines = [f"**Comentários da tabela {tbl}** ({len(data)}):\n"]
        for row in data:
            col = row.get("column_name") or "(tabela)"
            lines.append(f"- **{col}**: {row['comment_text']}")
        return "\n".join(lines)

    def _fmt_columns_with_comments(self, data, params):
        if not data:
            return "Nenhuma coluna com comentário."
        lines = [f"**Colunas com comentários** ({len(data)}):\n"]
        for row in data:
            lines.append(
                f"- `{row['owner']}.{row['table_name']}.{row['column_name']}`: "
                f"{row['comment_text']}"
            )
        return "\n".join(lines)

    def _fmt_list_owners(self, data, params):
        if not data:
            return "Nenhum owner encontrado."
        lines = ["**Owners no banco:**\n"]
        for row in data:
            lines.append(f"- `{row['owner']}` ({row['table_count']} tabelas)")
        return "\n".join(lines)

    def _fmt_search_object(self, data, params):
        if not data:
            return "Nenhum objeto encontrado."

        lines = ["**Resultados da busca:**\n"]
        if data.get("tables"):
            lines.append(f"**Tabelas** ({len(data['tables'])}):")
            for r in data["tables"]:
                lines.append(f"  - `{r['owner']}.{r['table_name']}`")
        if data.get("columns"):
            lines.append(f"\n**Colunas** ({len(data['columns'])}):")
            for r in data["columns"][:20]:
                lines.append(f"  - `{r['owner']}.{r['table_name']}.{r['column_name']}`")
            if len(data["columns"]) > 20:
                lines.append(f"  ... e mais {len(data['columns']) - 20}")
        if data.get("indexes"):
            lines.append(f"\n**Índices** ({len(data['indexes'])}):")
            for r in data["indexes"]:
                lines.append(f"  - `{r['index_name']}` (tabela: `{r['table_name']}`)")
        return "\n".join(lines)

    def _fmt_columns_like(self, data, params):
        pattern = params.get("pattern", "")
        if not data:
            return f"Nenhuma coluna encontrada com `{pattern}` no nome."
        lines = [f"**Colunas com `{pattern}` no nome** ({len(data)}):\n"]
        lines.append("| Tabela | Coluna | Tipo |")
        lines.append("|--------|--------|------|")
        for row in data[:100]:
            lines.append(
                f"| `{row['owner']}.{row['table_name']}` | "
                f"`{row['column_name']}` | {row['data_type']} |"
            )
        if len(data) > 100:
            lines.append(f"\n... e mais {len(data) - 100} colunas.")
        return "\n".join(lines)

    def _fmt_who_are_you(self, data, params):
        return (
            "Eu sou o **RAGQuery**, um assistente especializado em consultas sobre "
            "a estrutura de bancos de dados Oracle.\n\n"
            "Fui projetado para responder perguntas sobre:\n"
            "- **Tabelas** — listar, contar, buscar por prefixo ou owner\n"
            "- **Colunas** — de uma tabela, por tipo, por padrão de nome\n"
            "- **Índices** — de uma tabela, tabelas sem índice\n"
            "- **Constraints** — PKs, FKs, referências entre tabelas\n"
            "- **Grants e Roles** — permissões, quem acessa o quê\n"
            "- **Tablespaces** — listar, contar tabelas por tablespace\n"
            "- **Comentários** — documentação das colunas\n\n"
            "Utilizo os DDLs que foram indexados no meu banco de metadados. "
            "Quando disponível, uso o modelo **Phi-3-mini** para entender "
            "perguntas mais complexas."
        )

    def _fmt_help(self, data, params):
        return (
            "**Como posso te ajudar:**\n\n"
            "Faça perguntas em linguagem natural sobre a estrutura do banco Oracle. "
            "Alguns exemplos:\n\n"
            "| Tipo | Exemplo |\n"
            "|------|---------|\n"
            "| Tabelas | _Quais as tabelas do owner LOJA?_ |\n"
            "| Colunas | _Quais as colunas da tabela VENDA_PEDIDO?_ |\n"
            "| Busca | _Quais colunas possuem VENDA no nome?_ |\n"
            "| Índices | _Quais os índices da tabela VENDA_CLIENTE?_ |\n"
            "| Sem índice | _Tabelas sem índice_ |\n"
            "| PKs/FKs | _FK da tabela VENDA_PEDIDO_ |\n"
            "| Grants | _Grants na tabela AUD_INCONSISTENCIA_ |\n"
            "| Referências | _Quais tabelas referenciam VENDA_LOJA?_ |\n"
            "| Tablespaces | _Quais tablespaces existem?_ |\n"
            "| Roles | _Quais roles existem?_ |\n"
            "| Sobre mim | _Quem é você?_ |\n\n"
            "Você pode perguntar em **português** ou **inglês**."
        )

    def _format_generic(self, data, params):
        """Formatação genérica para resultados não mapeados."""
        if isinstance(data, list):
            if not data:
                return "Nenhum resultado encontrado."
            if len(data) == 1:
                return self._dict_to_text(data[0])
            lines = [f"**{len(data)} resultados:**\n"]
            for row in data[:50]:
                lines.append(f"- {self._dict_to_inline(row)}")
            if len(data) > 50:
                lines.append(f"\n... e mais {len(data) - 50} resultados.")
            return "\n".join(lines)
        if isinstance(data, dict):
            return self._dict_to_text(data)
        return str(data)

    def _dict_to_text(self, d: dict) -> str:
        lines = []
        for k, v in d.items():
            lines.append(f"- **{k}:** {v}")
        return "\n".join(lines)

    def _dict_to_inline(self, d: dict) -> str:
        parts = [f"{k}={v}" for k, v in d.items() if v]
        return ", ".join(parts)

    # Mapa de formatters
    _FORMATTERS = {
        IntentType.LIST_TABLES.value: _fmt_list_tables,
        IntentType.COUNT_TABLES.value: _fmt_count_tables,
        IntentType.TABLES_IN_TABLESPACE.value: _fmt_tables_in_tablespace,
        IntentType.TABLES_WITH_PREFIX.value: _fmt_tables_with_prefix,
        IntentType.TABLE_DETAILS.value: _fmt_table_details,
        IntentType.TABLE_DDL.value: _fmt_table_ddl,
        IntentType.COLUMNS_OF_TABLE.value: _fmt_columns_of_table,
        IntentType.TABLES_WITH_COLUMN.value: _fmt_tables_with_column,
        IntentType.COLUMNS_NOT_NULL.value: _fmt_columns_not_null,
        IntentType.COLUMNS_BY_TYPE.value: _fmt_columns_by_type,
        IntentType.INDEXES_OF_TABLE.value: _fmt_indexes_of_table,
        IntentType.COUNT_INDEXES.value: _fmt_count_indexes,
        IntentType.TABLES_WITHOUT_INDEX.value: _fmt_tables_without_index,
        IntentType.INDEXES_WITH_COLUMN.value: _fmt_indexes_with_column,
        IntentType.CONSTRAINTS_OF_TABLE.value: _fmt_constraints_of_table,
        IntentType.TABLES_REFERENCING.value: _fmt_tables_referencing,
        IntentType.PK_OF_TABLE.value: _fmt_pk_of_table,
        IntentType.FKS_OF_TABLE.value: _fmt_fks_of_table,
        IntentType.GRANTS_ON_TABLE.value: _fmt_grants_on_table,
        IntentType.TABLES_FOR_GRANTEE.value: _fmt_tables_for_grantee,
        IntentType.GRANTS_WITH_PRIVILEGE.value: _fmt_grants_with_privilege,
        IntentType.LIST_TABLESPACES.value: _fmt_list_tablespaces,
        IntentType.COUNT_TABLES_PER_TABLESPACE.value: _fmt_count_tables_per_tablespace,
        IntentType.LIST_ROLES.value: _fmt_list_roles,
        IntentType.ROLES_WITH_PREFIX.value: _fmt_roles_with_prefix,
        IntentType.COMMENTS_OF_TABLE.value: _fmt_comments_of_table,
        IntentType.COLUMNS_WITH_COMMENTS.value: _fmt_columns_with_comments,
        IntentType.LIST_OWNERS.value: _fmt_list_owners,
        IntentType.SEARCH_OBJECT.value: _fmt_search_object,
        IntentType.COLUMNS_LIKE.value: _fmt_columns_like,
        IntentType.WHO_ARE_YOU.value: _fmt_who_are_you,
        IntentType.HELP.value: _fmt_help,
    }
