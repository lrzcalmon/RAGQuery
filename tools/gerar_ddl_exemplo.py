"""
Gera um DDL Oracle fictício (domínio de varejo) para demonstrar e testar o RAGQuery.

Uso:
    python tools/gerar_ddl_exemplo.py

Gera ArqsToRAG/exemplo_loja.ddl (e uma cópia .txt para testar o parser com essa extensão). Nenhum dado real: nomes e estruturas são inventados.
"""
import random
from pathlib import Path

random.seed(42)

OWNER = "LOJA"
TS_DADOS = "LOJA_DADOS"
TS_INDICE = "LOJA_INDICE"
OUT = Path(__file__).resolve().parent.parent / "ArqsToRAG" / "exemplo_loja.ddl"

DOMINIOS = {
    "VENDA": ["CLIENTE", "PEDIDO", "ITEM_PEDIDO", "LOJA", "ERRO", "CUPOM", "DEVOLUCAO", "CARRINHO",
              "PAGAMENTO", "FRETE", "ENTREGA", "AVALIACAO", "PROMOCAO", "VENDEDOR", "COMISSAO",
              "CANAL", "META", "CAMPANHA", "TROCA", "NOTA_FISCAL"],
    "ESTOQUE": ["PRODUTO", "CATEGORIA", "MARCA", "FORNECEDOR", "DEPOSITO", "MOVIMENTO", "SALDO",
                "LOTE", "INVENTARIO", "TRANSFERENCIA", "RESERVA", "PRECO", "CUSTO", "EMBALAGEM",
                "UNIDADE", "COMPRA", "COTACAO", "RECEBIMENTO", "AJUSTE", "PERDA"],
    "FIN": ["CONTA", "TITULO", "BAIXA", "BANCO", "AGENCIA", "CENTRO_CUSTO", "PLANO_CONTAS",
            "LANCAMENTO", "CONCILIACAO", "IMPOSTO", "ALIQUOTA", "BOLETO", "CARTAO", "PARCELA",
            "ADIANTAMENTO", "REEMBOLSO", "ORCAMENTO", "FLUXO_CAIXA", "COBRANCA", "CHEQUE"],
    "RH": ["FUNCIONARIO", "CARGO", "DEPARTAMENTO", "FOLHA", "BENEFICIO", "FERIAS", "PONTO",
           "ESCALA", "TREINAMENTO", "AVALIACAO", "DEPENDENTE", "AFASTAMENTO", "ADMISSAO",
           "DESLIGAMENTO", "SALARIO", "BANCO_HORAS", "TURNO", "LOTACAO", "CURSO", "VAGA"],
    "AUD": ["INCONSISTENCIA", "TIPO_INCONSISTENCIA", "LOG_CARGA", "LOG_ACESSO", "LOG_ALTERACAO",
            "REGRA", "EXECUCAO", "ALERTA", "SESSAO", "PARAMETRO", "AGENDA", "PROCESSO",
            "ARQUIVO", "LOTE_CARGA", "STATUS", "MENSAGEM", "VALIDACAO", "RESULTADO", "OCORRENCIA",
            "HISTORICO"],
    "CRM": ["CONTATO", "INTERACAO", "SEGMENTO", "PREFERENCIA", "OPORTUNIDADE", "LEAD", "TICKET",
            "PESQUISA", "RESPOSTA", "FIDELIDADE"],
}

ROLES = ["ROLE_LOJA_CONSULTA", "ROLE_LOJA_ESCRITA", "ROLE_VENDAS", "ROLE_ESTOQUE", "ROLE_FINANCEIRO",
         "ROLE_RH", "ROLE_AUDITORIA", "ROLE_CRM", "ROLE_BI", "ROLE_ETL", "ROLE_SUPORTE", "ROLE_ADMIN"]
APP_USERS = ["APP_PORTAL", "APP_BATCH", "APP_RELATORIOS"]

COLS_EXTRA = [
    ("DESCRICAO", "VARCHAR2 (200 BYTE)"), ("STATUS", "CHAR (1 BYTE)"), ("VALOR", "NUMBER (15,2)"),
    ("QUANTIDADE", "NUMBER (10)"), ("DATA_CRIACAO", "DATE"), ("DATA_ALTERACAO", "DATE"),
    ("USUARIO_ALTERACAO", "VARCHAR2 (30 BYTE)"), ("OBSERVACAO", "VARCHAR2 (4000 BYTE)"),
    ("COD_LOJA", "NUMBER (5)"), ("COD_CLIENTE", "NUMBER (12)"),
]

STORAGE = """    PCTFREE 10
    PCTUSED 40
    TABLESPACE {ts}
    LOGGING
    STORAGE (
    INITIAL 65536
    NEXT 1048576
    PCTINCREASE 0
    MINEXTENTS 1
    MAXEXTENTS 2147483645
    FREELISTS 1
    FREELIST GROUPS 1
    BUFFER_POOL DEFAULT
    )"""


def main() -> None:
    out = ["-- DDL fictício gerado por tools/gerar_ddl_exemplo.py (domínio de varejo).",
           "-- Não contém dados reais.", ""]
    for ts in (TS_DADOS, TS_INDICE):
        out.append(f"CREATE TABLESPACE {ts} \n    LOGGING \n    ONLINE \n    EXTENT MANAGEMENT LOCAL AUTOALLOCATE \n    FLASHBACK ON \n;\n")
    for role in ROLES:
        out.append(f"CREATE ROLE {role} \n    NOT IDENTIFIED \n;\n")

    tabelas = []
    for prefixo, nomes in DOMINIOS.items():
        for nome in nomes:
            tabelas.append(f"{prefixo}_{nome}")

    # Chaves estrangeiras de exemplo
    fks = [
        ("VENDA_PEDIDO", "VENDA_CLIENTE"), ("VENDA_PEDIDO", "VENDA_LOJA"), ("VENDA_ITEM_PEDIDO", "VENDA_PEDIDO"),
        ("VENDA_ITEM_PEDIDO", "ESTOQUE_PRODUTO"), ("VENDA_ERRO", "VENDA_LOJA"), ("VENDA_PAGAMENTO", "VENDA_PEDIDO"),
        ("VENDA_ENTREGA", "VENDA_PEDIDO"), ("VENDA_CLIENTE", "VENDA_LOJA"), ("ESTOQUE_SALDO", "ESTOQUE_PRODUTO"),
        ("ESTOQUE_PRODUTO", "ESTOQUE_CATEGORIA"), ("AUD_INCONSISTENCIA", "AUD_TIPO_INCONSISTENCIA"),
        ("FIN_TITULO", "FIN_CONTA"), ("RH_FUNCIONARIO", "RH_CARGO"),
    ]
    def pk_de(t: str) -> str:
        return {"VENDA_LOJA": "COD_LOJA", "VENDA_CLIENTE": "COD_CLIENTE"}.get(t, "COD_" + t.split("_", 1)[1])

    pks = {}
    for t in tabelas:
        pk = pk_de(t)
        pks[t] = pk
        cols = [(pk, "NUMBER (12)  NOT NULL")]
        if t == "AUD_INCONSISTENCIA":
            cols.append(("COD_TIPO_INCONSISTENCIA", "NUMBER (5)  NOT NULL"))
        extras = random.sample(COLS_EXTRA, k=random.randint(3, 7))
        for c, tipo in extras:
            if c != pk and c not in {x[0] for x in cols}:
                cols.append((c, tipo))
        if t.startswith("VENDA_") and "COD_LOJA" not in {x[0] for x in cols}:
            cols.append(("COD_LOJA", "NUMBER (5)"))
        for filha, pai in fks:
            if filha == t and pk_de(pai) not in {x[0] for x in cols}:
                cols.append((pk_de(pai), "NUMBER (12)"))
        body = " , \n".join(f"     {c} {tipo}" for c, tipo in cols)
        out.append(f"CREATE TABLE {OWNER}.{t} \n    ( \n{body} \n    ) \n{STORAGE.format(ts=TS_DADOS)} \n;\n")
        out.append(f"COMMENT ON TABLE {OWNER}.{t} IS 'Tabela fictícia de exemplo ({t})' \n;\n")

        idx_pk = f"PK_{t}"
        out.append(f"CREATE UNIQUE INDEX {OWNER}.{idx_pk} ON {OWNER}.{t} \n    ( \n     {pk} ASC \n    ) \n{STORAGE.format(ts=TS_INDICE)} \n;\n")
        col_names = [c for c, _ in cols]
        if "COD_LOJA" in col_names and pk != "COD_LOJA":
            out.append(f"CREATE INDEX {OWNER}.IX_{t}_01 ON {OWNER}.{t} \n    ( \n     COD_LOJA ASC , \n     {pk} ASC \n    ) \n{STORAGE.format(ts=TS_INDICE)} \n;\n")
        out.append(f"ALTER TABLE {OWNER}.{t} \n    ADD CONSTRAINT {idx_pk} PRIMARY KEY ( {pk} ) \n    USING INDEX {OWNER}.{idx_pk} ;\n")

        out.append(f"GRANT SELECT \n    ON {OWNER}.{t} TO ROLE_LOJA_CONSULTA \n;\n")
        out.append(f"GRANT SELECT \n    ON {OWNER}.{t} TO ROLE_BI \n;\n")
        out.append(f"GRANT DELETE, INSERT, SELECT, UPDATE \n    ON {OWNER}.{t} TO ROLE_LOJA_ESCRITA \n;\n")
        if t.startswith("VENDA_"):
            out.append(f"GRANT DELETE, INSERT, SELECT, UPDATE \n    ON {OWNER}.{t} TO APP_PORTAL \n;\n")

    for i, (filha, pai) in enumerate(fks, 1):
        col = pks[pai]
        out.append(f"ALTER TABLE {OWNER}.{filha} \n    ADD CONSTRAINT FK_{filha}_{i:02d} FOREIGN KEY \n    ( \n     {col}\n    ) \n    REFERENCES {OWNER}.{pai} \n    ( \n     {col}\n    ) \n    NOT DEFERRABLE \n;\n")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(out), encoding="utf-8")
    OUT.with_suffix(".txt").write_text("\n".join(out), encoding="utf-8")
    print(f"Gerado {OUT} com {len(tabelas)} tabelas")


if __name__ == "__main__":
    main()
