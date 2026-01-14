"""
PesapalDB Constraints

Implements database constraints: PRIMARY KEY, UNIQUE, NOT NULL, FOREIGN KEY.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .schema import Table, Schema


class ConstraintViolation(Exception):
    """Exception raised when a constraint is violated."""
    pass


class Constraint(ABC):
    """Base class for database constraints."""
    
    @abstractmethod
    def validate(
        self, 
        value: Any, 
        existing_values: List[Any] = None,
        **context
    ) -> None:
        """
        Validate a value against this constraint.
        
        Raises:
            ConstraintViolation: If the constraint is violated
        """
        pass


class PrimaryKeyConstraint(Constraint):
    """Primary key constraint - ensures non-null unique values."""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
    
    def validate(
        self, 
        value: Any, 
        existing_values: List[Any] = None,
        **context
    ) -> None:
        if value is None:
            raise ConstraintViolation(
                f"PRIMARY KEY constraint violated: '{self.column_name}' cannot be NULL"
            )
        if existing_values and value in existing_values:
            raise ConstraintViolation(
                f"PRIMARY KEY constraint violated: duplicate value '{value}' for column '{self.column_name}'"
            )


class UniqueConstraint(Constraint):
    """Unique constraint - ensures unique values (NULL allowed)."""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
    
    def validate(
        self, 
        value: Any, 
        existing_values: List[Any] = None,
        **context
    ) -> None:
        if value is not None and existing_values and value in existing_values:
            raise ConstraintViolation(
                f"UNIQUE constraint violated: duplicate value '{value}' for column '{self.column_name}'"
            )


class NotNullConstraint(Constraint):
    """Not null constraint - ensures non-null values."""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
    
    def validate(
        self, 
        value: Any, 
        existing_values: List[Any] = None,
        **context
    ) -> None:
        if value is None:
            raise ConstraintViolation(
                f"NOT NULL constraint violated: '{self.column_name}' cannot be NULL"
            )


class ForeignKeyConstraint(Constraint):
    """Foreign key constraint - ensures referential integrity."""
    
    def __init__(
        self, 
        column_name: str, 
        ref_table: str, 
        ref_column: str
    ):
        self.column_name = column_name
        self.ref_table = ref_table
        self.ref_column = ref_column
    
    def validate(
        self, 
        value: Any, 
        existing_values: List[Any] = None,
        ref_values: List[Any] = None,
        **context
    ) -> None:
        if value is None:
            return  # NULL foreign keys are typically allowed
        if ref_values is None:
            return  # Skip if no reference values provided
        if value not in ref_values:
            raise ConstraintViolation(
                f"FOREIGN KEY constraint violated: value '{value}' not found in "
                f"'{self.ref_table}.{self.ref_column}'"
            )


class ConstraintChecker:
    """Utility class for checking constraints on table operations."""
    
    @staticmethod
    def check_insert(
        table: "Table",
        row: Dict[str, Any],
        existing_rows: List[Dict[str, Any]],
        schema: "Schema" = None
    ) -> None:
        """
        Check all constraints for an INSERT operation.
        
        Raises:
            ConstraintViolation: If any constraint is violated
        """
        for col in table.columns:
            value = row.get(col.name)
            
            # Get existing values for this column
            existing_values = [r.get(col.name) for r in existing_rows]
            
            # Check NOT NULL
            if not col.nullable:
                NotNullConstraint(col.name).validate(value)
            
            # Check PRIMARY KEY
            if col.primary_key:
                PrimaryKeyConstraint(col.name).validate(value, existing_values)
            
            # Check UNIQUE
            elif col.unique:
                UniqueConstraint(col.name).validate(value, existing_values)
    
    @staticmethod
    def check_update(
        table: "Table",
        row_id: Any,
        updates: Dict[str, Any],
        existing_rows: List[Dict[str, Any]],
        pk_column: str,
        schema: "Schema" = None
    ) -> None:
        """
        Check all constraints for an UPDATE operation.
        
        Raises:
            ConstraintViolation: If any constraint is violated
        """
        # Filter out the row being updated
        other_rows = [r for r in existing_rows if r.get(pk_column) != row_id]
        
        for col in table.columns:
            if col.name not in updates:
                continue
                
            value = updates[col.name]
            existing_values = [r.get(col.name) for r in other_rows]
            
            # Check NOT NULL
            if not col.nullable:
                NotNullConstraint(col.name).validate(value)
            
            # Check PRIMARY KEY
            if col.primary_key:
                PrimaryKeyConstraint(col.name).validate(value, existing_values)
            
            # Check UNIQUE
            elif col.unique:
                UniqueConstraint(col.name).validate(value, existing_values)
