"""Notes API router.

Implements REST endpoints for creating, listing, retrieving, updating, deleting,
and searching notes.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Query, status

from src.db.sqlite import resolve_sqlite_config
from src.models.notes import ErrorResponse, Note, NoteCreate, NoteListResponse, NoteUpdate
from src.repositories.notes_repository import NotesRepository, NoteNotFoundError
from src.services.notes_service import NotesService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes", tags=["notes"])


def _service() -> NotesService:
    """Create the NotesService with resolved dependencies."""
    cfg = resolve_sqlite_config()
    repo = NotesRepository(sqlite_config=cfg)
    return NotesService(repo=repo)


@router.post(
    "",
    response_model=Note,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Create a note",
    description="Create a new note with a title and content.",
    operation_id="create_note",
)
def create_note(payload: NoteCreate) -> Note:
    """Create a new note."""
    try:
        return _service().create_note_flow(payload=payload)
    except Exception as e:
        logger.exception("create_note failed")
        raise HTTPException(status_code=500, detail=f"Failed to create note: {e}") from e


@router.get(
    "",
    response_model=NoteListResponse,
    responses={500: {"model": ErrorResponse}},
    summary="List notes",
    description="List notes ordered by most recently updated.",
    operation_id="list_notes",
)
def list_notes(
    limit: int = Query(200, ge=1, le=500, description="Max number of notes to return."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
) -> NoteListResponse:
    """List notes."""
    try:
        items = _service().list_notes_flow(limit=limit, offset=offset)
        return NoteListResponse(items=items, total=len(items))
    except Exception as e:
        logger.exception("list_notes failed")
        raise HTTPException(status_code=500, detail=f"Failed to list notes: {e}") from e


@router.get(
    "/{note_id}",
    response_model=Note,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get a note",
    description="Retrieve a single note by id.",
    operation_id="get_note",
)
def get_note(note_id: int) -> Note:
    """Get a note by id."""
    try:
        return _service().get_note_flow(note_id=note_id)
    except NoteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("get_note failed")
        raise HTTPException(status_code=500, detail=f"Failed to get note: {e}") from e


@router.put(
    "/{note_id}",
    response_model=Note,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Update a note",
    description="Update an existing note. Only provided fields are updated.",
    operation_id="update_note",
)
def update_note(note_id: int, payload: NoteUpdate) -> Note:
    """Update a note by id."""
    try:
        return _service().update_note_flow(note_id=note_id, payload=payload)
    except NoteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("update_note failed")
        raise HTTPException(status_code=500, detail=f"Failed to update note: {e}") from e


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Delete a note",
    description="Delete a note by id.",
    operation_id="delete_note",
)
def delete_note(note_id: int) -> None:
    """Delete a note by id."""
    try:
        _service().delete_note_flow(note_id=note_id)
        return None
    except NoteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("delete_note failed")
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {e}") from e


@router.get(
    "/search",
    response_model=NoteListResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Search notes",
    description="Search notes by query substring in title/content.",
    operation_id="search_notes",
)
def search_notes(
    q: str = Query(..., min_length=1, max_length=200, description="Search query."),
    limit: int = Query(200, ge=1, le=500, description="Max number of notes to return."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
) -> NoteListResponse:
    """Search notes."""
    try:
        items = _service().search_notes_flow(q=q, limit=limit, offset=offset)
        return NoteListResponse(items=items, total=len(items))
    except Exception as e:
        logger.exception("search_notes failed")
        raise HTTPException(status_code=500, detail=f"Failed to search notes: {e}") from e
