"""
PesapalDB Query Executor

Executes parsed SQL AST nodes against the database.
"""

from typing import Any, Dict, List, Optional, Tuple
import re

from ..schema import Schema, Table, Column
from ..storage import StorageEngine
from ..indexing import IndexManager
from ..constraints import ConstraintChecker, ConstraintViolation
from ..types import DataType, parse_column_type
from ..parser.ast import (
    Expression,
    Statement,
    Literal,
    Identifier,
    QualifiedIdentifier,
    BinaryOp,
    UnaryOp,
    FunctionCall,
    InList,
    Between,
    IsNull,
    Like,
    Star,
    SelectColumn,
    TableRef,
    JoinClause,
    OrderByItem,
    GroupByClause,
    SelectStatement,
    InsertStatement,
    UpdateStatement,
    DeleteStatement,
    ColumnDef,
    CreateTableStatement,
    DropTableStatement,
    CreateIndexStatement,
    DropIndexStatement,
)


class QueryResult:
    """Result of a query execution."""

    def __init__(
        self,
        success: bool = True,
        message: str = "",
        rows: List[Dict[str, Any]] = None,
        columns: List[str] = None,
        row_count: int = 0,
    ):
        self.success = success
        self.message = message
        self.rows = rows or []
        self.columns = columns or []
        self.row_count = row_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "rows": self.rows,
            "columns": self.columns,
            "row_count": self.row_count,
        }


class QueryExecutor:
    """Executes SQL statements against the database."""

    def __init__(
        self,
        schema: Schema,
        storage: StorageEngine,
        indexes: Dict[str, IndexManager] = None,
    ):
        self.schema = schema
        self.storage = storage
        self.indexes = indexes or {}

    def execute(self, statement: Statement) -> QueryResult:
        """Execute a single SQL statement."""
        try:
            if isinstance(statement, SelectStatement):
                return self._execute_select(statement)
            elif isinstance(statement, InsertStatement):
                return self._execute_insert(statement)
            elif isinstance(statement, UpdateStatement):
                return self._execute_update(statement)
            elif isinstance(statement, DeleteStatement):
                return self._execute_delete(statement)
            elif isinstance(statement, CreateTableStatement):
                return self._execute_create_table(statement)
            elif isinstance(statement, DropTableStatement):
                return self._execute_drop_table(statement)
            elif isinstance(statement, CreateIndexStatement):
                return self._execute_create_index(statement)
            elif isinstance(statement, DropIndexStatement):
                return self._execute_drop_index(statement)
            else:
                return QueryResult(
                    success=False,
                    message=f"Unknown statement type: {type(statement).__name__}",
                )
        except ConstraintViolation as e:
            return QueryResult(success=False, message=str(e))
        except Exception as e:
            return QueryResult(success=False, message=str(e))

    # SELECT

    def _execute_select(self, stmt: SelectStatement) -> QueryResult:
        """Execute SELECT statement."""
        if not stmt.from_table:
            # SELECT without FROM (e.g., SELECT 1+1)
            row = {}
            for col in stmt.columns:
                value = self._evaluate_expr(col.expression, {})
                alias = col.alias or str(col.expression)
                row[alias] = value
            return QueryResult(
                success=True,
                message="Query executed",
                rows=[row],
                columns=list(row.keys()),
                row_count=1,
            )

        table_name = stmt.from_table.name
        table_alias = stmt.from_table.alias or table_name

        if not self.schema.has_table(table_name):
            return QueryResult(
                success=False, message=f"Table '{table_name}' does not exist"
            )

        # Get base rows
        rows = self.storage.read_table(table_name)

        # Add table prefix to columns
        working_rows = []
        for row in rows:
            prefixed = {f"{table_alias}.{k}": v for k, v in row.items()}
            prefixed.update(row)  # Also allow unprefixed access
            working_rows.append(prefixed)

        # Process JOINs
        for join in stmt.joins:
            working_rows = self._execute_join(working_rows, join, table_alias)

        # Apply WHERE
        if stmt.where:
            working_rows = [
                row for row in working_rows if self._evaluate_expr(stmt.where, row)
            ]

        # Apply GROUP BY
        if stmt.group_by:
            working_rows = self._execute_group_by(working_rows, stmt)

        # Apply DISTINCT
        if stmt.distinct:
            seen = set()
            unique_rows = []
            for row in working_rows:
                key = tuple(sorted(row.items()))
                if key not in seen:
                    seen.add(key)
                    unique_rows.append(row)
            working_rows = unique_rows

        # Apply ORDER BY
        if stmt.order_by:
            for order_item in reversed(stmt.order_by):
                working_rows.sort(
                    key=lambda r: self._evaluate_expr(order_item.expression, r) or "",
                    reverse=not order_item.ascending,
                )

        # Apply LIMIT/OFFSET
        if stmt.offset:
            working_rows = working_rows[stmt.offset :]
        if stmt.limit:
            working_rows = working_rows[: stmt.limit]

        # Project columns
        result_rows = []
        columns = []

        for row in working_rows:
            result_row = {}
            for i, col in enumerate(stmt.columns):
                if isinstance(col.expression, Star):
                    # Expand *
                    if col.expression.table:
                        prefix = f"{col.expression.table}."
                        for k, v in row.items():
                            if k.startswith(prefix):
                                col_name = k[len(prefix) :]
                                result_row[col_name] = v
                                if col_name not in columns:
                                    columns.append(col_name)
                    else:
                        # Get columns from the table schema
                        table = self.schema.get_table(table_name)
                        for c in table.columns:
                            result_row[c.name] = row.get(c.name) or row.get(
                                f"{table_alias}.{c.name}"
                            )
                            if c.name not in columns:
                                columns.append(c.name)
                else:
                    value = self._evaluate_expr(col.expression, row)
                    alias = col.alias or self._expr_to_string(col.expression)
                    result_row[alias] = value
                    if alias not in columns:
                        columns.append(alias)

            result_rows.append(result_row)

        return QueryResult(
            success=True,
            message="Query executed",
            rows=result_rows,
            columns=columns,
            row_count=len(result_rows),
        )

    def _execute_join(
        self, left_rows: List[Dict], join: JoinClause, left_alias: str
    ) -> List[Dict]:
        """Execute a JOIN operation."""
        right_table = join.table.name
        right_alias = join.table.alias or right_table

        if not self.schema.has_table(right_table):
            raise ValueError(f"Table '{right_table}' does not exist")

        right_rows = self.storage.read_table(right_table)

        # Prefix right table columns
        right_prefixed = []
        for row in right_rows:
            prefixed = {f"{right_alias}.{k}": v for k, v in row.items()}
            prefixed.update(row)
            right_prefixed.append(prefixed)

        result = []

        if join.join_type == "CROSS":
            # Cartesian product
            for left in left_rows:
                for right in right_prefixed:
                    result.append({**left, **right})
        elif join.join_type in ("INNER", "LEFT", "RIGHT", "FULL"):
            left_matched = set()
            right_matched = set()

            for i, left in enumerate(left_rows):
                matched = False
                for j, right in enumerate(right_prefixed):
                    combined = {**left, **right}
                    if join.condition is None or self._evaluate_expr(
                        join.condition, combined
                    ):
                        result.append(combined)
                        matched = True
                        left_matched.add(i)
                        right_matched.add(j)

                # LEFT OUTER: include unmatched left rows
                if not matched and join.join_type in ("LEFT", "FULL"):
                    null_right = (
                        {f"{right_alias}.{k}": None for k in right_rows[0].keys()}
                        if right_rows
                        else {}
                    )
                    result.append({**left, **null_right})

            # RIGHT OUTER: include unmatched right rows
            if join.join_type in ("RIGHT", "FULL"):
                for j, right in enumerate(right_prefixed):
                    if j not in right_matched:
                        null_left = (
                            {k: None for k in left_rows[0].keys()} if left_rows else {}
                        )
                        result.append({**null_left, **right})

        return result

    def _execute_group_by(self, rows: List[Dict], stmt: SelectStatement) -> List[Dict]:
        """Execute GROUP BY with aggregate functions."""
        groups: Dict[tuple, List[Dict]] = {}

        for row in rows:
            key = tuple(
                self._evaluate_expr(expr, row) for expr in stmt.group_by.columns
            )
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        result = []
        for key, group_rows in groups.items():
            # Apply HAVING
            if stmt.group_by.having:
                # Evaluate with aggregate context
                if not self._evaluate_expr(
                    stmt.group_by.having, group_rows[0], group_rows
                ):
                    continue

            # Build result row with aggregates
            result_row = {}
            for col in stmt.columns:
                alias = col.alias or self._expr_to_string(col.expression)
                result_row[alias] = self._evaluate_expr(
                    col.expression, group_rows[0], group_rows
                )
            result.append(result_row)

        return result

    # INSERT

    def _execute_insert(self, stmt: InsertStatement) -> QueryResult:
        """Execute INSERT statement."""
        table_name = stmt.table

        if not self.schema.has_table(table_name):
            return QueryResult(
                success=False, message=f"Table '{table_name}' does not exist"
            )

        table = self.schema.get_table(table_name)
        existing_rows = self.storage.read_table(table_name)
        inserted_count = 0

        for value_list in stmt.values:
            row = {}

            if stmt.columns:
                # Named columns
                for i, col_name in enumerate(stmt.columns):
                    if i < len(value_list):
                        row[col_name] = self._evaluate_expr(value_list[i], {})
            else:
                # Positional values
                for i, col in enumerate(table.columns):
                    if i < len(value_list):
                        row[col.name] = self._evaluate_expr(value_list[i], {})

            # Validate and coerce types
            validated_row = table.validate_row(row)

            # Check constraints
            ConstraintChecker.check_insert(
                table, validated_row, existing_rows, self.schema
            )

            existing_rows.append(validated_row)
            inserted_count += 1

            # Update indexes
            if table_name in self.indexes:
                pk_col = table.get_primary_key()
                row_id = (
                    validated_row.get(pk_col.name) if pk_col else len(existing_rows) - 1
                )
                self.indexes[table_name].insert(validated_row, row_id)

        self.storage.write_table(table_name, existing_rows)
        self.storage.save_schema(self.schema)

        return QueryResult(
            success=True,
            message=f"Inserted {inserted_count} row(s)",
            row_count=inserted_count,
        )

    # UPDATE

    def _execute_update(self, stmt: UpdateStatement) -> QueryResult:
        """Execute UPDATE statement."""
        table_name = stmt.table

        if not self.schema.has_table(table_name):
            return QueryResult(
                success=False, message=f"Table '{table_name}' does not exist"
            )

        table = self.schema.get_table(table_name)
        rows = self.storage.read_table(table_name)
        pk_col = table.get_primary_key()
        updated_count = 0

        for i, row in enumerate(rows):
            if stmt.where and not self._evaluate_expr(stmt.where, row):
                continue

            updates = {}
            for col_name, value_expr in stmt.assignments:
                updates[col_name] = self._evaluate_expr(value_expr, row)

            # Check constraints
            pk_value = row.get(pk_col.name) if pk_col else i
            ConstraintChecker.check_update(
                table,
                pk_value,
                updates,
                rows,
                pk_col.name if pk_col else "id",
                self.schema,
            )

            # Apply updates
            for col_name, value in updates.items():
                rows[i][col_name] = value

            updated_count += 1

        self.storage.write_table(table_name, rows)

        return QueryResult(
            success=True,
            message=f"Updated {updated_count} row(s)",
            row_count=updated_count,
        )

    # DELETE

    def _execute_delete(self, stmt: DeleteStatement) -> QueryResult:
        """Execute DELETE statement."""
        table_name = stmt.table

        if not self.schema.has_table(table_name):
            return QueryResult(
                success=False, message=f"Table '{table_name}' does not exist"
            )

        rows = self.storage.read_table(table_name)
        original_count = len(rows)

        if stmt.where:
            rows = [row for row in rows if not self._evaluate_expr(stmt.where, row)]
        else:
            rows = []

        deleted_count = original_count - len(rows)
        self.storage.write_table(table_name, rows)

        return QueryResult(
            success=True,
            message=f"Deleted {deleted_count} row(s)",
            row_count=deleted_count,
        )

    # CREATE TABLE

    def _execute_create_table(self, stmt: CreateTableStatement) -> QueryResult:
        """Execute CREATE TABLE statement."""
        table_name = stmt.table

        if self.schema.has_table(table_name):
            return QueryResult(
                success=False, message=f"Table '{table_name}' already exists"
            )

        table = Table(name=table_name)

        for col_def in stmt.columns:
            col_type = parse_column_type(
                f"{col_def.data_type}"
                + (f"({col_def.length})" if col_def.length else "")
            )

            column = Column(
                name=col_def.name,
                data_type=col_type,
                nullable=col_def.nullable,
                primary_key=col_def.primary_key,
                unique=col_def.unique,
                auto_increment=col_def.auto_increment,
                default=(
                    self._evaluate_expr(col_def.default, {})
                    if col_def.default
                    else None
                ),
            )
            table.add_column(column)

        self.schema.add_table(table)
        self.storage.save_schema(self.schema)
        self.storage.create_table(table_name)

        # Create index for primary key
        pk = table.get_primary_key()
        if pk:
            if table_name not in self.indexes:
                self.indexes[table_name] = IndexManager()
            self.indexes[table_name].create_index(pk.name)
            table.indexes.add(pk.name)

        return QueryResult(success=True, message=f"Table '{table_name}' created")

    # DROP TABLE

    def _execute_drop_table(self, stmt: DropTableStatement) -> QueryResult:
        """Execute DROP TABLE statement."""
        table_name = stmt.table

        if not self.schema.has_table(table_name):
            if stmt.if_exists:
                return QueryResult(
                    success=True, message=f"Table '{table_name}' does not exist"
                )
            return QueryResult(
                success=False, message=f"Table '{table_name}' does not exist"
            )

        self.schema.drop_table(table_name)
        self.storage.drop_table(table_name)
        self.storage.save_schema(self.schema)

        if table_name in self.indexes:
            del self.indexes[table_name]

        return QueryResult(success=True, message=f"Table '{table_name}' dropped")

    # CREATE/DROP INDEX

    def _execute_create_index(self, stmt: CreateIndexStatement) -> QueryResult:
        """Execute CREATE INDEX statement."""
        table_name = stmt.table

        if not self.schema.has_table(table_name):
            return QueryResult(
                success=False, message=f"Table '{table_name}' does not exist"
            )

        table = self.schema.get_table(table_name)

        if table_name not in self.indexes:
            self.indexes[table_name] = IndexManager()

        for col_name in stmt.columns:
            self.indexes[table_name].create_index(col_name)
            table.indexes.add(col_name)

        # Rebuild index from existing data
        rows = self.storage.read_table(table_name)
        pk = table.get_primary_key()
        self.indexes[table_name].rebuild_from_rows(rows, pk.name if pk else None)

        self.storage.save_schema(self.schema)

        return QueryResult(
            success=True, message=f"Index '{stmt.name}' created on '{table_name}'"
        )

    def _execute_drop_index(self, stmt: DropIndexStatement) -> QueryResult:
        """Execute DROP INDEX statement."""
        if stmt.table and stmt.table in self.indexes:
            # This is simplified - would need to track index names properly
            return QueryResult(success=True, message=f"Index '{stmt.name}' dropped")
        return QueryResult(success=True, message=f"Index '{stmt.name}' dropped")

    # Expression evaluation

    def _evaluate_expr(
        self, expr: Expression, row: Dict[str, Any], group_rows: List[Dict] = None
    ) -> Any:
        """Evaluate an expression in the context of a row."""
        if expr is None:
            return None

        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, Identifier):
            return row.get(expr.name)

        if isinstance(expr, QualifiedIdentifier):
            return row.get(f"{expr.table}.{expr.column}") or row.get(expr.column)

        if isinstance(expr, Star):
            return "*"

        if isinstance(expr, BinaryOp):
            left = self._evaluate_expr(expr.left, row, group_rows)
            right = self._evaluate_expr(expr.right, row, group_rows)
            return self._apply_binary_op(expr.operator, left, right)

        if isinstance(expr, UnaryOp):
            operand = self._evaluate_expr(expr.operand, row, group_rows)
            if expr.operator == "-":
                return -operand if operand is not None else None
            if expr.operator == "NOT":
                return not operand
            return operand

        if isinstance(expr, FunctionCall):
            return self._evaluate_function(expr, row, group_rows)

        if isinstance(expr, InList):
            value = self._evaluate_expr(expr.value, row, group_rows)
            items = [self._evaluate_expr(item, row, group_rows) for item in expr.items]
            result = value in items
            return not result if expr.negated else result

        if isinstance(expr, Between):
            value = self._evaluate_expr(expr.value, row, group_rows)
            low = self._evaluate_expr(expr.low, row, group_rows)
            high = self._evaluate_expr(expr.high, row, group_rows)
            result = (
                low <= value <= high
                if all(x is not None for x in [value, low, high])
                else False
            )
            return not result if expr.negated else result

        if isinstance(expr, IsNull):
            value = self._evaluate_expr(expr.value, row, group_rows)
            result = value is None
            return not result if expr.negated else result

        if isinstance(expr, Like):
            value = self._evaluate_expr(expr.value, row, group_rows)
            pattern = self._evaluate_expr(expr.pattern, row, group_rows)
            if value is None or pattern is None:
                return False
            # Convert SQL LIKE pattern to regex
            regex = pattern.replace("%", ".*").replace("_", ".")
            result = bool(re.match(f"^{regex}$", str(value), re.IGNORECASE))
            return not result if expr.negated else result

        return None

    def _apply_binary_op(self, op: str, left: Any, right: Any) -> Any:
        """Apply a binary operator."""
        op = op.upper()

        if op in ("=", "=="):
            return left == right
        if op in ("!=", "<>"):
            return left != right
        if op == "<":
            return left < right if left is not None and right is not None else False
        if op == "<=":
            return left <= right if left is not None and right is not None else False
        if op == ">":
            return left > right if left is not None and right is not None else False
        if op == ">=":
            return left >= right if left is not None and right is not None else False
        if op == "AND":
            return bool(left) and bool(right)
        if op == "OR":
            return bool(left) or bool(right)
        if op == "+":
            return left + right if left is not None and right is not None else None
        if op == "-":
            return left - right if left is not None and right is not None else None
        if op == "*":
            return left * right if left is not None and right is not None else None
        if op == "/":
            return (
                left / right
                if left is not None and right is not None and right != 0
                else None
            )
        if op == "%":
            return (
                left % right
                if left is not None and right is not None and right != 0
                else None
            )

        return None

    def _evaluate_function(
        self, func: FunctionCall, row: Dict[str, Any], group_rows: List[Dict] = None
    ) -> Any:
        """Evaluate a function call."""
        name = func.name.upper()

        # Aggregate functions
        if name in ("COUNT", "SUM", "AVG", "MIN", "MAX") and group_rows:
            values = []
            for r in group_rows:
                if func.arguments:
                    arg = func.arguments[0]
                    if isinstance(arg, Star):
                        values.append(1)
                    else:
                        val = self._evaluate_expr(arg, r)
                        if val is not None:
                            values.append(val)
                else:
                    values.append(1)

            if name == "COUNT":
                return len(values)
            if name == "SUM":
                return sum(values) if values else 0
            if name == "AVG":
                return sum(values) / len(values) if values else None
            if name == "MIN":
                return min(values) if values else None
            if name == "MAX":
                return max(values) if values else None

        # Non-aggregate or single-row context
        if name == "COUNT":
            return 1

        # Scalar functions
        args = [self._evaluate_expr(arg, row, group_rows) for arg in func.arguments]

        if name == "UPPER" and args:
            return str(args[0]).upper() if args[0] else None
        if name == "LOWER" and args:
            return str(args[0]).lower() if args[0] else None
        if name == "LENGTH" and args:
            return len(str(args[0])) if args[0] else None
        if name == "COALESCE":
            for arg in args:
                if arg is not None:
                    return arg
            return None

        return None

    def _expr_to_string(self, expr: Expression) -> str:
        """Convert expression to string for column naming."""
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, QualifiedIdentifier):
            return f"{expr.table}.{expr.column}"
        if isinstance(expr, Literal):
            return str(expr.value)
        if isinstance(expr, FunctionCall):
            return f"{expr.name}(...)"
        if isinstance(expr, Star):
            return "*"
        return "?"
