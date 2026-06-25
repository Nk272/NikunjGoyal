"""
ast_nodes.py
============
Abstract Syntax Tree node definitions produced by parser.py.

These are plain dataclasses with no behaviour; they are a structural
description of a parsed SQL statement that the planner turns into a tree of
physical operators.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


# --- Expressions -----------------------------------------------------------
@dataclass
class Column:
    """A column reference, optionally qualified: `table.name` or `name`."""
    name: str
    table: Optional[str] = None

    @property
    def qualified(self):
        return "{}.{}".format(self.table, self.name) if self.table else self.name


@dataclass
class Literal:
    value: Any           # python int / float / str / bool / None
    raw_type: str        # 'int' | 'float' | 'string' | 'bool' | 'null'


@dataclass
class Star:
    """The `*` in SELECT * or COUNT(*)."""
    pass


@dataclass
class BinOp:
    """Binary comparison / arithmetic / logical operator."""
    op: str
    left: Any
    right: Any


@dataclass
class Aggregate:
    func: str            # 'count' | 'sum' | 'avg' | 'min' | 'max'
    arg: Any             # Column or Star
    alias: Optional[str] = None


# --- Statements ------------------------------------------------------------
@dataclass
class ColumnDef:
    name: str
    type: str            # 'int' | 'float' | 'text'


@dataclass
class CreateTable:
    table: str
    columns: List[ColumnDef]


@dataclass
class Insert:
    table: str
    columns: Optional[List[str]]   # explicit column list, or None
    rows: List[List[Any]]          # each row is a list of Literal


@dataclass
class JoinClause:
    table: str
    on_left: Column
    on_right: Column


@dataclass
class OrderKey:
    expr: Column
    descending: bool = False


@dataclass
class SelectItem:
    """One item in the SELECT projection list."""
    expr: Any                       # Column | Aggregate | Star
    alias: Optional[str] = None


@dataclass
class Select:
    items: List[SelectItem]
    from_table: str
    from_alias: Optional[str] = None
    join: Optional[JoinClause] = None
    where: Optional[Any] = None
    group_by: List[Column] = field(default_factory=list)
    order_by: List[OrderKey] = field(default_factory=list)
    limit: Optional[int] = None
