"""Global dependency store — DB and VectorStore singletons shared across all nodes."""
from __future__ import annotations

import os
from typing import Callable, Any
from memory.db import Database
from memory.vector_store import VectorStore

_db: Database | None = None
_vs: VectorStore | None = None
_emit_fn: Callable[[dict], None] | None = None  # set per-run by the SSE handler


def set_emit(fn: Callable[[dict], None] | None) -> None:
    global _emit_fn
    _emit_fn = fn


def emit(event: dict) -> None:
    """Fire a structured SSE event from any node/thread."""
    if _emit_fn is not None:
        try:
            _emit_fn(event)
        except Exception:
            pass


def init(data_dir: str | None = None) -> None:
    global _db, _vs
    d = data_dir or os.getenv("VAH_DATA_DIR", "./data")
    _db = Database(db_path=f"{d}/vah.db")
    _vs = VectorStore(persist_dir=f"{d}/chroma")


def db() -> Database:
    if _db is None:
        init()
    return _db  # type: ignore[return-value]


def vs() -> VectorStore:
    if _vs is None:
        init()
    return _vs  # type: ignore[return-value]
