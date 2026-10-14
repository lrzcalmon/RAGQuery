"""
Testes do Metadata Store (SQLite).
"""
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ddl_parser.oracle_parser import OracleDDLParser
from src.metadata_store.db_manager import MetadataDB
from src.metadata_store.queries import MetadataQueries


DDL_FILE = PROJECT_ROOT / "ArqsToRAG" / "exemplo_loja.ddl"


@pytest.fixture
def populated_db():
    """Cria banco temporário populado com dados do DDL."""
    if not DDL_FILE.exists():
        pytest.skip("DDL file not found")

    parser = OracleDDLParser()
    result = parser.parse_file(DDL_FILE)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = MetadataDB(db_path)
    db.connect()
    db.create_schema()
    db.insert_parse_result(result, DDL_FILE)

    yield db, MetadataQueries(db)

    db.close()
    db_path.unlink(missing_ok=True)


class TestMetadataDB:
    def test_get_stats(self, populated_db):
        db, mq = populated_db
        stats = db.get_stats()
        assert stats["ddl_tables"] > 100
        assert stats["ddl_columns"] > 100
        assert stats["ddl_indexes"] > 50
        assert stats["ddl_roles"] > 10

    def test_file_ingestion_log(self, populated_db):
        db, mq = populated_db
        assert db.is_file_ingested(DDL_FILE)


class TestMetadataQueries:
    def test_list_tables_by_owner(self, populated_db):
        db, mq = populated_db
        tables = mq.list_tables("LOJA")
        assert len(tables) > 100

    def test_count_tables(self, populated_db):
        db, mq = populated_db
        count = mq.count_tables()
        assert count > 100

    def test_tables_with_column(self, populated_db):
        db, mq = populated_db
        tables = mq.tables_with_column("COD_LOJA")
        assert len(tables) > 0

    def test_columns_of_table(self, populated_db):
        db, mq = populated_db
        cols = mq.columns_of_table("AUD_INCONSISTENCIA")
        assert len(cols) > 0

    def test_indexes_of_table(self, populated_db):
        db, mq = populated_db
        # VENDA_CLIENTE tem index conhecido
        indexes = mq.indexes_of_table("VENDA_CLIENTE")
        assert len(indexes) > 0

    def test_grants_on_table(self, populated_db):
        db, mq = populated_db
        grants = mq.grants_on_table("AUD_INCONSISTENCIA")
        assert len(grants) > 0

    def test_list_roles(self, populated_db):
        db, mq = populated_db
        roles = mq.list_roles()
        assert len(roles) > 10

    def test_list_tablespaces(self, populated_db):
        db, mq = populated_db
        tss = mq.list_tablespaces()
        assert len(tss) > 0

    def test_list_owners(self, populated_db):
        db, mq = populated_db
        owners = mq.list_owners()
        assert len(owners) > 0
        owner_names = [o["owner"] for o in owners]
        assert "LOJA" in owner_names

    def test_tables_without_index(self, populated_db):
        db, mq = populated_db
        tables = mq.tables_without_index()
        # Deve haver tabelas sem índice
        assert isinstance(tables, list)

    def test_search_object(self, populated_db):
        db, mq = populated_db
        results = mq.search_object("CLIENTE")
        assert results["tables"] or results["columns"] or results["indexes"]
