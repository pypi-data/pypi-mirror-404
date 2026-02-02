from __future__ import annotations

from pathlib import Path
from typing import NotRequired, TypedDict

from pydantic import SecretStr
from utilities.constants import CPU_COUNT
from utilities.core import get_env

BACKBLAZE_KEY_ID_ENV_VAR: str = "BACKBLAZE_KEY_ID"
BACKBLAZE_KEY_ID: SecretStr | None = get_env(
    BACKBLAZE_KEY_ID_ENV_VAR, nullable=True, transform=SecretStr
)
BACKBLAZE_APPLICATION_KEY_ENV_VAR: str = "BACKBLAZE_APPLICATION_KEY"
BACKBLAZE_APPLICATION_KEY: SecretStr | None = get_env(
    BACKBLAZE_APPLICATION_KEY_ENV_VAR, nullable=True, transform=SecretStr
)


LATEST: str = "latest"
READ_CONCURRENCY: int = max(round(CPU_COUNT / 2), 2)


RESTIC_PASSWORD: SecretStr | None = get_env(
    "RESTIC_PASSWORD", nullable=True, transform=SecretStr
)
RESTIC_PASSWORD_FILE_ENV_VAR: str = "RESTIC_PASSWORD_FILE"  # noqa: S105
RESTIC_PASSWORD_FILE: Path | None = get_env(
    RESTIC_PASSWORD_FILE_ENV_VAR, nullable=True, transform=Path
)


RESTIC_SRC_PASSWORD: SecretStr | None = get_env(
    "RESTIC_SRC_PASSWORD", nullable=True, transform=SecretStr
)
RESTIC_SRC_PASSWORD_FILE: Path | None = get_env(
    "RESTIC_SRC_PASSWORD_FILE", nullable=True, transform=Path
)
RESTIC_DEST_PASSWORD: SecretStr | None = get_env(
    "RESTIC_DEST_PASSWORD", nullable=True, transform=SecretStr
)
RESTIC_DEST_PASSWORD_FILE: Path | None = get_env(
    "RESTIC_DEST_PASSWORD_FILE", nullable=True, transform=Path
)


RESTIC_REPOSITORY_ENV_VAR: str = "RESTIC_REPOSITORY"
RESTIC_REPOSITORY: str | None = get_env(RESTIC_REPOSITORY_ENV_VAR, nullable=True)


##


class KeepKwargs(TypedDict):
    keep_last: NotRequired[int]
    keep_hourly: NotRequired[int]
    keep_daily: NotRequired[int]
    keep_weekly: NotRequired[int]
    keep_monthly: NotRequired[int]
    keep_yearly: NotRequired[int]
    keep_within: NotRequired[str]
    keep_within_hourly: NotRequired[str]
    keep_within_daily: NotRequired[str]
    keep_within_weekly: NotRequired[str]
    keep_within_monthly: NotRequired[str]
    keep_within_yearly: NotRequired[str]


DEFAULT_KEEP_KWARGS = KeepKwargs(
    keep_last=100,
    keep_hourly=24 * 7,
    keep_daily=30,
    keep_weekly=52,
    keep_monthly=5 * 12,
    keep_yearly=10,
    keep_within_hourly="7d",
    keep_within_daily="1m",
    keep_within_weekly="1y",
    keep_within_monthly="5y",
    keep_within_yearly="10y",
)


__all__ = [
    "BACKBLAZE_APPLICATION_KEY",
    "BACKBLAZE_APPLICATION_KEY_ENV_VAR",
    "BACKBLAZE_KEY_ID",
    "BACKBLAZE_KEY_ID_ENV_VAR",
    "DEFAULT_KEEP_KWARGS",
    "LATEST",
    "READ_CONCURRENCY",
    "RESTIC_DEST_PASSWORD",
    "RESTIC_DEST_PASSWORD_FILE",
    "RESTIC_PASSWORD",
    "RESTIC_PASSWORD_FILE",
    "RESTIC_PASSWORD_FILE_ENV_VAR",
    "RESTIC_REPOSITORY",
    "RESTIC_REPOSITORY_ENV_VAR",
    "RESTIC_SRC_PASSWORD",
    "RESTIC_SRC_PASSWORD_FILE",
    "KeepKwargs",
]
