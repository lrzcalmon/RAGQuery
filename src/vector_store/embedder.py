"""
Gera embeddings para objetos DDL parseados.
Cada tabela vira um documento textual descritivo para embedding.
"""
from pathlib import Path

from ..config import settings
from ..metadata_store.db_manager import MetadataDB


class DDLEmbedder:
    """Converte metadados DDL em documentos textuais e gera embeddings."""

    def __init__(self, db: MetadataDB):
        self.db = db
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                settings.embedding.model_name,
                device=settings.embedding.device,
            )
        return self._model

    def build_documents(self) -> list[dict]:
        """
        Constrói documentos textuais a partir dos metadados SQLite.
        Cada tabela gera um documento com: owner, nome, colunas, índices, constraints, grants.
        """
        documents = []

        tables = self.db.query(
            "SELECT owner, table_name, tablespace_name FROM ddl_tables ORDER BY owner, table_name"
        )

        for tbl in tables:
            owner = tbl["owner"]
            table_name = tbl["table_name"]

            # Colunas
            columns = self.db.query(
                "SELECT column_name, data_type, data_length, nullable "
                "FROM ddl_columns WHERE owner = ? AND table_name = ? ORDER BY position",
                (owner, table_name)
            )
            col_lines = []
            for c in columns:
                size = f"({c['data_length']})" if c['data_length'] else ""
                nn = " NOT NULL" if c['nullable'] == 'N' else ""
                col_lines.append(f"  {c['column_name']} {c['data_type']}{size}{nn}")

            # Índices
            indexes = self.db.query(
                "SELECT i.index_name, i.uniqueness, "
                "GROUP_CONCAT(ic.column_name, ', ') as cols "
                "FROM ddl_indexes i "
                "LEFT JOIN ddl_index_columns ic ON i.owner = ic.owner AND i.index_name = ic.index_name "
                "WHERE i.table_name = ? AND i.owner = ? "
                "GROUP BY i.index_name, i.uniqueness",
                (table_name, owner)
            )
            idx_lines = []
            for idx in indexes:
                idx_lines.append(f"  {idx['index_name']} ({idx['uniqueness']}): {idx['cols'] or ''}")

            # Constraints
            constraints = self.db.query(
                "SELECT constraint_name, constraint_type, columns, ref_table "
                "FROM ddl_constraints WHERE owner = ? AND table_name = ?",
                (owner, table_name)
            )
            con_lines = []
            for con in constraints:
                ref = f" -> {con['ref_table']}" if con['ref_table'] else ""
                con_lines.append(f"  {con['constraint_type']} {con['constraint_name']}: {con['columns']}{ref}")

            # Grants
            grants = self.db.query(
                "SELECT grantee, privileges FROM ddl_grants WHERE owner = ? AND table_name = ?",
                (owner, table_name)
            )
            grant_lines = [f"  {g['grantee']}: {g['privileges']}" for g in grants]

            # Comentários
            comments = self.db.query(
                "SELECT column_name, comment_text FROM ddl_comments "
                "WHERE owner = ? AND table_name = ?",
                (owner, table_name)
            )
            comment_lines = []
            for cm in comments:
                target = cm['column_name'] or 'TABLE'
                comment_lines.append(f"  {target}: {cm['comment_text']}")

            # Montar documento
            text = f"Tabela: {owner}.{table_name}\n"
            text += f"Tablespace: {tbl.get('tablespace_name', '')}\n"

            if col_lines:
                text += "Colunas:\n" + "\n".join(col_lines) + "\n"
            if idx_lines:
                text += "Indices:\n" + "\n".join(idx_lines) + "\n"
            if con_lines:
                text += "Constraints:\n" + "\n".join(con_lines) + "\n"
            if grant_lines:
                text += "Grants:\n" + "\n".join(grant_lines) + "\n"
            if comment_lines:
                text += "Comentarios:\n" + "\n".join(comment_lines) + "\n"

            documents.append({
                "id": f"{owner}.{table_name}",
                "text": text,
                "metadata": {
                    "owner": owner,
                    "table_name": table_name,
                    "tablespace": tbl.get("tablespace_name", ""),
                    "num_columns": len(columns),
                    "num_indexes": len(indexes),
                    "type": "table",
                },
            })

        return documents

    def generate_embeddings(self, documents: list[dict]) -> list[dict]:
        """Adiciona campo 'embedding' a cada documento."""
        model = self._load_model()
        texts = [d["text"] for d in documents]

        batch_size = settings.embedding.batch_size
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embs = model.encode(batch, show_progress_bar=False)
            all_embeddings.extend(embs)

        for doc, emb in zip(documents, all_embeddings):
            doc["embedding"] = emb.tolist()

        return documents
