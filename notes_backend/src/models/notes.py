"""Pydantic models for the Notes API.

These models define the public HTTP contract for create/read/update/list/search.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Shared fields for notes."""

    title: str = Field("", description="Note title (can be empty).", max_length=500)
    content: str = Field("", description="Note content.", max_length=20000)


class NoteCreate(NoteBase):
    """Request model for creating a note."""


class NoteUpdate(BaseModel):
    """Request model for updating a note.

    Fields are optional; only provided fields are updated.
    """

    title: Optional[str] = Field(
        default=None, description="Updated note title (can be empty).", max_length=500
    )
    content: Optional[str] = Field(
        default=None, description="Updated note content.", max_length=20000
    )


class Note(NoteBase):
    """Response model for a note."""

    id: int = Field(..., description="Note identifier.")
    created_at: datetime = Field(..., description="When the note was created (UTC).")
    updated_at: datetime = Field(..., description="When the note was last updated (UTC).")


class NoteListResponse(BaseModel):
    """Response model for listing/searching notes."""

    items: list[Note] = Field(..., description="Notes returned for the request.")
    total: int = Field(..., description="Total notes returned (len(items)).")


class ErrorResponse(BaseModel):
    """Standard error response payload."""

    detail: str = Field(..., description="Human-readable error message.")
