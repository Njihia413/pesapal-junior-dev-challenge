"""
PesapalDB Interactive REPL

Read-Eval-Print Loop for interactive SQL execution.
"""

import sys
import readline
from typing import Optional
from tabulate import tabulate

from .engine import Database


class REPL:
    """Interactive SQL REPL."""

    COMMANDS = {
        ".help": "Show this help message",
        ".tables": "List all tables",
        ".schema": "Show schema for a table (.schema tablename)",
        ".stats": "Show database statistics",
        ".clear": "Clear the screen",
        ".exit": "Exit the REPL",
        ".quit": "Exit the REPL",
    }

    def __init__(self, data_dir: str = "data"):
        self.db = Database(data_dir)
        self.running = True
        self.buffer = []

    def start(self) -> None:
        """Start the REPL."""
        self._print_banner()

        while self.running:
            try:
                prompt = "sql> " if not self.buffer else "...> "
                line = input(prompt)
                self._process_line(line)
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("\nUse .exit or .quit to exit")
                self.buffer = []

    def _print_banner(self) -> None:
        """Print welcome banner."""
        print("\n" + "=" * 50)
        print("  PesapalDB - Interactive SQL Console")
        print("  Type .help for commands, .exit to quit")
        print("=" * 50 + "\n")

    def _process_line(self, line: str) -> None:
        """Process a line of input."""
        line = line.strip()

        if not line:
            return

        # Handle dot commands
        if line.startswith("."):
            self._handle_command(line)
            return

        # Accumulate SQL until we see a semicolon
        self.buffer.append(line)

        full_sql = " ".join(self.buffer)

        if ";" in full_sql:
            self.buffer = []
            self._execute_sql(full_sql)

    def _handle_command(self, cmd: str) -> None:
        """Handle a dot command."""
        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if command in (".exit", ".quit"):
            self.running = False
            print("Goodbye!")
        elif command == ".help":
            self._show_help()
        elif command == ".tables":
            self._show_tables()
        elif command == ".schema":
            self._show_schema(args[0] if args else None)
        elif command == ".stats":
            self._show_stats()
        elif command == ".clear":
            print("\033[H\033[J", end="")
        else:
            print(f"Unknown command: {command}")
            print("Type .help for available commands")

    def _execute_sql(self, sql: str) -> None:
        """Execute SQL and display results."""
        try:
            result = self.db.execute(sql)

            if result.success:
                if result.rows:
                    # Display as table
                    print(tabulate(result.rows, headers="keys", tablefmt="simple"))
                    print(f"\n{result.row_count} row(s) returned")
                else:
                    print(f"✓ {result.message}")
            else:
                print(f"✗ Error: {result.message}")
        except Exception as e:
            print(f"✗ Error: {e}")

        print()

    def _show_help(self) -> None:
        """Show help message."""
        print("\nAvailable commands:")
        for cmd, desc in self.COMMANDS.items():
            print(f"  {cmd:12} {desc}")
        print("\nSQL statements should end with a semicolon (;)")
        print()

    def _show_tables(self) -> None:
        """Show all tables."""
        tables = self.db.get_tables()
        if tables:
            print("\nTables:")
            for table in tables:
                rows = len(self.db.storage.read_table(table))
                print(f"  {table} ({rows} rows)")
        else:
            print("\nNo tables exist yet")
        print()

    def _show_schema(self, table_name: Optional[str]) -> None:
        """Show schema for a table."""
        if not table_name:
            print("Usage: .schema <table_name>")
            return

        info = self.db.get_table_info(table_name)
        if not info:
            print(f"Table '{table_name}' not found")
            return

        print(f"\nTable: {info['name']}")
        print("-" * 60)

        headers = ["Column", "Type", "Nullable", "Key", "Extra"]
        rows = []
        for col in info["columns"]:
            type_str = col["type"]
            if col["length"]:
                type_str += f"({col['length']})"

            key = ""
            if col["primary_key"]:
                key = "PRI"
            elif col["unique"]:
                key = "UNI"

            extra = []
            if col["auto_increment"]:
                extra.append("auto_increment")

            rows.append(
                [
                    col["name"],
                    type_str,
                    "YES" if col["nullable"] else "NO",
                    key,
                    ", ".join(extra),
                ]
            )

        print(tabulate(rows, headers=headers, tablefmt="simple"))
        print(f"\nRows: {info['row_count']}")
        if info["indexes"]:
            print(f"Indexes: {', '.join(info['indexes'])}")
        print()

    def _show_stats(self) -> None:
        """Show database statistics."""
        stats = self.db.get_stats()

        print("\nDatabase Statistics:")
        print("-" * 40)
        print(f"  Data directory: {stats['data_directory']}")
        print(f"  Tables: {stats['table_count']}")
        print(f"  Total size: {stats['total_size_bytes']:,} bytes")

        if stats.get("tables"):
            print("\nTable row counts:")
            for name, count in stats["tables"].items():
                print(f"  {name}: {count} rows")
        print()


def main():
    """Entry point for the REPL."""
    import argparse

    parser = argparse.ArgumentParser(description="PesapalDB Interactive REPL")
    parser.add_argument(
        "--data-dir", "-d", default="data", help="Data directory path (default: data)"
    )
    args = parser.parse_args()

    repl = REPL(data_dir=args.data_dir)
    repl.start()


if __name__ == "__main__":
    main()
