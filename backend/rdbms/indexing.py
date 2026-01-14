"""
PesapalDB Indexing

Implements B-tree index structure and IndexManager for efficient lookups.
"""

from typing import Any, Dict, List, Optional, Tuple


class BTreeNode:
    """A node in the B-tree."""

    def __init__(self, leaf: bool = True):
        self.leaf = leaf
        self.keys: List[Any] = []
        self.values: List[List[int]] = []  # List of row IDs for each key
        self.children: List["BTreeNode"] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "leaf": self.leaf,
            "keys": self.keys,
            "values": self.values,
            "children": [c.to_dict() for c in self.children],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BTreeNode":
        """Create node from dictionary."""
        node = cls(leaf=data.get("leaf", True))
        node.keys = data.get("keys", [])
        node.values = data.get("values", [])
        node.children = [cls.from_dict(c) for c in data.get("children", [])]
        return node


class BTree:
    """B-tree index implementation."""

    def __init__(self, order: int = 4):
        self.order = order  # Maximum number of children
        self.root = BTreeNode(leaf=True)

    @property
    def min_keys(self) -> int:
        """Minimum number of keys in a node."""
        return (self.order - 1) // 2

    @property
    def max_keys(self) -> int:
        """Maximum number of keys in a node."""
        return self.order - 1

    def insert(self, key: Any, row_id: int) -> None:
        """Insert a key-rowid pair into the index."""
        root = self.root

        # If root is full, split it
        if len(root.keys) == self.max_keys:
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root

        self._insert_non_full(self.root, key, row_id)

    def _insert_non_full(self, node: BTreeNode, key: Any, row_id: int) -> None:
        """Insert into a node that is not full."""
        # Find position for the key
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        # If key already exists, add row_id to its list
        if i < len(node.keys) and node.keys[i] == key:
            if row_id not in node.values[i]:
                node.values[i].append(row_id)
            return

        if node.leaf:
            # Insert key and row_id
            node.keys.insert(i, key)
            node.values.insert(i, [row_id])
        else:
            # Descend to child
            if len(node.children[i].keys) == self.max_keys:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, row_id)

    def _split_child(self, parent: BTreeNode, index: int) -> None:
        """Split a full child node."""
        child = parent.children[index]
        mid = len(child.keys) // 2

        new_node = BTreeNode(leaf=child.leaf)

        # Move right half of keys to new node
        new_node.keys = child.keys[mid + 1 :]
        new_node.values = child.values[mid + 1 :]

        if not child.leaf:
            new_node.children = child.children[mid + 1 :]
            child.children = child.children[: mid + 1]

        # Move middle key to parent
        parent.keys.insert(index, child.keys[mid])
        parent.values.insert(index, child.values[mid])
        parent.children.insert(index + 1, new_node)

        # Truncate child
        child.keys = child.keys[:mid]
        child.values = child.values[:mid]

    def search(self, key: Any) -> List[int]:
        """Search for row IDs with the given key."""
        return self._search(self.root, key)

    def _search(self, node: BTreeNode, key: Any) -> List[int]:
        """Recursive search in a node."""
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if i < len(node.keys) and node.keys[i] == key:
            return node.values[i]

        if node.leaf:
            return []

        return self._search(node.children[i], key)

    def delete(self, key: Any, row_id: int = None) -> None:
        """Delete a key or specific row_id from the index."""
        self._delete(self.root, key, row_id)

    def _delete(self, node: BTreeNode, key: Any, row_id: int = None) -> None:
        """Recursive delete from a node."""
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if i < len(node.keys) and node.keys[i] == key:
            if row_id is not None:
                # Remove specific row_id
                if row_id in node.values[i]:
                    node.values[i].remove(row_id)
                if not node.values[i]:
                    # No more row_ids, remove the key entirely
                    node.keys.pop(i)
                    node.values.pop(i)
            else:
                # Remove the entire key
                node.keys.pop(i)
                node.values.pop(i)
        elif not node.leaf:
            self._delete(node.children[i], key, row_id)

    def range_search(
        self, min_key: Any = None, max_key: Any = None
    ) -> List[Tuple[Any, List[int]]]:
        """Search for all keys in a range."""
        results = []
        self._range_search(self.root, min_key, max_key, results)
        return results

    def _range_search(
        self,
        node: BTreeNode,
        min_key: Any,
        max_key: Any,
        results: List[Tuple[Any, List[int]]],
    ) -> None:
        """Recursive range search."""
        for i, key in enumerate(node.keys):
            if min_key is not None and key < min_key:
                continue
            if max_key is not None and key > max_key:
                break
            results.append((key, node.values[i]))

        if not node.leaf:
            for i, child in enumerate(node.children):
                if i < len(node.keys):
                    if min_key is None or node.keys[i] >= min_key:
                        self._range_search(child, min_key, max_key, results)
                else:
                    self._range_search(child, min_key, max_key, results)

    def to_dict(self) -> Dict[str, Any]:
        """Convert B-tree to dictionary for serialization."""
        return {"order": self.order, "root": self.root.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BTree":
        """Create B-tree from dictionary."""
        tree = cls(order=data.get("order", 4))
        tree.root = BTreeNode.from_dict(data.get("root", {}))
        return tree


class IndexManager:
    """Manages indexes for a table."""

    def __init__(self):
        self.indexes: Dict[str, BTree] = {}

    def create_index(self, column_name: str, order: int = 4) -> BTree:
        """Create a new index for a column."""
        index = BTree(order=order)
        self.indexes[column_name] = index
        return index

    def drop_index(self, column_name: str) -> None:
        """Drop an index."""
        if column_name in self.indexes:
            del self.indexes[column_name]

    def get_index(self, column_name: str) -> Optional[BTree]:
        """Get an index by column name."""
        return self.indexes.get(column_name)

    def has_index(self, column_name: str) -> bool:
        """Check if an index exists for a column."""
        return column_name in self.indexes

    def insert(self, row: Dict[str, Any], row_id: int) -> None:
        """Update all indexes with a new row."""
        for column_name, index in self.indexes.items():
            if column_name in row:
                value = row[column_name]
                if value is not None:
                    index.insert(value, row_id)

    def delete(self, row: Dict[str, Any], row_id: int) -> None:
        """Remove a row from all indexes."""
        for column_name, index in self.indexes.items():
            if column_name in row:
                value = row[column_name]
                if value is not None:
                    index.delete(value, row_id)

    def rebuild_from_rows(
        self, rows: List[Dict[str, Any]], pk_column: str = None
    ) -> None:
        """Rebuild all indexes from rows."""
        for column_name, index in self.indexes.items():
            # Clear and rebuild
            index.root = BTreeNode(leaf=True)
            for i, row in enumerate(rows):
                row_id = row.get(pk_column, i) if pk_column else i
                value = row.get(column_name)
                if value is not None:
                    index.insert(value, row_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert all indexes to dictionary."""
        return {name: idx.to_dict() for name, idx in self.indexes.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexManager":
        """Create IndexManager from dictionary."""
        manager = cls()
        for name, idx_data in data.items():
            manager.indexes[name] = BTree.from_dict(idx_data)
        return manager
