"""
PesapalDB Database Engine

Main entry point for the database.
"""

from typing import Any, Dict, List, Optional

from .schema import Schema
from .storage import StorageEngine
from .indexing import IndexManager
from .parser import Parser
from .executor import QueryExecutor
from .executor.executor import QueryResult


class Database:
    """Main database class - entry point for all operations."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.storage = StorageEngine(data_dir)

        # Load existing schema or create new
        self.schema = self.storage.load_schema() or Schema()

        # Initialize indexes for tables
        self.indexes: Dict[str, IndexManager] = {}
        for table_name, table in self.schema.tables.items():
            self.indexes[table_name] = IndexManager()
            pk = table.get_primary_key()
            if pk:
                self.indexes[table_name].create_index(pk.name)
                # Rebuild index from data
                rows = self.storage.read_table(table_name)
                self.indexes[table_name].rebuild_from_rows(rows, pk.name)

        # Create executor
        self.executor = QueryExecutor(self.schema, self.storage, self.indexes)

    def execute(self, sql: str) -> QueryResult:
        """Execute a SQL query string."""
        parser = Parser(sql)
        statements = parser.parse()

        if not statements:
            return QueryResult(success=False, message="No valid SQL statement")

        # Execute all statements, return last result
        result = None
        for stmt in statements:
            result = self.executor.execute(stmt)
            if not result.success:
                return result

        return result

    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute query and return dictionary result."""
        result = self.execute(sql)
        return result.to_dict()

    def get_tables(self) -> List[str]:
        """Get list of table names."""
        return list(self.schema.tables.keys())

    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a table."""
        table = self.schema.get_table(table_name)
        if not table:
            return None

        return {
            "name": table.name,
            "columns": [
                {
                    "name": col.name,
                    "type": col.data_type[0].value,
                    "length": col.data_type[1],
                    "nullable": col.nullable,
                    "primary_key": col.primary_key,
                    "unique": col.unique,
                    "auto_increment": col.auto_increment or False,
                }
                for col in table.columns
            ],
            "row_count": len(self.storage.read_table(table_name)),
            "indexes": list(table.indexes),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        storage_stats = self.storage.get_stats()

        tables_info = {}
        for name in self.schema.tables:
            rows = self.storage.read_table(name)
            tables_info[name] = len(rows)

        return {
            **storage_stats,
            "tables": tables_info,
        }

    def reset(self) -> None:
        """Reset the database (delete all data)."""
        self.storage.reset()
        self.schema = Schema()
        self.indexes = {}
        self.executor = QueryExecutor(self.schema, self.storage, self.indexes)
