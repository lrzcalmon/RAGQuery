"""
Schema SQLite para armazenamento de metadados DDL Oracle.
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ddl_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    table_name TEXT NOT NULL,
    tablespace_name TEXT,
    pctfree INTEGER,
    pctused INTEGER,
    logging TEXT,
    full_ddl TEXT,
    UNIQUE(owner, table_name)
);

CREATE TABLE IF NOT EXISTS ddl_columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    data_length INTEGER,
    nullable TEXT DEFAULT 'Y',
    position INTEGER
);

CREATE TABLE IF NOT EXISTS ddl_indexes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    index_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    tablespace_name TEXT,
    uniqueness TEXT DEFAULT 'NONUNIQUE',
    logging TEXT,
    UNIQUE(owner, index_name)
);

CREATE TABLE IF NOT EXISTS ddl_index_columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    index_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    position INTEGER,
    sort_order TEXT DEFAULT 'ASC'
);

CREATE TABLE IF NOT EXISTS ddl_constraints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    constraint_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    constraint_type TEXT,
    columns TEXT,
    ref_owner TEXT,
    ref_table TEXT,
    ref_columns TEXT
);

CREATE TABLE IF NOT EXISTS ddl_grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    table_name TEXT NOT NULL,
    grantee TEXT NOT NULL,
    privileges TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ddl_tablespaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tablespace_name TEXT UNIQUE NOT NULL,
    logging TEXT,
    extent_management TEXT
);

CREATE TABLE IF NOT EXISTS ddl_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS ddl_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    table_name TEXT NOT NULL,
    column_name TEXT,
    comment_text TEXT
);

CREATE TABLE IF NOT EXISTS ddl_ingestion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    objects_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'OK'
);

CREATE INDEX IF NOT EXISTS idx_columns_name ON ddl_columns(column_name);
CREATE INDEX IF NOT EXISTS idx_columns_table ON ddl_columns(owner, table_name);
CREATE INDEX IF NOT EXISTS idx_indexes_table ON ddl_indexes(table_name);
CREATE INDEX IF NOT EXISTS idx_grants_table ON ddl_grants(table_name);
CREATE INDEX IF NOT EXISTS idx_grants_grantee ON ddl_grants(grantee);
CREATE INDEX IF NOT EXISTS idx_constraints_table ON ddl_constraints(table_name);
CREATE INDEX IF NOT EXISTS idx_constraints_ref ON ddl_constraints(ref_table);
CREATE INDEX IF NOT EXISTS idx_comments_table ON ddl_comments(owner, table_name);
CREATE INDEX IF NOT EXISTS idx_tables_owner ON ddl_tables(owner);
CREATE INDEX IF NOT EXISTS idx_tables_tablespace ON ddl_tables(tablespace_name);
"""
