"""
PesapalDB Data Types

Defines supported data types and type validation for the database.
"""

from enum import Enum
from typing import Any, Optional, Tuple
from datetime import datetime, date


class DataType(Enum):
    """Supported data types in PesapalDB."""
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    VARCHAR = "VARCHAR"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"


# Type alias for column type with optional length
ColumnType = Tuple[DataType, Optional[int]]


class TypeValidator:
    """Validates and coerces values to their expected data types."""

    @staticmethod
    def validate(value: Any, column_type: ColumnType, nullable: bool = True) -> Any:
        """
        Validate and coerce a value to the specified type.
        
        Args:
            value: The value to validate
            column_type: Tuple of (DataType, optional_length)
            nullable: Whether NULL values are allowed
            
        Returns:
            The coerced value
            
        Raises:
            ValueError: If validation fails
        """
        data_type, length = column_type

        # Handle NULL values
        if value is None:
            if not nullable:
                raise ValueError("NULL value not allowed for non-nullable column")
            return None

        # Type-specific validation
        if data_type == DataType.INTEGER:
            return TypeValidator._validate_integer(value)
        elif data_type == DataType.FLOAT:
            return TypeValidator._validate_float(value)
        elif data_type == DataType.VARCHAR:
            return TypeValidator._validate_varchar(value, length)
        elif data_type == DataType.BOOLEAN:
            return TypeValidator._validate_boolean(value)
        elif data_type == DataType.DATE:
            return TypeValidator._validate_date(value)
        elif data_type == DataType.TIMESTAMP:
            return TypeValidator._validate_timestamp(value)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    @staticmethod
    def _validate_integer(value: Any) -> int:
        """Validate and convert to integer."""
        if isinstance(value, bool):
            raise ValueError(f"Cannot convert boolean to INTEGER")
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to INTEGER")
        raise ValueError(f"Cannot convert {type(value).__name__} to INTEGER")

    @staticmethod
    def _validate_float(value: Any) -> float:
        """Validate and convert to float."""
        if isinstance(value, bool):
            raise ValueError(f"Cannot convert boolean to FLOAT")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to FLOAT")
        raise ValueError(f"Cannot convert {type(value).__name__} to FLOAT")

    @staticmethod
    def _validate_varchar(value: Any, max_length: Optional[int]) -> str:
        """Validate and convert to string with optional length check."""
        str_value = str(value)
        if max_length is not None and len(str_value) > max_length:
            raise ValueError(
                f"String exceeds maximum length of {max_length}: got {len(str_value)}"
            )
        return str_value

    @staticmethod
    def _validate_boolean(value: Any) -> bool:
        """Validate and convert to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            lower = value.lower()
            if lower in ('true', '1', 'yes', 'on'):
                return True
            if lower in ('false', '0', 'no', 'off'):
                return False
            raise ValueError(f"Cannot convert '{value}' to BOOLEAN")
        raise ValueError(f"Cannot convert {type(value).__name__} to BOOLEAN")

    @staticmethod
    def _validate_date(value: Any) -> str:
        """Validate and convert to date string (YYYY-MM-DD)."""
        if isinstance(value, date) and not isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, str):
            try:
                parsed = datetime.strptime(value, "%Y-%m-%d")
                return parsed.date().isoformat()
            except ValueError:
                raise ValueError(f"Invalid date format '{value}', expected YYYY-MM-DD")
        raise ValueError(f"Cannot convert {type(value).__name__} to DATE")

    @staticmethod
    def _validate_timestamp(value: Any) -> str:
        """Validate and convert to timestamp string."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f",
            ]
            for fmt in formats:
                try:
                    parsed = datetime.strptime(value, fmt)
                    return parsed.isoformat()
                except ValueError:
                    continue
            raise ValueError(f"Invalid timestamp format '{value}'")
        raise ValueError(f"Cannot convert {type(value).__name__} to TIMESTAMP")


def parse_column_type(type_str: str) -> ColumnType:
    """
    Parse a type string like 'VARCHAR(255)' or 'INTEGER' into a ColumnType.
    
    Args:
        type_str: The type string to parse
        
    Returns:
        Tuple of (DataType, optional_length)
    """
    type_str = type_str.upper().strip()
    
    # Check for parameterized types like VARCHAR(255)
    if '(' in type_str:
        base_type = type_str[:type_str.index('(')]
        length_str = type_str[type_str.index('(')+1:type_str.index(')')]
        try:
            length = int(length_str)
        except ValueError:
            raise ValueError(f"Invalid type length: {length_str}")
        return (DataType[base_type], length)
    
    return (DataType[type_str], None)
