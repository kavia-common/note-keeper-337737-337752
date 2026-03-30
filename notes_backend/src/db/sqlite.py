"""SQLite adapter utilities for the notes backend.

This module is the single I/O boundary for opening SQLite connections.
It intentionally resolves the database file path using the *database container's*
canonical db_connection.txt, if present.

Environment variables:
  - SQLITE_DB (optional): If set, overrides all other resolution mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sqlite3
from typing import Optional


@dataclass(frozen=True)
class SqliteConfig:
    """Resolved SQLite configuration."""

    db_file_path: Path


def _parse_db_connection_txt(connection_txt_path: Path) -> Optional[Path]:
    """Parse '# File path: ...' from db_connection.txt. Returns None if not found."""
    if not connection_txt_path.exists():
        return None
    try:
        content = connection_txt_path.read_text(encoding="utf-8")
    except Exception:
        return None

    for line in content.splitlines():
        line = line.strip()
        if line.lower().startswith("# file path:"):
            raw = line.split(":", 1)[1].strip()
            if raw:
                return Path(raw)
    return None


# PUBLIC_INTERFACE
def resolve_sqlite_config() -> SqliteConfig:
    """Resolve SQLite DB file path for this backend.

    Flow name:
      ResolveSqliteConfigFlow

    Contract:
      Inputs:
        - Reads SQLITE_DB environment variable (optional).
        - Reads canonical db_connection.txt from the sibling database container (optional).
      Outputs:
        - SqliteConfig with db_file_path.
      Errors:
        - Never raises for missing files; falls back to a local 'myapp.db' in CWD.
      Side effects:
        - None.
    """
    env_db = os.getenv("SQLITE_DB")
    if env_db:
        return SqliteConfig(db_file_path=Path(env_db))

    # Canonical path lives in the database container.
    # Repository layout: note-keeper-.../notes_backend/src/db/sqlite.py
    # -> go up to workspace root and into database container.
    workspace_root = Path(__file__).resolve().parents[4]
    connection_txt_path = (
        workspace_root / "note-keeper-337737-337753" / "database" / "db_connection.txt"
    )
    parsed = _parse_db_connection_txt(connection_txt_path)
    if parsed:
        return SqliteConfig(db_file_path=parsed)

    # Fallback for dev/tests: local file.
    return SqliteConfig(db_file_path=Path("myapp.db"))


# PUBLIC_INTERFACE
def connect_sqlite(*, config: SqliteConfig) -> sqlite3.Connection:
    """Open a SQLite connection with consistent pragmas.

    Contract:
      Inputs:
        - config.db_file_path: Path to SQLite DB file (absolute or relative).
      Outputs:
        - sqlite3.Connection with row_factory=sqlite3.Row.
      Errors:
        - Raises sqlite3.Error on connection problems.
      Side effects:
        - May create the DB file if it doesn't exist.
    """
    if config.db_file_path.is_absolute():
        config.db_file_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(config.db_file_path), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn
