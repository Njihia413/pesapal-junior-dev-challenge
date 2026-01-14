"""
PesapalDB Schema Management

Defines Column, Table, and Schema classes for managing database structure.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from .types import DataType, ColumnType, parse_column_type


@dataclass
class Column:
    """Represents a column in a table."""
    name: str
    data_type: ColumnType
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    auto_increment: bool = False
    default: Any = None
    
    def __post_init__(self):
        """Validate column configuration."""
        if self.primary_key:
            self.nullable = False
            self.unique = True
        if self.auto_increment:
            if self.data_type[0] != DataType.INTEGER:
                raise ValueError("AUTO_INCREMENT only valid for INTEGER columns")
            self.primary_key = True
            self.nullable = False
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert column to dictionary for serialization."""
        return {
            "name": self.name,
            "data_type": self.data_type[0].value,
            "length": self.data_type[1],
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "unique": self.unique,
            "auto_increment": self.auto_increment,
            "default": self.default,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Column":
        """Create column from dictionary."""
        data_type = (DataType(data["data_type"]), data.get("length"))
        return cls(
            name=data["name"],
            data_type=data_type,
            nullable=data.get("nullable", True),
            primary_key=data.get("primary_key", False),
            unique=data.get("unique", False),
            auto_increment=data.get("auto_increment", False),
            default=data.get("default"),
        )


@dataclass
class Table:
    """Represents a database table."""
    name: str
    columns: List[Column] = field(default_factory=list)
    indexes: Set[str] = field(default_factory=set)
    _auto_increment_counters: Dict[str, int] = field(default_factory=dict)
    
    def add_column(self, column: Column) -> None:
        """Add a column to the table."""
        if any(c.name == column.name for c in self.columns):
            raise ValueError(f"Column '{column.name}' already exists in table '{self.name}'")
        self.columns.append(column)
        
    def get_column(self, name: str) -> Optional[Column]:
        """Get a column by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None
    
    def get_primary_key(self) -> Optional[Column]:
        """Get the primary key column if any."""
        for col in self.columns:
            if col.primary_key:
                return col
        return None
    
    def get_next_auto_increment(self, column_name: str) -> int:
        """Get the next auto increment value for a column."""
        current = self._auto_increment_counters.get(column_name, 0)
        self._auto_increment_counters[column_name] = current + 1
        return current + 1
    
    def update_auto_increment(self, column_name: str, value: int) -> None:
        """Update auto increment counter if value is higher."""
        current = self._auto_increment_counters.get(column_name, 0)
        if value > current:
            self._auto_increment_counters[column_name] = value
    
    def validate_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a row against the table schema.
        Returns the validated/coerced row.
        """
        from .types import TypeValidator
        
        validated = {}
        for col in self.columns:
            value = row.get(col.name)
            
            # Handle auto increment
            if col.auto_increment and value is None:
                value = self.get_next_auto_increment(col.name)
            
            # Handle default values
            if value is None and col.default is not None:
                value = col.default
                
            # Validate type
            validated[col.name] = TypeValidator.validate(
                value, col.data_type, col.nullable
            )
            
            # Track auto increment values
            if col.auto_increment and validated[col.name] is not None:
                self.update_auto_increment(col.name, validated[col.name])
                
        return validated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert table to dictionary for serialization."""
        return {
            "name": self.name,
            "columns": [c.to_dict() for c in self.columns],
            "indexes": list(self.indexes),
            "auto_increment_counters": self._auto_increment_counters,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Table":
        """Create table from dictionary."""
        table = cls(
            name=data["name"],
            columns=[Column.from_dict(c) for c in data.get("columns", [])],
            indexes=set(data.get("indexes", [])),
        )
        table._auto_increment_counters = data.get("auto_increment_counters", {})
        return table


@dataclass
class Schema:
    """Represents the database schema containing all tables."""
    name: str = "default"
    tables: Dict[str, Table] = field(default_factory=dict)
    
    def add_table(self, table: Table) -> None:
        """Add a table to the schema."""
        if table.name in self.tables:
            raise ValueError(f"Table '{table.name}' already exists")
        self.tables[table.name] = table
        
    def drop_table(self, name: str) -> None:
        """Remove a table from the schema."""
        if name not in self.tables:
            raise ValueError(f"Table '{name}' does not exist")
        del self.tables[name]
        
    def get_table(self, name: str) -> Optional[Table]:
        """Get a table by name."""
        return self.tables.get(name)
    
    def has_table(self, name: str) -> bool:
        """Check if a table exists."""
        return name in self.tables
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary for serialization."""
        return {
            "name": self.name,
            "tables": {name: t.to_dict() for name, t in self.tables.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schema":
        """Create schema from dictionary."""
        schema = cls(name=data.get("name", "default"))
        for name, table_data in data.get("tables", {}).items():
            schema.tables[name] = Table.from_dict(table_data)
        return schema
