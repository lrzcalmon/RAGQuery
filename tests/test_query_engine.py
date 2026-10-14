"""
Testes do Query Engine (intent classifier + response builder).
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.query_engine.intent_classifier import IntentClassifier, IntentType


@pytest.fixture
def classifier():
    return IntentClassifier()


class TestIntentClassifier:
    """Testa classificação de intenção para cada categoria de pergunta."""

    def test_list_tables_by_owner(self, classifier):
        intent = classifier.classify("Quais as tabelas do owner LOJA?")
        assert intent.intent_type == IntentType.LIST_TABLES
        assert intent.params.get("owner") == "LOJA"

    def test_list_tables_from_owner(self, classifier):
        intent = classifier.classify("Liste as tabelas de LOJA")
        assert intent.intent_type == IntentType.LIST_TABLES

    def test_count_tables(self, classifier):
        intent = classifier.classify("Quantas tabelas existem?")
        assert intent.intent_type == IntentType.COUNT_TABLES

    def test_tables_in_tablespace(self, classifier):
        intent = classifier.classify("Tabelas no tablespace LOJA_DADOS")
        assert intent.intent_type == IntentType.TABLES_IN_TABLESPACE
        assert intent.params.get("tablespace") == "LOJA_DADOS"

    def test_tables_with_prefix(self, classifier):
        intent = classifier.classify("Tabelas com prefixo VENDA_")
        assert intent.intent_type == IntentType.TABLES_WITH_PREFIX

    def test_columns_of_table(self, classifier):
        intent = classifier.classify("Quais as colunas da tabela VENDA_CLIENTE?")
        assert intent.intent_type == IntentType.COLUMNS_OF_TABLE
        assert intent.params.get("table_name") == "VENDA_CLIENTE"

    def test_tables_with_column(self, classifier):
        intent = classifier.classify("Quais tabelas possuem a coluna COD_LOJA?")
        assert intent.intent_type == IntentType.TABLES_WITH_COLUMN
        assert intent.params.get("column_name") == "COD_LOJA"

    def test_indexes_of_table(self, classifier):
        intent = classifier.classify("Quais os índices da tabela VENDA_PEDIDO?")
        assert intent.intent_type == IntentType.INDEXES_OF_TABLE
        assert intent.params.get("table_name") == "VENDA_PEDIDO"

    def test_tables_without_index(self, classifier):
        intent = classifier.classify("Tabelas sem índice")
        assert intent.intent_type == IntentType.TABLES_WITHOUT_INDEX

    def test_constraints_of_table(self, classifier):
        intent = classifier.classify("Constraints da tabela VENDA_ERRO")
        assert intent.intent_type == IntentType.CONSTRAINTS_OF_TABLE

    def test_tables_referencing(self, classifier):
        intent = classifier.classify("Quais tabelas referenciam VENDA_LOJA?")
        assert intent.intent_type == IntentType.TABLES_REFERENCING
        assert intent.params.get("table_name") == "VENDA_LOJA"

    def test_grants_on_table(self, classifier):
        intent = classifier.classify("Quais os grants da tabela AUD_INCONSISTENCIA?")
        assert intent.intent_type == IntentType.GRANTS_ON_TABLE

    def test_who_has_access(self, classifier):
        intent = classifier.classify("Quem tem acesso à tabela VENDA_CLIENTE?")
        assert intent.intent_type == IntentType.GRANTS_ON_TABLE

    def test_list_tablespaces(self, classifier):
        intent = classifier.classify("Quais tablespaces existem?")
        assert intent.intent_type == IntentType.LIST_TABLESPACES

    def test_list_roles(self, classifier):
        intent = classifier.classify("Quais roles existem?")
        assert intent.intent_type == IntentType.LIST_ROLES

    def test_roles_with_prefix(self, classifier):
        intent = classifier.classify("Roles que começam com ROLE_")
        assert intent.intent_type == IntentType.ROLES_WITH_PREFIX

    def test_list_owners(self, classifier):
        intent = classifier.classify("Quais owners existem?")
        assert intent.intent_type == IntentType.LIST_OWNERS

    def test_pk_of_table(self, classifier):
        intent = classifier.classify("PK da tabela VENDA_CLIENTE")
        assert intent.intent_type == IntentType.PK_OF_TABLE

    def test_fk_of_table(self, classifier):
        intent = classifier.classify("FKs da tabela VENDA_ERRO")
        assert intent.intent_type == IntentType.FKS_OF_TABLE

    def test_unknown_intent(self, classifier):
        intent = classifier.classify("Qual o sentido da vida?")
        assert intent.intent_type == IntentType.UNKNOWN
