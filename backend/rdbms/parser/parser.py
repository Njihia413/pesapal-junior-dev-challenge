"""
PesapalDB SQL Parser

Recursive descent parser for SQL statements.
"""

from typing import List, Optional

from .lexer import Lexer, Token, TokenType
from .ast import (
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


class ParseError(Exception):
    """Parser error with location information."""

    def __init__(self, message: str, token: Token = None):
        self.token = token
        if token:
            super().__init__(f"{message} at line {token.line}, column {token.column}")
        else:
            super().__init__(message)


class Parser:
    """SQL Parser - converts tokens to AST."""

    def __init__(self, sql: str):
        self.lexer = Lexer(sql)
        self.tokens = self.lexer.tokenize()
        self.pos = 0

    @property
    def current(self) -> Token:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def peek(self, offset: int = 1) -> Token:
        """Peek at token at offset."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]

    def advance(self) -> Token:
        """Advance to next token and return current."""
        token = self.current
        self.pos += 1
        return token

    def match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the types."""
        return self.current.type in types

    def consume(self, token_type: TokenType, message: str = None) -> Token:
        """Consume a token of the expected type."""
        if self.current.type != token_type:
            msg = message or f"Expected {token_type.name}, got {self.current.type.name}"
            raise ParseError(msg, self.current)
        return self.advance()

    def parse(self) -> List[Statement]:
        """Parse all statements."""
        statements = []
        while not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            # Skip optional semicolons
            while self.match(TokenType.SEMICOLON):
                self.advance()
        return statements

    def parse_statement(self) -> Optional[Statement]:
        """Parse a single statement."""
        if self.match(TokenType.SELECT):
            return self.parse_select()
        elif self.match(TokenType.INSERT):
            return self.parse_insert()
        elif self.match(TokenType.UPDATE):
            return self.parse_update()
        elif self.match(TokenType.DELETE):
            return self.parse_delete()
        elif self.match(TokenType.CREATE):
            return self.parse_create()
        elif self.match(TokenType.DROP):
            return self.parse_drop()
        else:
            raise ParseError(f"Unexpected token: {self.current.value}", self.current)

    # SELECT

    def parse_select(self) -> SelectStatement:
        """Parse SELECT statement."""
        self.consume(TokenType.SELECT)

        stmt = SelectStatement()

        # DISTINCT
        if self.match(TokenType.DISTINCT):
            self.advance()
            stmt.distinct = True

        # Columns
        stmt.columns = self.parse_select_columns()

        # FROM
        if self.match(TokenType.FROM):
            self.advance()
            stmt.from_table = self.parse_table_ref()

            # JOINs
            while self.match(
                TokenType.JOIN,
                TokenType.LEFT,
                TokenType.RIGHT,
                TokenType.INNER,
                TokenType.FULL,
                TokenType.CROSS,
            ):
                stmt.joins.append(self.parse_join())

        # WHERE
        if self.match(TokenType.WHERE):
            self.advance()
            stmt.where = self.parse_expression()

        # GROUP BY
        if self.match(TokenType.GROUP):
            self.advance()
            self.consume(TokenType.BY)
            stmt.group_by = self.parse_group_by()

        # ORDER BY
        if self.match(TokenType.ORDER):
            self.advance()
            self.consume(TokenType.BY)
            stmt.order_by = self.parse_order_by()

        # LIMIT
        if self.match(TokenType.LIMIT):
            self.advance()
            limit_token = self.consume(TokenType.INTEGER)
            stmt.limit = limit_token.value

            # OFFSET
            if self.match(TokenType.OFFSET):
                self.advance()
                offset_token = self.consume(TokenType.INTEGER)
                stmt.offset = offset_token.value

        return stmt

    def parse_select_columns(self) -> List[SelectColumn]:
        """Parse SELECT column list."""
        columns = []

        while True:
            col = self.parse_select_column()
            columns.append(col)

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        return columns

    def parse_select_column(self) -> SelectColumn:
        """Parse a single SELECT column."""
        # Check for *
        if self.match(TokenType.STAR):
            self.advance()
            return SelectColumn(expression=Star())

        # Check for table.*
        if self.match(TokenType.IDENTIFIER) and self.peek().type == TokenType.DOT:
            if self.peek(2).type == TokenType.STAR:
                table = self.advance().value
                self.advance()  # .
                self.advance()  # *
                return SelectColumn(expression=Star(table=table))

        expr = self.parse_expression()
        alias = None

        if self.match(TokenType.AS):
            self.advance()
            alias = self.consume(TokenType.IDENTIFIER).value
        elif self.match(TokenType.IDENTIFIER):
            # Implicit alias
            alias = self.advance().value

        return SelectColumn(expression=expr, alias=alias)

    def parse_table_ref(self) -> TableRef:
        """Parse a table reference."""
        name = self.consume(TokenType.IDENTIFIER).value
        alias = None

        if self.match(TokenType.AS):
            self.advance()
            alias = self.consume(TokenType.IDENTIFIER).value
        elif self.match(TokenType.IDENTIFIER):
            alias = self.advance().value

        return TableRef(name=name, alias=alias)

    def parse_join(self) -> JoinClause:
        """Parse a JOIN clause."""
        join_type = "INNER"

        if self.match(TokenType.LEFT):
            self.advance()
            join_type = "LEFT"
            if self.match(TokenType.OUTER):
                self.advance()
        elif self.match(TokenType.RIGHT):
            self.advance()
            join_type = "RIGHT"
            if self.match(TokenType.OUTER):
                self.advance()
        elif self.match(TokenType.FULL):
            self.advance()
            join_type = "FULL"
            if self.match(TokenType.OUTER):
                self.advance()
        elif self.match(TokenType.CROSS):
            self.advance()
            join_type = "CROSS"
        elif self.match(TokenType.INNER):
            self.advance()

        self.consume(TokenType.JOIN)
        table = self.parse_table_ref()

        condition = None
        if self.match(TokenType.ON):
            self.advance()
            condition = self.parse_expression()

        return JoinClause(join_type=join_type, table=table, condition=condition)

    def parse_group_by(self) -> GroupByClause:
        """Parse GROUP BY clause."""
        columns = []

        while True:
            columns.append(self.parse_expression())
            if not self.match(TokenType.COMMA):
                break
            self.advance()

        having = None
        if self.match(TokenType.HAVING):
            self.advance()
            having = self.parse_expression()

        return GroupByClause(columns=columns, having=having)

    def parse_order_by(self) -> List[OrderByItem]:
        """Parse ORDER BY clause."""
        items = []

        while True:
            expr = self.parse_expression()
            ascending = True

            if self.match(TokenType.ASC):
                self.advance()
            elif self.match(TokenType.DESC):
                self.advance()
                ascending = False

            items.append(OrderByItem(expression=expr, ascending=ascending))

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        return items

    # INSERT

    def parse_insert(self) -> InsertStatement:
        """Parse INSERT statement."""
        self.consume(TokenType.INSERT)
        self.consume(TokenType.INTO)

        table = self.consume(TokenType.IDENTIFIER).value
        columns = []

        # Optional column list
        if self.match(TokenType.LPAREN):
            self.advance()
            while True:
                columns.append(self.consume(TokenType.IDENTIFIER).value)
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
            self.consume(TokenType.RPAREN)

        # VALUES
        self.consume(TokenType.VALUES)

        values = []
        while True:
            self.consume(TokenType.LPAREN)
            row_values = []
            while True:
                row_values.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
            self.consume(TokenType.RPAREN)
            values.append(row_values)

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        return InsertStatement(table=table, columns=columns, values=values)

    # UPDATE

    def parse_update(self) -> UpdateStatement:
        """Parse UPDATE statement."""
        self.consume(TokenType.UPDATE)
        table = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.SET)

        assignments = []
        while True:
            column = self.consume(TokenType.IDENTIFIER).value
            self.consume(TokenType.EQUALS)
            value = self.parse_expression()
            assignments.append((column, value))

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        where = None
        if self.match(TokenType.WHERE):
            self.advance()
            where = self.parse_expression()

        return UpdateStatement(table=table, assignments=assignments, where=where)

    # DELETE

    def parse_delete(self) -> DeleteStatement:
        """Parse DELETE statement."""
        self.consume(TokenType.DELETE)
        self.consume(TokenType.FROM)
        table = self.consume(TokenType.IDENTIFIER).value

        where = None
        if self.match(TokenType.WHERE):
            self.advance()
            where = self.parse_expression()

        return DeleteStatement(table=table, where=where)

    # CREATE

    def parse_create(self) -> Statement:
        """Parse CREATE statement."""
        self.consume(TokenType.CREATE)

        if self.match(TokenType.TABLE):
            return self.parse_create_table()
        elif self.match(TokenType.INDEX) or self.match(TokenType.UNIQUE):
            return self.parse_create_index()
        else:
            raise ParseError("Expected TABLE or INDEX", self.current)

    def parse_create_table(self) -> CreateTableStatement:
        """Parse CREATE TABLE statement."""
        self.consume(TokenType.TABLE)

        table = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.LPAREN)

        columns = []
        while True:
            col = self.parse_column_def()
            columns.append(col)

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        self.consume(TokenType.RPAREN)

        return CreateTableStatement(table=table, columns=columns)

    def parse_column_def(self) -> ColumnDef:
        """Parse column definition."""
        name = self.consume(TokenType.IDENTIFIER).value

        # Data type
        data_type = self.parse_data_type()
        length = None

        if self.match(TokenType.LPAREN):
            self.advance()
            length = self.consume(TokenType.INTEGER).value
            self.consume(TokenType.RPAREN)

        col = ColumnDef(name=name, data_type=data_type, length=length)

        # Constraints
        while True:
            if self.match(TokenType.PRIMARY):
                self.advance()
                self.consume(TokenType.KEY)
                col.primary_key = True
                col.nullable = False
            elif self.match(TokenType.UNIQUE):
                self.advance()
                col.unique = True
            elif self.match(TokenType.NOT):
                self.advance()
                self.consume(TokenType.NULL)
                col.nullable = False
            elif self.match(TokenType.NULL):
                self.advance()
                col.nullable = True
            elif self.match(TokenType.DEFAULT):
                self.advance()
                col.default = self.parse_primary_expression()
            elif self.match(TokenType.AUTO_INCREMENT):
                self.advance()
                col.auto_increment = True
                col.primary_key = True
                col.nullable = False
            elif self.match(TokenType.REFERENCES):
                self.advance()
                ref_table = self.consume(TokenType.IDENTIFIER).value
                self.consume(TokenType.LPAREN)
                ref_column = self.consume(TokenType.IDENTIFIER).value
                self.consume(TokenType.RPAREN)
                col.references = (ref_table, ref_column)
            else:
                break

        return col

    def parse_data_type(self) -> str:
        """Parse a data type."""
        type_tokens = [
            TokenType.INT,
            TokenType.INTEGER_TYPE,
            TokenType.FLOAT_TYPE,
            TokenType.VARCHAR,
            TokenType.BOOLEAN,
            TokenType.DATE,
            TokenType.TIMESTAMP,
        ]

        if not any(self.match(t) for t in type_tokens):
            raise ParseError("Expected data type", self.current)

        token = self.advance()

        # Normalize type names
        type_map = {
            TokenType.INT: "INTEGER",
            TokenType.INTEGER_TYPE: "INTEGER",
            TokenType.FLOAT_TYPE: "FLOAT",
            TokenType.VARCHAR: "VARCHAR",
            TokenType.BOOLEAN: "BOOLEAN",
            TokenType.DATE: "DATE",
            TokenType.TIMESTAMP: "TIMESTAMP",
        }

        return type_map.get(token.type, token.value)

    def parse_create_index(self) -> CreateIndexStatement:
        """Parse CREATE INDEX statement."""
        unique = False
        if self.match(TokenType.UNIQUE):
            self.advance()
            unique = True

        self.consume(TokenType.INDEX)
        name = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.ON)
        table = self.consume(TokenType.IDENTIFIER).value

        self.consume(TokenType.LPAREN)
        columns = []
        while True:
            columns.append(self.consume(TokenType.IDENTIFIER).value)
            if not self.match(TokenType.COMMA):
                break
            self.advance()
        self.consume(TokenType.RPAREN)

        return CreateIndexStatement(
            name=name, table=table, columns=columns, unique=unique
        )

    # DROP

    def parse_drop(self) -> Statement:
        """Parse DROP statement."""
        self.consume(TokenType.DROP)

        if self.match(TokenType.TABLE):
            self.advance()
            table = self.consume(TokenType.IDENTIFIER).value
            return DropTableStatement(table=table)
        elif self.match(TokenType.INDEX):
            self.advance()
            name = self.consume(TokenType.IDENTIFIER).value
            table = None
            if self.match(TokenType.ON):
                self.advance()
                table = self.consume(TokenType.IDENTIFIER).value
            return DropIndexStatement(name=name, table=table)
        else:
            raise ParseError("Expected TABLE or INDEX", self.current)

    # Expressions

    def parse_expression(self) -> Expression:
        """Parse an expression."""
        return self.parse_or()

    def parse_or(self) -> Expression:
        """Parse OR expression."""
        left = self.parse_and()

        while self.match(TokenType.OR):
            self.advance()
            right = self.parse_and()
            left = BinaryOp(left=left, operator="OR", right=right)

        return left

    def parse_and(self) -> Expression:
        """Parse AND expression."""
        left = self.parse_not()

        while self.match(TokenType.AND):
            self.advance()
            right = self.parse_not()
            left = BinaryOp(left=left, operator="AND", right=right)

        return left

    def parse_not(self) -> Expression:
        """Parse NOT expression."""
        if self.match(TokenType.NOT):
            self.advance()
            operand = self.parse_not()
            return UnaryOp(operator="NOT", operand=operand)

        return self.parse_comparison()

    def parse_comparison(self) -> Expression:
        """Parse comparison expression."""
        left = self.parse_additive()

        # IS NULL / IS NOT NULL
        if self.match(TokenType.IS):
            self.advance()
            negated = False
            if self.match(TokenType.NOT):
                self.advance()
                negated = True
            self.consume(TokenType.NULL)
            return IsNull(value=left, negated=negated)

        # IN
        if self.match(TokenType.IN) or (
            self.match(TokenType.NOT) and self.peek().type == TokenType.IN
        ):
            negated = False
            if self.match(TokenType.NOT):
                self.advance()
                negated = True
            self.consume(TokenType.IN)
            self.consume(TokenType.LPAREN)
            items = []
            while True:
                items.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
            self.consume(TokenType.RPAREN)
            return InList(value=left, items=items, negated=negated)

        # BETWEEN
        if self.match(TokenType.BETWEEN) or (
            self.match(TokenType.NOT) and self.peek().type == TokenType.BETWEEN
        ):
            negated = False
            if self.match(TokenType.NOT):
                self.advance()
                negated = True
            self.consume(TokenType.BETWEEN)
            low = self.parse_additive()
            self.consume(TokenType.AND)
            high = self.parse_additive()
            return Between(value=left, low=low, high=high, negated=negated)

        # LIKE
        if self.match(TokenType.LIKE) or (
            self.match(TokenType.NOT) and self.peek().type == TokenType.LIKE
        ):
            negated = False
            if self.match(TokenType.NOT):
                self.advance()
                negated = True
            self.consume(TokenType.LIKE)
            pattern = self.parse_additive()
            return Like(value=left, pattern=pattern, negated=negated)

        # Comparison operators
        if self.match(
            TokenType.EQUALS,
            TokenType.NOT_EQUALS,
            TokenType.LESS_THAN,
            TokenType.LESS_THAN_EQUALS,
            TokenType.GREATER_THAN,
            TokenType.GREATER_THAN_EQUALS,
        ):
            op = self.advance().value
            right = self.parse_additive()
            return BinaryOp(left=left, operator=op, right=right)

        return left

    def parse_additive(self) -> Expression:
        """Parse additive expression (+, -)."""
        left = self.parse_multiplicative()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinaryOp(left=left, operator=op, right=right)

        return left

    def parse_multiplicative(self) -> Expression:
        """Parse multiplicative expression (*, /, %)."""
        left = self.parse_unary()

        while self.match(TokenType.STAR, TokenType.DIVIDE, TokenType.MODULO):
            op = self.advance().value
            right = self.parse_unary()
            left = BinaryOp(left=left, operator=op, right=right)

        return left

    def parse_unary(self) -> Expression:
        """Parse unary expression."""
        if self.match(TokenType.MINUS):
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(operator="-", operand=operand)

        return self.parse_primary_expression()

    def parse_primary_expression(self) -> Expression:
        """Parse primary expression."""
        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return expr

        # Literals
        if self.match(TokenType.INTEGER):
            return Literal(value=self.advance().value)
        if self.match(TokenType.FLOAT):
            return Literal(value=self.advance().value)
        if self.match(TokenType.STRING):
            return Literal(value=self.advance().value)
        if self.match(TokenType.TRUE):
            self.advance()
            return Literal(value=True)
        if self.match(TokenType.FALSE):
            self.advance()
            return Literal(value=False)
        if self.match(TokenType.NULL):
            self.advance()
            return Literal(value=None)

        # Star
        if self.match(TokenType.STAR):
            self.advance()
            return Star()

        # Identifier or function call
        if self.match(TokenType.IDENTIFIER):
            name = self.advance().value

            # Function call
            if self.match(TokenType.LPAREN):
                self.advance()
                args = []
                distinct = False

                if self.match(TokenType.DISTINCT):
                    self.advance()
                    distinct = True

                if not self.match(TokenType.RPAREN):
                    while True:
                        if self.match(TokenType.STAR):
                            self.advance()
                            args.append(Star())
                        else:
                            args.append(self.parse_expression())
                        if not self.match(TokenType.COMMA):
                            break
                        self.advance()

                self.consume(TokenType.RPAREN)
                return FunctionCall(
                    name=name.upper(), arguments=args, distinct=distinct
                )

            # Qualified identifier (table.column)
            if self.match(TokenType.DOT):
                self.advance()
                column = self.consume(TokenType.IDENTIFIER).value
                return QualifiedIdentifier(table=name, column=column)

            return Identifier(name=name)

        raise ParseError(
            f"Unexpected token in expression: {self.current.value}", self.current
        )
