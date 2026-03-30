"""FastAPI application entrypoint for the notes backend.

Provides:
- Health endpoint
- Notes REST API (CRUD + search) backed by SQLite

Environment variables:
- SQLITE_DB (optional): absolute/relative path to SQLite file.
  If unset, backend attempts to read canonical path from the database container's
  db_connection.txt, else falls back to ./myapp.db.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.notes import router as notes_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

openapi_tags = [
    {
        "name": "system",
        "description": "System/health endpoints.",
    },
    {
        "name": "notes",
        "description": "CRUD and search for notes.",
    },
]

app = FastAPI(
    title="Notes Backend API",
    description="REST API for creating, listing, retrieving, updating, deleting, and searching notes.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["system"],
    summary="Health check",
    description="Health probe endpoint used by deployment and local development.",
    operation_id="health_check",
)
def health_check():
    """Return a simple health response."""
    return {"message": "Healthy"}


app.include_router(notes_router)
