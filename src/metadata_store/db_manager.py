"""
Gerenciador do banco SQLite de metadados DDL.
"""
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .schema import SCHEMA_SQL
from ..ddl_parser.models import ParseResult


class MetadataDB:
    """CRUD para o banco de metadados SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None

    def connect(self):
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_schema(self):
        """Cria todas as tabelas e índices."""
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def recreate(self):
        """Apaga todos os dados e recria schema."""
        tables = [
            "ddl_tables", "ddl_columns", "ddl_indexes", "ddl_index_columns",
            "ddl_constraints", "ddl_grants", "ddl_tablespaces", "ddl_roles",
            "ddl_comments", "ddl_ingestion_log",
        ]
        for t in tables:
            self.conn.execute(f"DROP TABLE IF EXISTS {t}")
        self.conn.commit()
        self.create_schema()

    def file_hash(self, file_path: Path) -> str:
        """Calcula SHA256 do arquivo."""
        h = hashlib.sha256()
        h.update(file_path.read_bytes())
        return h.hexdigest()

    def is_file_ingested(self, file_path: Path) -> bool:
        """Verifica se arquivo já foi ingerido (mesmo hash)."""
        cur = self.conn.execute(
            "SELECT file_hash FROM ddl_ingestion_log WHERE file_path = ?",
            (str(file_path),)
        )
        row = cur.fetchone()
        if not row:
            return False
        return row["file_hash"] == self.file_hash(file_path)

    def insert_parse_result(self, result: ParseResult, file_path: Path):
        """Insere todos os objetos parseados no banco."""
        cur = self.conn.cursor()

        # Coletar owner+table_name para limpar dados antigos (dedup)
        table_keys = {(t.owner, t.table_name) for t in result.tables}
        for owner, tname in table_keys:
            cur.execute("DELETE FROM ddl_columns WHERE owner=? AND table_name=?", (owner, tname))
            cur.execute("DELETE FROM ddl_grants WHERE owner=? AND table_name=?", (owner, tname))
            cur.execute("DELETE FROM ddl_constraints WHERE owner=? AND table_name=?", (owner, tname))
            cur.execute("DELETE FROM ddl_comments WHERE owner=? AND table_name=?", (owner, tname))

        # Limpar index_columns para índices que serão reinseridos
        idx_keys = {(idx.owner, idx.index_name) for idx in result.indexes}
        for owner, iname in idx_keys:
            cur.execute("DELETE FROM ddl_index_columns WHERE owner=? AND index_name=?", (owner, iname))

        # Tabelas
        for t in result.tables:
            cur.execute(
                "INSERT OR REPLACE INTO ddl_tables "
                "(owner, table_name, tablespace_name, pctfree, pctused, logging, full_ddl) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (t.owner, t.table_name, t.tablespace_name, t.pctfree,
                 t.pctused, t.logging, t.full_ddl),
            )

        # Colunas
        for c in result.columns:
            cur.execute(
                "INSERT INTO ddl_columns "
                "(owner, table_name, column_name, data_type, data_length, nullable, position) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (c.owner, c.table_name, c.column_name, c.data_type,
                 c.data_length, c.nullable, c.position),
            )

        # Índices
        for idx in result.indexes:
            cur.execute(
                "INSERT OR REPLACE INTO ddl_indexes "
                "(owner, index_name, table_name, tablespace_name, uniqueness, logging) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (idx.owner, idx.index_name, idx.table_name,
                 idx.tablespace_name, idx.uniqueness, idx.logging),
            )

        # Colunas de índice
        for ic in result.index_columns:
            cur.execute(
                "INSERT INTO ddl_index_columns "
                "(owner, index_name, column_name, position, sort_order) "
                "VALUES (?, ?, ?, ?, ?)",
                (ic.owner, ic.index_name, ic.column_name, ic.position, ic.sort_order),
            )

        # Constraints
        for con in result.constraints:
            cur.execute(
                "INSERT INTO ddl_constraints "
                "(owner, constraint_name, table_name, constraint_type, columns, "
                "ref_owner, ref_table, ref_columns) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (con.owner, con.constraint_name, con.table_name,
                 con.constraint_type, json.dumps(con.columns),
                 con.ref_owner, con.ref_table, json.dumps(con.ref_columns)),
            )

        # Grants
        for g in result.grants:
            cur.execute(
                "INSERT INTO ddl_grants (owner, table_name, grantee, privileges) "
                "VALUES (?, ?, ?, ?)",
                (g.owner, g.table_name, g.grantee, g.privileges),
            )

        # Tablespaces
        for ts in result.tablespaces:
            cur.execute(
                "INSERT OR IGNORE INTO ddl_tablespaces "
                "(tablespace_name, logging, extent_management) "
                "VALUES (?, ?, ?)",
                (ts.tablespace_name, ts.logging, ts.extent_management),
            )

        # Roles
        for r in result.roles:
            cur.execute(
                "INSERT OR IGNORE INTO ddl_roles (role_name) VALUES (?)",
                (r.role_name,),
            )

        # Comentários
        for cm in result.comments:
            cur.execute(
                "INSERT INTO ddl_comments (owner, table_name, column_name, comment_text) "
                "VALUES (?, ?, ?, ?)",
                (cm.owner, cm.table_name, cm.column_name, cm.comment_text),
            )

        # Log de ingestão
        cur.execute(
            "INSERT OR REPLACE INTO ddl_ingestion_log "
            "(file_path, file_hash, file_size, ingested_at, objects_count, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (str(file_path), self.file_hash(file_path),
             file_path.stat().st_size, datetime.now().isoformat(),
             result.total_objects, "OK"),
        )

        self.conn.commit()

    def get_stats(self) -> dict:
        """Retorna estatísticas do banco."""
        stats = {}
        for table in ["ddl_tables", "ddl_columns", "ddl_indexes",
                       "ddl_constraints", "ddl_grants", "ddl_tablespaces",
                       "ddl_roles", "ddl_comments"]:
            cur = self.conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            stats[table] = cur.fetchone()["cnt"]
        return stats

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        """Executa query e retorna lista de dicts."""
        cur = self.conn.execute(sql, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def query_scalar(self, sql: str, params: tuple = ()):
        """Executa query e retorna valor escalar."""
        cur = self.conn.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None
