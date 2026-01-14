"""
PesapalDB Abstract Syntax Tree

Defines AST nodes for all SQL constructs.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union


# Base classes


@dataclass
class ASTNode:
    """Base class for all AST nodes."""

    pass


@dataclass
class Expression(ASTNode):
    """Base class for expressions."""

    pass


@dataclass
class Statement(ASTNode):
    """Base class for SQL statements."""

    pass


# Expressions


@dataclass
class Literal(Expression):
    """A literal value (number, string, boolean, null)."""

    value: Any


@dataclass
class Identifier(Expression):
    """A column or table identifier."""

    name: str


@dataclass
class QualifiedIdentifier(Expression):
    """A qualified identifier like table.column."""

    table: str
    column: str


@dataclass
class BinaryOp(Expression):
    """Binary operation (e.g., a + b, x = y)."""

    left: Expression
    operator: str
    right: Expression


@dataclass
class UnaryOp(Expression):
    """Unary operation (e.g., NOT x, -5)."""

    operator: str
    operand: Expression


@dataclass
class FunctionCall(Expression):
    """Function call (e.g., COUNT(*), SUM(price))."""

    name: str
    arguments: List[Expression] = field(default_factory=list)
    distinct: bool = False


@dataclass
class InList(Expression):
    """IN expression (e.g., x IN (1, 2, 3))."""

    value: Expression
    items: List[Expression] = field(default_factory=list)
    negated: bool = False


@dataclass
class Between(Expression):
    """BETWEEN expression (e.g., x BETWEEN 1 AND 10)."""

    value: Expression
    low: Expression
    high: Expression
    negated: bool = False


@dataclass
class IsNull(Expression):
    """IS NULL expression."""

    value: Expression
    negated: bool = False


@dataclass
class Like(Expression):
    """LIKE expression for pattern matching."""

    value: Expression
    pattern: Expression
    negated: bool = False


@dataclass
class Star(Expression):
    """Represents SELECT *."""

    table: Optional[str] = None


# SELECT components


@dataclass
class SelectColumn:
    """A column in the SELECT clause."""

    expression: Expression
    alias: Optional[str] = None


@dataclass
class TableRef:
    """A table reference in the FROM clause."""

    name: str
    alias: Optional[str] = None


@dataclass
class JoinClause:
    """A JOIN clause."""

    join_type: str  # INNER, LEFT, RIGHT, FULL, CROSS
    table: TableRef
    condition: Optional[Expression] = None


@dataclass
class OrderByItem:
    """An item in the ORDER BY clause."""

    expression: Expression
    ascending: bool = True


@dataclass
class GroupByClause:
    """GROUP BY clause."""

    columns: List[Expression] = field(default_factory=list)
    having: Optional[Expression] = None


# Statements


@dataclass
class SelectStatement(Statement):
    """SELECT statement."""

    columns: List[SelectColumn] = field(default_factory=list)
    from_table: Optional[TableRef] = None
    joins: List[JoinClause] = field(default_factory=list)
    where: Optional[Expression] = None
    group_by: Optional[GroupByClause] = None
    order_by: List[OrderByItem] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    distinct: bool = False


@dataclass
class InsertStatement(Statement):
    """INSERT statement."""

    table: str
    columns: List[str] = field(default_factory=list)
    values: List[List[Expression]] = field(default_factory=list)


@dataclass
class UpdateStatement(Statement):
    """UPDATE statement."""

    table: str
    assignments: List[tuple] = field(default_factory=list)  # [(column, value), ...]
    where: Optional[Expression] = None


@dataclass
class DeleteStatement(Statement):
    """DELETE statement."""

    table: str
    where: Optional[Expression] = None


# DDL - Column definition


@dataclass
class ColumnDef:
    """Column definition in CREATE TABLE."""

    name: str
    data_type: str
    length: Optional[int] = None
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    auto_increment: bool = False
    default: Optional[Expression] = None
    references: Optional[tuple] = None  # (table, column)


@dataclass
class CreateTableStatement(Statement):
    """CREATE TABLE statement."""

    table: str
    columns: List[ColumnDef] = field(default_factory=list)
    if_not_exists: bool = False


@dataclass
class DropTableStatement(Statement):
    """DROP TABLE statement."""

    table: str
    if_exists: bool = False


@dataclass
class CreateIndexStatement(Statement):
    """CREATE INDEX statement."""

    name: str
    table: str
    columns: List[str] = field(default_factory=list)
    unique: bool = False


@dataclass
class DropIndexStatement(Statement):
    """DROP INDEX statement."""

    name: str
    table: Optional[str] = None
