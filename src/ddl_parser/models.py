"""
Dataclasses para representar objetos Oracle parseados do DDL.
"""
from dataclasses import dataclass, field


@dataclass
class Column:
    owner: str
    table_name: str
    column_name: str
    data_type: str
    data_length: int | None = None
    nullable: str = "Y"
    position: int = 0


@dataclass
class Table:
    owner: str
    table_name: str
    tablespace_name: str = ""
    pctfree: int | None = None
    pctused: int | None = None
    logging: str = ""
    full_ddl: str = ""
    columns: list[Column] = field(default_factory=list)


@dataclass
class IndexColumn:
    owner: str
    index_name: str
    column_name: str
    position: int = 0
    sort_order: str = "ASC"


@dataclass
class Index:
    owner: str
    index_name: str
    table_name: str
    tablespace_name: str = ""
    uniqueness: str = "NONUNIQUE"
    logging: str = ""
    columns: list[IndexColumn] = field(default_factory=list)


@dataclass
class Constraint:
    owner: str
    constraint_name: str
    table_name: str
    constraint_type: str = ""  # PK, FK, UK, CHECK
    columns: list[str] = field(default_factory=list)
    ref_owner: str = ""
    ref_table: str = ""
    ref_columns: list[str] = field(default_factory=list)


@dataclass
class Grant:
    owner: str
    table_name: str
    grantee: str
    privileges: str = ""


@dataclass
class Tablespace:
    tablespace_name: str
    logging: str = ""
    extent_management: str = ""


@dataclass
class Role:
    role_name: str


@dataclass
class Comment:
    owner: str
    table_name: str
    column_name: str | None = None
    comment_text: str = ""


@dataclass
class ParseResult:
    """Resultado consolidado do parsing de um arquivo DDL."""
    tables: list[Table] = field(default_factory=list)
    columns: list[Column] = field(default_factory=list)
    indexes: list[Index] = field(default_factory=list)
    index_columns: list[IndexColumn] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    grants: list[Grant] = field(default_factory=list)
    tablespaces: list[Tablespace] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    @property
    def total_objects(self) -> int:
        return (len(self.tables) + len(self.indexes) + len(self.constraints)
                + len(self.grants) + len(self.tablespaces) + len(self.roles)
                + len(self.comments))
