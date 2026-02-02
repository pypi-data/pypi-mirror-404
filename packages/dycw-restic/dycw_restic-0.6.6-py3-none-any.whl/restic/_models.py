from __future__ import annotations

import datetime as dt  # noqa: TC003
from pathlib import Path  # noqa: TC003

from pydantic import BaseModel


class Snapshot(BaseModel):
    time: dt.datetime
    tree: str
    paths: list[Path]
    hostname: str
    username: str
    uid: int
    gid: int
    program_version: str
    summary: Summary
    id: str
    short_id: str


class Summary(BaseModel):
    backup_start: dt.datetime
    backup_end: dt.datetime
    files_new: int
    files_changed: int
    files_unmodified: int
    dirs_new: int
    dirs_changed: int
    dirs_unmodified: int
    data_blobs: int
    tree_blobs: int
    data_added: int
    data_added_packed: int
    total_files_processed: int
    total_bytes_processed: int


_ = Snapshot.model_rebuild()


__all__ = ["Snapshot", "Summary"]
