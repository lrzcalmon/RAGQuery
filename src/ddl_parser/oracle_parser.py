"""
Parser de DDL Oracle.
Extrai tabelas, colunas, índices, constraints, grants, comments, roles, tablespaces.
"""
import re
import json
from pathlib import Path

from .models import (
    Table, Column, Index, IndexColumn, Constraint, Grant,
    Tablespace, Role, Comment, ParseResult,
)
from .ddl_splitter import DDLSplitter


class OracleDDLParser:
    """Parser para DDL gerado pelo Oracle SQL Developer Data Modeler."""

    # --- Regex patterns ---
    RE_OWNER_TABLE = re.compile(
        r'CREATE\s+(?:GLOBAL\s+TEMPORARY\s+)?TABLE\s+(\w+)\.(\w+)', re.IGNORECASE
    )
    RE_TABLE_ONLY = re.compile(
        r'CREATE\s+(?:GLOBAL\s+TEMPORARY\s+)?TABLE\s+(\w+)', re.IGNORECASE
    )
    RE_COLUMN = re.compile(
        r'^\s+(\w+)\s+([\w$#]+(?:\s*\([^)]*\))?(?:\s+BYTE)?)'
        r'(?:\s+(NOT\s+NULL))?',
        re.IGNORECASE | re.MULTILINE
    )
    RE_TABLESPACE = re.compile(
        r'TABLESPACE\s+(\w+)', re.IGNORECASE
    )
    RE_PCTFREE = re.compile(r'PCTFREE\s+(\d+)', re.IGNORECASE)
    RE_PCTUSED = re.compile(r'PCTUSED\s+(\d+)', re.IGNORECASE)
    RE_LOGGING = re.compile(r'\b(LOGGING|NOLOGGING)\b', re.IGNORECASE)

    RE_INDEX = re.compile(
        r'CREATE\s+(?:(UNIQUE)\s+)?INDEX\s+(\w+)\.(\w+)\s+ON\s+(\w+)\.(\w+)',
        re.IGNORECASE
    )
    RE_INDEX_COLS = re.compile(
        r'\(\s*\n?([\s\S]*?)\n?\s*\)', re.IGNORECASE
    )

    RE_ALTER_PK = re.compile(
        r'ADD\s+CONSTRAINT\s+(\w+)\s+PRIMARY\s+KEY\s*\(\s*([\s\S]*?)\s*\)',
        re.IGNORECASE
    )
    RE_ALTER_FK = re.compile(
        r'ADD\s+(?:CONSTRAINT\s+(\w+)\s+)?FOREIGN\s+KEY\s*\(\s*([\s\S]*?)\s*\)'
        r'\s*REFERENCES\s+(\w+)\.(\w+)\s*\(\s*([\s\S]*?)\s*\)',
        re.IGNORECASE
    )
    RE_ALTER_TABLE = re.compile(
        r'ALTER\s+TABLE\s+(\w+)\.(\w+)', re.IGNORECASE
    )

    RE_GRANT = re.compile(
        r'GRANT\s+([\w\s,]+?)\s+ON\s+(\w+)\.(\w+)\s+TO\s+(\w+)',
        re.IGNORECASE
    )

    RE_COMMENT_COL = re.compile(
        r"COMMENT\s+ON\s+COLUMN\s+(\w+)\.(\w+)\.(\w+)\s+IS\s+'((?:[^']|'')*)'",
        re.IGNORECASE
    )
    RE_COMMENT_TABLE = re.compile(
        r"COMMENT\s+ON\s+TABLE\s+(\w+)\.(\w+)\s+IS\s+'((?:[^']|'')*)'",
        re.IGNORECASE
    )

    RE_CREATE_TABLESPACE = re.compile(
        r'CREATE\s+TABLESPACE\s+(\w+)', re.IGNORECASE
    )
    RE_EXTENT_MGMT = re.compile(
        r'EXTENT\s+MANAGEMENT\s+([\w\s]+?)(?:\n|$)', re.IGNORECASE
    )

    RE_CREATE_ROLE = re.compile(
        r'CREATE\s+ROLE\s+([\w$]+)', re.IGNORECASE
    )

    # Palavras que não são nomes de coluna (aparecem dentro do bloco de colunas)
    COLUMN_BLACKLIST = {
        'PCTFREE', 'PCTUSED', 'TABLESPACE', 'LOGGING', 'NOLOGGING',
        'STORAGE', 'INITIAL', 'NEXT', 'PCTINCREASE', 'MINEXTENTS',
        'MAXEXTENTS', 'FREELISTS', 'FREELIST', 'BUFFER_POOL',
        'CONSTRAINT', 'NOT', 'NULL', 'DEFAULT', 'PRIMARY', 'KEY',
        'UNIQUE', 'CHECK', 'FOREIGN', 'REFERENCES', 'ON', 'DELETE',
        'CASCADE', 'SET', 'GROUPS', 'ENABLE', 'DISABLE', 'NOVALIDATE',
        'VALIDATE', 'DEFERRABLE', 'DEFERRED', 'IMMEDIATE', 'ADD',
        'SUPPLEMENTAL', 'LOG', 'DATA', 'ALL', 'COLUMNS', 'USING',
        'INDEX', 'ALTER', 'TABLE', 'GRANT', 'CREATE', 'COMMENT',
        'FLASHBACK',
    }

    # Tipos de dados Oracle válidos
    VALID_DATA_TYPES = {
        'NUMBER', 'VARCHAR2', 'CHAR', 'DATE', 'TIMESTAMP', 'CLOB', 'BLOB',
        'NVARCHAR2', 'NCHAR', 'NCLOB', 'RAW', 'LONG', 'FLOAT', 'INTEGER',
        'SMALLINT', 'REAL', 'DOUBLE', 'BINARY_FLOAT', 'BINARY_DOUBLE',
        'XMLTYPE', 'SDO_GEOMETRY', 'ROWID', 'UROWID', 'BFILE',
        'INTERVAL', 'BOOLEAN',
    }

    def __init__(self, default_owner: str = "UNKNOWN"):
        self.default_owner = default_owner

    def parse_file(self, file_path: Path) -> ParseResult:
        """Parseia um arquivo DDL completo e retorna ParseResult."""
        splitter = DDLSplitter(file_path)
        splitter.read_file()
        statements = splitter.split()

        result = ParseResult()

        for stmt in statements:
            stype = stmt["type"]
            text = stmt["text"]

            if stype in ("CREATE TABLE", "CREATE GLOBAL TEMPORARY TABLE"):
                self._parse_create_table(text, result)
            elif stype in ("CREATE INDEX", "CREATE UNIQUE INDEX"):
                self._parse_create_index(text, result)
            elif stype == "ALTER TABLE":
                self._parse_alter_table(text, result)
            elif stype == "GRANT":
                self._parse_grant(text, result)
            elif stype == "COMMENT ON":
                self._parse_comment(text, result)
            elif stype == "CREATE TABLESPACE":
                self._parse_create_tablespace(text, result)
            elif stype == "CREATE ROLE":
                self._parse_create_role(text, result)

        return result

    # ----------------------------------------------------------------
    # CREATE TABLE
    # ----------------------------------------------------------------
    def _parse_create_table(self, text: str, result: ParseResult):
        m = self.RE_OWNER_TABLE.search(text)
        if m:
            owner, table_name = m.group(1).upper(), m.group(2).upper()
        else:
            m2 = self.RE_TABLE_ONLY.search(text)
            if not m2:
                return
            owner = self.default_owner
            table_name = m2.group(1).upper()

        tablespace = ""
        m_ts = self.RE_TABLESPACE.search(text)
        if m_ts:
            tablespace = m_ts.group(1).upper()

        pctfree = None
        m_pf = self.RE_PCTFREE.search(text)
        if m_pf:
            pctfree = int(m_pf.group(1))

        pctused = None
        m_pu = self.RE_PCTUSED.search(text)
        if m_pu:
            pctused = int(m_pu.group(1))

        logging = ""
        m_log = self.RE_LOGGING.search(text)
        if m_log:
            logging = m_log.group(1).upper()

        table = Table(
            owner=owner,
            table_name=table_name,
            tablespace_name=tablespace,
            pctfree=pctfree,
            pctused=pctused,
            logging=logging,
            full_ddl=text,
        )

        # Extrair colunas do bloco entre parênteses após o nome da tabela
        columns = self._extract_columns(text, owner, table_name)
        table.columns = columns
        result.columns.extend(columns)
        result.tables.append(table)

    def _extract_columns(self, ddl: str, owner: str, table_name: str) -> list[Column]:
        """Extrai colunas do CREATE TABLE."""
        columns = []

        # Encontrar o bloco de definição de colunas: primeiro '(' após CREATE TABLE ... nome
        # Aceita ambos formatos: ( na mesma linha da 1ª coluna ou em linha separada
        paren_match = re.search(
            r'CREATE\s+(?:GLOBAL\s+TEMPORARY\s+)?TABLE\s+\S+\s*\(\s*([\s\S]*?)\n\s*\)',
            ddl, re.IGNORECASE
        )
        if not paren_match:
            return columns

        block = paren_match.group(1)
        lines = block.split('\n')

        position = 0
        for line in lines:
            stripped = line.strip().rstrip(',')
            if not stripped:
                continue

            # Tentar parsear como definição de coluna
            col = self._parse_column_line(stripped, owner, table_name, position)
            if col:
                columns.append(col)
                position += 1

        return columns

    def _parse_column_line(self, line: str, owner: str, table_name: str,
                           position: int) -> Column | None:
        """Parseia uma linha como definição de coluna."""
        # Formato típico: COL_NAME  DATA_TYPE(len)  [NOT NULL]  [CONSTRAINT ...]
        # Ignorar linhas que começam com keywords
        first_word = line.split()[0].upper() if line.split() else ""
        if first_word in self.COLUMN_BLACKLIST:
            return None

        # Match: NOME  TIPO[(tamanho)] [BYTE] [NOT NULL]
        m = re.match(
            r'^(\w+)\s+'
            r'(NUMBER|VARCHAR2|CHAR|DATE|TIMESTAMP|CLOB|BLOB|NVARCHAR2|NCHAR|'
            r'NCLOB|RAW|LONG|FLOAT|INTEGER|SMALLINT|REAL|XMLTYPE|ROWID|BFILE)'
            r'(?:\s*\(([^)]*)\))?'
            r'(?:\s+BYTE)?'
            r'(.*)',
            line, re.IGNORECASE
        )
        if not m:
            return None

        col_name = m.group(1).upper()
        data_type = m.group(2).upper()
        size_str = m.group(3)
        rest = m.group(4) or ""

        # Verificar se não é uma keyword
        if col_name in self.COLUMN_BLACKLIST:
            return None

        data_length = None
        if size_str:
            # Pegar primeiro número do tamanho: NUMBER(10,2) → 10
            nums = re.findall(r'\d+', size_str)
            if nums:
                data_length = int(nums[0])

        nullable = "N" if "NOT NULL" in rest.upper() else "Y"

        # Verificar constraint inline (CONSTRAINT nn_xxx NOT NULL)
        if re.search(r'CONSTRAINT\s+\w+\s+NOT\s+NULL', rest, re.IGNORECASE):
            nullable = "N"

        return Column(
            owner=owner,
            table_name=table_name,
            column_name=col_name,
            data_type=data_type,
            data_length=data_length,
            nullable=nullable,
            position=position,
        )

    # ----------------------------------------------------------------
    # CREATE INDEX
    # ----------------------------------------------------------------
    def _parse_create_index(self, text: str, result: ParseResult):
        m = self.RE_INDEX.search(text)
        if not m:
            return

        uniqueness = "UNIQUE" if m.group(1) else "NONUNIQUE"
        idx_owner = m.group(2).upper()
        idx_name = m.group(3).upper()
        tbl_owner = m.group(4).upper()
        tbl_name = m.group(5).upper()

        tablespace = ""
        m_ts = self.RE_TABLESPACE.search(text)
        if m_ts:
            tablespace = m_ts.group(1).upper()

        logging = ""
        m_log = self.RE_LOGGING.search(text)
        if m_log:
            logging = m_log.group(1).upper()

        # Extrair colunas do índice
        idx_columns = []
        # Pegar o bloco entre parênteses após ON owner.table
        on_pos = text.upper().find(f" ON {tbl_owner}.{tbl_name}")
        if on_pos >= 0:
            remaining = text[on_pos:]
            m_cols = self.RE_INDEX_COLS.search(remaining)
            if m_cols:
                cols_text = m_cols.group(1)
                for i, col_part in enumerate(cols_text.split(',')):
                    col_part = col_part.strip()
                    if not col_part:
                        continue
                    parts = col_part.split()
                    col_name = parts[0].upper()
                    sort_order = "ASC"
                    if len(parts) > 1 and parts[1].upper() in ("ASC", "DESC"):
                        sort_order = parts[1].upper()

                    idx_col = IndexColumn(
                        owner=idx_owner,
                        index_name=idx_name,
                        column_name=col_name,
                        position=i,
                        sort_order=sort_order,
                    )
                    idx_columns.append(idx_col)

        index = Index(
            owner=idx_owner,
            index_name=idx_name,
            table_name=tbl_name,
            tablespace_name=tablespace,
            uniqueness=uniqueness,
            logging=logging,
            columns=idx_columns,
        )
        result.indexes.append(index)
        result.index_columns.extend(idx_columns)

    # ----------------------------------------------------------------
    # ALTER TABLE (PK / FK)
    # ----------------------------------------------------------------
    def _parse_alter_table(self, text: str, result: ParseResult):
        m_tbl = self.RE_ALTER_TABLE.search(text)
        if not m_tbl:
            return

        owner = m_tbl.group(1).upper()
        table_name = m_tbl.group(2).upper()

        # PRIMARY KEY
        m_pk = self.RE_ALTER_PK.search(text)
        if m_pk:
            pk_name = m_pk.group(1).upper()
            pk_cols = [c.strip().upper() for c in m_pk.group(2).split(',')]
            result.constraints.append(Constraint(
                owner=owner,
                constraint_name=pk_name,
                table_name=table_name,
                constraint_type="PK",
                columns=pk_cols,
            ))
            return

        # FOREIGN KEY
        m_fk = self.RE_ALTER_FK.search(text)
        if m_fk:
            fk_name = (m_fk.group(1) or "").upper()
            fk_cols = [c.strip().upper() for c in m_fk.group(2).split(',')]
            ref_owner = m_fk.group(3).upper()
            ref_table = m_fk.group(4).upper()
            ref_cols = [c.strip().upper() for c in m_fk.group(5).split(',')]

            if not fk_name:
                fk_name = f"FK_{table_name}_{ref_table}"

            result.constraints.append(Constraint(
                owner=owner,
                constraint_name=fk_name,
                table_name=table_name,
                constraint_type="FK",
                columns=fk_cols,
                ref_owner=ref_owner,
                ref_table=ref_table,
                ref_columns=ref_cols,
            ))
            return

        # SUPPLEMENTAL LOG DATA — ignorar
        if "SUPPLEMENTAL" in text.upper():
            return

    # ----------------------------------------------------------------
    # GRANT
    # ----------------------------------------------------------------
    def _parse_grant(self, text: str, result: ParseResult):
        m = self.RE_GRANT.search(text)
        if not m:
            return

        privileges = re.sub(r'\s+', ' ', m.group(1).strip()).upper()
        owner = m.group(2).upper()
        table_name = m.group(3).upper()
        grantee = m.group(4).upper()

        result.grants.append(Grant(
            owner=owner,
            table_name=table_name,
            grantee=grantee,
            privileges=privileges,
        ))

    # ----------------------------------------------------------------
    # COMMENT ON
    # ----------------------------------------------------------------
    def _parse_comment(self, text: str, result: ParseResult):
        # COMMENT ON COLUMN
        m = self.RE_COMMENT_COL.search(text)
        if m:
            result.comments.append(Comment(
                owner=m.group(1).upper(),
                table_name=m.group(2).upper(),
                column_name=m.group(3).upper(),
                comment_text=m.group(4).replace("''", "'"),
            ))
            return

        # COMMENT ON TABLE
        m = self.RE_COMMENT_TABLE.search(text)
        if m:
            result.comments.append(Comment(
                owner=m.group(1).upper(),
                table_name=m.group(2).upper(),
                column_name=None,
                comment_text=m.group(3).replace("''", "'"),
            ))

    # ----------------------------------------------------------------
    # CREATE TABLESPACE
    # ----------------------------------------------------------------
    def _parse_create_tablespace(self, text: str, result: ParseResult):
        m = self.RE_CREATE_TABLESPACE.search(text)
        if not m:
            return

        name = m.group(1).upper()
        logging = ""
        m_log = self.RE_LOGGING.search(text)
        if m_log:
            logging = m_log.group(1).upper()

        extent = ""
        m_ext = self.RE_EXTENT_MGMT.search(text)
        if m_ext:
            extent = m_ext.group(1).strip().upper()

        result.tablespaces.append(Tablespace(
            tablespace_name=name,
            logging=logging,
            extent_management=extent,
        ))

    # ----------------------------------------------------------------
    # CREATE ROLE
    # ----------------------------------------------------------------
    def _parse_create_role(self, text: str, result: ParseResult):
        m = self.RE_CREATE_ROLE.search(text)
        if m:
            result.roles.append(Role(role_name=m.group(1).upper()))
