# RAGQuery

Pergunte em português sobre um banco Oracle e receba a resposta na hora, sem acesso ao banco e sem internet.

O RAGQuery lê os scripts DDL de um schema Oracle, guarda a estrutura (tabelas, colunas, índices, constraints, grants, roles, tablespaces) num SQLite e responde perguntas em linguagem natural numa interface web local. Nasceu de uma necessidade real: times que mantêm data warehouses grandes, com centenas de tabelas, gastam tempo procurando "quem referencia esta tabela" ou "quais tabelas têm esta coluna" em DDLs de milhares de linhas.

**Abordagem híbrida:** a maior parte das perguntas é resolvida de forma determinística (classificador de intenção + SQL sobre os metadados), o que é rápido e não alucina. Um LLM local (Phi-3-mini) e a busca semântica (ChromaDB) são opcionais e entram só nas perguntas que o classificador não resolve.

> Os dados deste repositório são **fictícios**. O DDL de exemplo (`ArqsToRAG/exemplo_loja.ddl`, um varejo com 110 tabelas) é gerado por `tools/gerar_ddl_exemplo.py`.

## Características

- **Consultas instantâneas** — Perguntas sobre tabelas, colunas, índices, constraints, grants, roles, tablespaces
- **100% Offline** — Funciona sem internet (exceto download opcional do modelo LLM)
- **Leve** — Roda em máquinas com 8GB RAM, sem GPU
- **Instalável** — Duas versões de instalador Windows (Light e Full)
- **LLM opcional** — Funciona em modo determinístico; LLM melhora classificação de perguntas complexas

## Estrutura

```
RAGQuery/
├── src/
│   ├── config.py                  # Configurações centrais
│   ├── ddl_parser/                # Parser de DDL Oracle
│   ├── metadata_store/            # SQLite: schema, CRUD, queries
│   ├── query_engine/              # Intent classifier + SQL generator + response builder
│   ├── llm/                       # Phi-3-mini via llama-cpp (opcional)
│   ├── vector_store/              # ChromaDB + embeddings (opcional)
│   └── web/                       # Flask: app, routes, templates, static
├── scripts/
│   ├── ingest.py                  # Pipeline de ingestão DDL → SQLite
│   └── serve.py                   # Inicia servidor web
├── installer/
│   ├── build.py                   # Script de build (Versão A e C)
│   ├── ragquery.spec              # PyInstaller spec
│   ├── ragquery_light.iss         # Inno Setup - Versão A (Light)
│   └── ragquery_full.iss          # Inno Setup - Versão C (Full)
├── tools/
│   └── gerar_ddl_exemplo.py       # Gera o DDL fictício de exemplo
├── launcher.py                    # Entry point: auto-ingest + Flask + abre browser
├── ArqsToRAG/                     # DDLs fonte (no repositório, só o exemplo fictício)
├── data/                          # metadata.db (gerado)
├── models/                        # Modelo LLM GGUF (opcional)
└── tests/                         # Testes automatizados (48 testes)
```

## Início Rápido (Desenvolvedor)

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Ingerir DDLs

O repositório já traz o DDL de exemplo. Para recriá-lo: `python tools/gerar_ddl_exemplo.py`.

```bash
python scripts/ingest.py --input-dir ArqsToRAG/ --recreate --no-vectors
```

### 3. Iniciar servidor
```bash
python scripts/serve.py --debug
# ou
python launcher.py   # auto-ingest + abre browser
```

Acesse http://127.0.0.1:5000

## Versões do Instalador

| Versão | Descrição | Tamanho | LLM |
|--------|-----------|---------|-----|
| **A (Light)** | App + parser + interface web | ~50-80 MB | Download pela interface (~2.4 GB) |
| **C (Full)** | Tudo-em-um com modelo Phi-3-mini | ~2.8 GB | Incluído, zero configuração |

### Build dos instaladores
```bash
# Ambas as versões
python installer/build.py --version all

# Apenas Versão A (Light)
python installer/build.py --version A

# Apenas Versão C (Full)
python installer/build.py --version C
```

Requisitos de build: Python 3.11+, PyInstaller, Inno Setup 6.

## Tecnologias

| Componente | Tecnologia |
|-----------|-----------|
| Parser DDL | Regex + dataclasses (Oracle DDL) |
| Metadata Store | SQLite (nativo Python) |
| Query Engine | Regex intent classifier + SQL |
| LLM (opcional) | Phi-3-mini-4k (GGUF Q4) via llama-cpp-python |
| Interface | Flask + HTML/CSS/JS (dark theme) |
| Build | PyInstaller + Inno Setup |

## Exemplos de Perguntas

- Quais as tabelas do owner LOJA?
- Quais tabelas possuem a coluna COD_LOJA?
- Quais os índices da tabela VENDA_CLIENTE?
- Quais roles existem?
- Grants na tabela AUD_INCONSISTENCIA
- Quais tabelas referenciam VENDA_LOJA?
- Tabelas sem índice
- Quais tablespaces existem?

## Testes

```bash
python -m pytest tests/ -v
```

48 testes cobrindo: parser DDL, metadata store, intent classifier.

## Adicionando novos DDLs

1. Coloque arquivos `.ddl`, `.sql` ou `.txt` em `ArqsToRAG/`
2. Execute: `python scripts/ingest.py` (modo incremental)
3. Reinicie o servidor

## Autor

Ricardo Calmon · [GitHub](https://github.com/lrzcalmon)

## Licença

MIT
