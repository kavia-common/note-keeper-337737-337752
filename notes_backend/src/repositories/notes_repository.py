"""NotesRepository: SQLite persistence for notes.

This module is the data-access layer (I/O boundary) for notes.
"""

from __future__ import annotations

from datetime import datetime
import logging
import sqlite3
from typing import Optional

from src.db.sqlite import SqliteConfig, connect_sqlite
from src.models.notes import Note

logger = logging.getLogger(__name__)


class NoteNotFoundError(KeyError):
    """Raised when a requested note does not exist."""


def _row_to_note(row: sqlite3.Row) -> Note:
    """Convert sqlite3.Row to Note."""
    # SQLite returns text for timestamps unless detect_types + converters exist.
    # We'll accept both str and datetime and normalize via fromisoformat when needed.
    def _to_dt(v):
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # SQLite CURRENT_TIMESTAMP -> 'YYYY-MM-DD HH:MM:SS'
            return datetime.fromisoformat(v.replace(" ", "T"))
        raise TypeError(f"Unsupported timestamp type: {type(v)}")

    return Note(
        id=int(row["id"]),
        title=row["title"] or "",
        content=row["content"] or "",
        created_at=_to_dt(row["created_at"]),
        updated_at=_to_dt(row["updated_at"]),
    )


class NotesRepository:
    """SQLite-backed repository for notes."""

    def __init__(self, *, sqlite_config: SqliteConfig):
        self._cfg = sqlite_config

    def _connect(self) -> sqlite3.Connection:
        return connect_sqlite(config=self._cfg)

    # PUBLIC_INTERFACE
    def create_note(self, *, title: str, content: str) -> Note:
        """Create a note and return it."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO notes (title, content) VALUES (?, ?)",
                (title, content),
            )
            note_id = int(cur.lastrowid)
            row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
            assert row is not None
            return _row_to_note(row)

    # PUBLIC_INTERFACE
    def list_notes(self, *, limit: int = 200, offset: int = 0) -> list[Note]:
        """List notes ordered by updated_at desc."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM notes ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?",
                (int(limit), int(offset)),
            ).fetchall()
            return [_row_to_note(r) for r in rows]

    # PUBLIC_INTERFACE
    def get_note(self, *, note_id: int) -> Note:
        """Get a note by id. Raises NoteNotFoundError if absent."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM notes WHERE id = ?", (int(note_id),)).fetchone()
            if row is None:
                raise NoteNotFoundError(f"Note {note_id} not found")
            return _row_to_note(row)

    # PUBLIC_INTERFACE
    def update_note(
        self,
        *,
        note_id: int,
        title: Optional[str],
        content: Optional[str],
    ) -> Note:
        """Update a note. Only provided fields are updated."""
        if title is None and content is None:
            # No-op update returns current state.
            return self.get_note(note_id=note_id)

        # Build statement without patchy branching at call sites: centralized here.
        sets: list[str] = []
        params: list[object] = []
        if title is not None:
            sets.append("title = ?")
            params.append(title)
        if content is not None:
            sets.append("content = ?")
            params.append(content)

        params.append(int(note_id))

        with self._connect() as conn:
            cur = conn.execute(
                f"UPDATE notes SET {', '.join(sets)} WHERE id = ?",
                tuple(params),
            )
            if cur.rowcount == 0:
                raise NoteNotFoundError(f"Note {note_id} not found")
            row = conn.execute("SELECT * FROM notes WHERE id = ?", (int(note_id),)).fetchone()
            assert row is not None
            return _row_to_note(row)

    # PUBLIC_INTERFACE
    def delete_note(self, *, note_id: int) -> None:
        """Delete a note. Raises NoteNotFoundError if absent."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM notes WHERE id = ?", (int(note_id),))
            if cur.rowcount == 0:
                raise NoteNotFoundError(f"Note {note_id} not found")

    # PUBLIC_INTERFACE
    def search_notes(self, *, q: str, limit: int = 200, offset: int = 0) -> list[Note]:
        """Search notes by query string in title/content (case-insensitive LIKE).

        Note: This uses LIKE for portability; can be replaced by FTS later behind
        this single repository method without touching API/flow layers.
        """
        term = f"%{q.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM notes
                WHERE title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\'
                ORDER BY updated_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (term, term, int(limit), int(offset)),
            ).fetchall()
            return [_row_to_note(r) for r in rows]
