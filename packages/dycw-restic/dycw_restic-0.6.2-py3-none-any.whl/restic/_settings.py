# ruff: noqa: TC003
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings
from utilities.importlib import files
from utilities.pydantic_settings import (
    CustomBaseSettings,
    PathLikeOrWithSection,
    load_settings,
)

_FILES = files(anchor="restic")
_SETTINGS_TOML = "settings.toml"


class _Settings(CustomBaseSettings):
    toml_files: ClassVar[Sequence[PathLikeOrWithSection]] = [
        (_SETTINGS_TOML, "gitea"),
        _FILES.joinpath(_SETTINGS_TOML),
    ]

    backup: _BackupSettings


class _BackupSettings(BaseSettings):
    sleep: int | None = None
    backblaze: _BackupBackBlazeSettings


class _BackupBackBlazeSettings(BaseSettings):
    job: Path


SETTINGS = load_settings(_Settings)


__all__ = ["SETTINGS"]
