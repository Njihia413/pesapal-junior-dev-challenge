"""
PesapalDB Storage Engine

Implements file-based persistence using JSON files.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from .schema import Schema


class StorageEngine:
    """Handles file-based persistence for the database."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_table_path(self, table_name: str) -> str:
        """Get the file path for a table's data."""
        return os.path.join(self.data_dir, f"{table_name}.json")

    def _get_schema_path(self) -> str:
        """Get the file path for the schema."""
        return os.path.join(self.data_dir, "_schema.json")

    def _get_metadata_path(self) -> str:
        """Get the file path for metadata."""
        return os.path.join(self.data_dir, "_metadata.json")

    def _get_index_path(self, table_name: str, column_name: str) -> str:
        """Get the file path for an index."""
        return os.path.join(self.data_dir, f"_idx_{table_name}_{column_name}.json")

    # Schema operations

    def save_schema(self, schema: Schema) -> None:
        """Save the schema to disk."""
        with open(self._get_schema_path(), "w") as f:
            json.dump(schema.to_dict(), f, indent=2)
        self._update_metadata()

    def load_schema(self) -> Optional[Schema]:
        """Load the schema from disk."""
        path = self._get_schema_path()
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            data = json.load(f)
        return Schema.from_dict(data)

    def _update_metadata(self) -> None:
        """Update metadata file with last modified time."""
        metadata = self._load_metadata()
        metadata["last_modified"] = datetime.now().isoformat()
        with open(self._get_metadata_path(), "w") as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from disk."""
        path = self._get_metadata_path()
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {"created_at": datetime.now().isoformat(), "version": "0.1.0"}

    # Table data operations

    def read_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Read all rows from a table."""
        path = self._get_table_path(table_name)
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            return json.load(f)

    def write_table(self, table_name: str, rows: List[Dict[str, Any]]) -> None:
        """Write all rows to a table."""
        path = self._get_table_path(table_name)
        with open(path, "w") as f:
            json.dump(rows, f, indent=2)
        self._update_metadata()

    def append_row(self, table_name: str, row: Dict[str, Any]) -> None:
        """Append a single row to a table."""
        rows = self.read_table(table_name)
        rows.append(row)
        self.write_table(table_name, rows)

    def create_table(self, table_name: str) -> None:
        """Create an empty table file."""
        self.write_table(table_name, [])

    def drop_table(self, table_name: str) -> None:
        """Delete a table file."""
        path = self._get_table_path(table_name)
        if os.path.exists(path):
            os.remove(path)
        # Also remove any indexes for this table
        self._remove_table_indexes(table_name)
        self._update_metadata()

    def _remove_table_indexes(self, table_name: str) -> None:
        """Remove all index files for a table."""
        prefix = f"_idx_{table_name}_"
        for filename in os.listdir(self.data_dir):
            if filename.startswith(prefix):
                os.remove(os.path.join(self.data_dir, filename))

    def table_exists(self, table_name: str) -> bool:
        """Check if a table file exists."""
        return os.path.exists(self._get_table_path(table_name))

    # Index operations

    def save_index(
        self, table_name: str, column_name: str, index_data: Dict[str, Any]
    ) -> None:
        """Save an index to disk."""
        path = self._get_index_path(table_name, column_name)
        with open(path, "w") as f:
            json.dump(index_data, f, indent=2)

    def load_index(self, table_name: str, column_name: str) -> Optional[Dict[str, Any]]:
        """Load an index from disk."""
        path = self._get_index_path(table_name, column_name)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def drop_index(self, table_name: str, column_name: str) -> None:
        """Delete an index file."""
        path = self._get_index_path(table_name, column_name)
        if os.path.exists(path):
            os.remove(path)

    # Statistics

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        metadata = self._load_metadata()

        # Count tables and calculate total size
        total_size = 0
        table_count = 0

        for filename in os.listdir(self.data_dir):
            filepath = os.path.join(self.data_dir, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
                if not filename.startswith("_"):
                    table_count += 1

        return {
            "table_count": table_count,
            "total_size_bytes": total_size,
            "data_directory": self.data_dir,
            "created_at": metadata.get("created_at"),
            "last_modified": metadata.get("last_modified"),
        }

    def reset(self) -> None:
        """Delete all data files."""
        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                filepath = os.path.join(self.data_dir, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
