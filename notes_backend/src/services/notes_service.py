"""NotesService: reusable orchestration layer for note operations.

This layer provides a single, named flow per use-case, with consistent logging and
error semantics. The API layer should call only these flows (not SQL directly).
"""

from __future__ import annotations

import logging

from src.models.notes import Note, NoteCreate, NoteUpdate
from src.repositories.notes_repository import NotesRepository, NoteNotFoundError

logger = logging.getLogger(__name__)


class NotesService:
    """Orchestration layer for notes flows."""

    def __init__(self, *, repo: NotesRepository):
        self._repo = repo

    # PUBLIC_INTERFACE
    def create_note_flow(self, *, payload: NoteCreate) -> Note:
        """CreateNoteFlow."""
        logger.info("CreateNoteFlow start title_len=%s content_len=%s", len(payload.title), len(payload.content))
        note = self._repo.create_note(title=payload.title, content=payload.content)
        logger.info("CreateNoteFlow done note_id=%s", note.id)
        return note

    # PUBLIC_INTERFACE
    def list_notes_flow(self, *, limit: int, offset: int) -> list[Note]:
        """ListNotesFlow."""
        logger.info("ListNotesFlow start limit=%s offset=%s", limit, offset)
        items = self._repo.list_notes(limit=limit, offset=offset)
        logger.info("ListNotesFlow done count=%s", len(items))
        return items

    # PUBLIC_INTERFACE
    def get_note_flow(self, *, note_id: int) -> Note:
        """GetNoteFlow."""
        logger.info("GetNoteFlow start note_id=%s", note_id)
        try:
            note = self._repo.get_note(note_id=note_id)
        except NoteNotFoundError:
            logger.info("GetNoteFlow not_found note_id=%s", note_id)
            raise
        logger.info("GetNoteFlow done note_id=%s", note_id)
        return note

    # PUBLIC_INTERFACE
    def update_note_flow(self, *, note_id: int, payload: NoteUpdate) -> Note:
        """UpdateNoteFlow."""
        logger.info(
            "UpdateNoteFlow start note_id=%s has_title=%s has_content=%s",
            note_id,
            payload.title is not None,
            payload.content is not None,
        )
        try:
            note = self._repo.update_note(note_id=note_id, title=payload.title, content=payload.content)
        except NoteNotFoundError:
            logger.info("UpdateNoteFlow not_found note_id=%s", note_id)
            raise
        logger.info("UpdateNoteFlow done note_id=%s", note_id)
        return note

    # PUBLIC_INTERFACE
    def delete_note_flow(self, *, note_id: int) -> None:
        """DeleteNoteFlow."""
        logger.info("DeleteNoteFlow start note_id=%s", note_id)
        try:
            self._repo.delete_note(note_id=note_id)
        except NoteNotFoundError:
            logger.info("DeleteNoteFlow not_found note_id=%s", note_id)
            raise
        logger.info("DeleteNoteFlow done note_id=%s", note_id)

    # PUBLIC_INTERFACE
    def search_notes_flow(self, *, q: str, limit: int, offset: int) -> list[Note]:
        """SearchNotesFlow."""
        logger.info("SearchNotesFlow start q_len=%s limit=%s offset=%s", len(q), limit, offset)
        items = self._repo.search_notes(q=q, limit=limit, offset=offset)
        logger.info("SearchNotesFlow done count=%s", len(items))
        return items
