"""
Divide um arquivo DDL Oracle em statements individuais.
"""
import re
from pathlib import Path

import chardet


class DDLSplitter:
    """Divide DDL Oracle em statements separados por ';'."""

    # Padrões para identificar tipo de statement
    STATEMENT_TYPES = [
        "CREATE UNIQUE INDEX",
        "CREATE GLOBAL TEMPORARY TABLE",
        "CREATE TABLESPACE",
        "CREATE TABLE",
        "CREATE INDEX",
        "CREATE ROLE",
        "CREATE USER",
        "ALTER TABLE",
        "GRANT",
        "COMMENT ON",
    ]

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = ""

    def detect_encoding(self) -> str:
        raw = self.file_path.read_bytes()
        result = chardet.detect(raw)
        return result.get("encoding", "utf-8") or "utf-8"

    def read_file(self) -> str:
        encoding = self.detect_encoding()
        raw = self.file_path.read_text(encoding=encoding, errors="replace")
        # Remover aspas duplas de identificadores Oracle (ex: "OWNER"."TABLE")
        self.content = raw.replace('"', '')
        return self.content

    def split(self) -> list[dict]:
        """
        Divide DDL em statements individuais.
        Retorna lista de dicts: {"type": str, "text": str, "line_number": int}
        """
        if not self.content:
            self.read_file()

        statements = []
        # Dividir por ';' no final de linha (padrão Oracle DDL)
        raw_parts = re.split(r';\s*\n', self.content)

        line_offset = 1
        for part in raw_parts:
            text = part.strip()
            if not text:
                line_offset += part.count('\n') + 1
                continue

            # Remover linhas de comentário puro
            clean = self._strip_leading_comments(text)
            if not clean:
                line_offset += part.count('\n') + 1
                continue

            stmt_type = self._detect_type(clean)
            if stmt_type:
                statements.append({
                    "type": stmt_type,
                    "text": text,
                    "line_number": line_offset,
                })

            line_offset += part.count('\n') + 1

        return statements

    def _strip_leading_comments(self, text: str) -> str:
        """Remove comentários no início do statement."""
        lines = text.split('\n')
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            result.append(line)
        return '\n'.join(result).strip()

    def _detect_type(self, text: str) -> str | None:
        """Detecta o tipo do statement SQL."""
        upper = text.upper().lstrip()
        for st in self.STATEMENT_TYPES:
            if upper.startswith(st):
                return st
        return None
