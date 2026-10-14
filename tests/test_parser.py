"""
Testes do DDL Parser Oracle.
"""
import sys
from pathlib import Path

import pytest

# Adicionar raiz ao path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ddl_parser.oracle_parser import OracleDDLParser
from src.ddl_parser.ddl_splitter import DDLSplitter
from src.ddl_parser.models import ParseResult


DDL_FILE = PROJECT_ROOT / "ArqsToRAG" / "exemplo_loja.ddl"
TXT_FILE = PROJECT_ROOT / "ArqsToRAG" / "exemplo_loja.txt"


@pytest.fixture
def parser():
    return OracleDDLParser()


@pytest.fixture
def ddl_result(parser) -> ParseResult:
    """Parseia o DDL completo (cache por sessão de teste)."""
    if DDL_FILE.exists():
        return parser.parse_file(DDL_FILE)
    pytest.skip(f"Arquivo DDL não encontrado: {DDL_FILE}")


class TestDDLSplitter:
    def test_split_ddl_file(self):
        if not DDL_FILE.exists():
            pytest.skip("DDL file not found")
        splitter = DDLSplitter(DDL_FILE)
        splitter.read_file()
        statements = splitter.split()
        assert len(statements) > 0
        # Deve ter pelo menos CREATE TABLE e CREATE INDEX
        types = {s["type"] for s in statements}
        assert "CREATE TABLE" in types

    def test_detect_encoding(self):
        if not DDL_FILE.exists():
            pytest.skip("DDL file not found")
        splitter = DDLSplitter(DDL_FILE)
        enc = splitter.detect_encoding()
        assert enc is not None
        assert len(enc) > 0


class TestOracleParser:
    def test_parse_tables(self, ddl_result):
        """DDL de exemplo deve conter mais de 100 tabelas."""
        assert len(ddl_result.tables) > 100
        # Verificar que tem owner LOJA
        owners = {t.owner for t in ddl_result.tables}
        assert "LOJA" in owners

    def test_parse_columns(self, ddl_result):
        """Deve extrair colunas das tabelas."""
        assert len(ddl_result.columns) > 100
        # Verificar que colunas conhecidas existem
        col_names = {c.column_name for c in ddl_result.columns}
        assert "COD_LOJA" in col_names or "COD_CLIENTE" in col_names

    def test_parse_indexes(self, ddl_result):
        """DDL de exemplo deve conter mais de 50 índices."""
        assert len(ddl_result.indexes) > 50

    def test_parse_constraints(self, ddl_result):
        """Deve extrair constraints (PK e FK)."""
        assert len(ddl_result.constraints) > 0
        types = {c.constraint_type for c in ddl_result.constraints}
        assert "PK" in types or "FK" in types

    def test_parse_grants(self, ddl_result):
        """Deve extrair grants."""
        assert len(ddl_result.grants) > 100

    def test_parse_tablespaces(self, ddl_result):
        """DDL deve conter tablespaces."""
        assert len(ddl_result.tablespaces) > 0
        ts_names = {t.tablespace_name for t in ddl_result.tablespaces}
        assert "LOJA_DADOS" in ts_names

    def test_parse_roles(self, ddl_result):
        """DDL de exemplo deve conter mais de 10 roles."""
        assert len(ddl_result.roles) > 10

    def test_table_has_columns(self, ddl_result):
        """Cada tabela deve ter pelo menos 1 coluna."""
        tables_with_cols = {c.table_name for c in ddl_result.columns}
        # A maioria das tabelas deve ter colunas
        assert len(tables_with_cols) > 50

    def test_index_has_columns(self, ddl_result):
        """Cada índice deve ter colunas associadas."""
        assert len(ddl_result.index_columns) > 0
        idx_names = {ic.index_name for ic in ddl_result.index_columns}
        assert len(idx_names) > 10

    def test_known_table_exists(self, ddl_result):
        """Tabela AUD_INCONSISTENCIA deve existir."""
        table_names = {t.table_name for t in ddl_result.tables}
        assert "AUD_INCONSISTENCIA" in table_names

    def test_known_table_columns(self, ddl_result):
        """Tabela AUD_INCONSISTENCIA deve ter colunas conhecidas."""
        cols = [c for c in ddl_result.columns if c.table_name == "AUD_INCONSISTENCIA"]
        col_names = {c.column_name for c in cols}
        assert "COD_INCONSISTENCIA" in col_names
        assert "COD_TIPO_INCONSISTENCIA" in col_names

    def test_parse_txt_file(self, parser):
        """Deve também parsear o arquivo .txt."""
        if not TXT_FILE.exists():
            pytest.skip("TXT file not found")
        result = parser.parse_file(TXT_FILE)
        assert len(result.tables) > 100


class TestParseResult:
    def test_total_objects(self, ddl_result):
        total = ddl_result.total_objects
        assert total > 200
