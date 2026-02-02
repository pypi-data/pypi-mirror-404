from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import to_logger
from utilities.subprocess import run

from restic._constants import RESTIC_PASSWORD, RESTIC_PASSWORD_FILE
from restic._utilities import (
    expand_bool,
    expand_dry_run,
    expand_group_by,
    expand_keep,
    expand_keep_within,
    expand_tag,
    yield_password,
)

if TYPE_CHECKING:
    from utilities.types import MaybeSequenceStr, PathLike, SecretLike

    from restic._repo import Repo


_LOGGER = to_logger(__name__)


def forget(
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    dry_run: bool = False,
    keep_last: int | None = None,
    keep_hourly: int | None = None,
    keep_daily: int | None = None,
    keep_weekly: int | None = None,
    keep_monthly: int | None = None,
    keep_yearly: int | None = None,
    keep_within: str | None = None,
    keep_within_hourly: str | None = None,
    keep_within_daily: str | None = None,
    keep_within_weekly: str | None = None,
    keep_within_monthly: str | None = None,
    keep_within_yearly: str | None = None,
    group_by: MaybeSequenceStr | None = None,
    prune: bool = True,
    repack_cacheable_only: bool = False,
    repack_small: bool = True,
    repack_uncompressed: bool = True,
    tag: MaybeSequenceStr | None = None,
) -> None:
    _LOGGER.info("Forgetting snapshots in %s...", repo)
    with (
        repo.yield_env(),
        yield_password(password=password, password_file=password_file),
    ):
        run(
            "restic",
            "forget",
            *expand_dry_run(dry_run=dry_run),
            *expand_keep("last", n=keep_last),
            *expand_keep("hourly", n=keep_hourly),
            *expand_keep("daily", n=keep_daily),
            *expand_keep("weekly", n=keep_weekly),
            *expand_keep("monthly", n=keep_monthly),
            *expand_keep("yearly", n=keep_yearly),
            *expand_keep_within("within", duration=keep_within),
            *expand_keep_within("within-hourly", duration=keep_within_hourly),
            *expand_keep_within("within-daily", duration=keep_within_daily),
            *expand_keep_within("within-weekly", duration=keep_within_weekly),
            *expand_keep_within("within-monthly", duration=keep_within_monthly),
            *expand_keep_within("within-yearly", duration=keep_within_yearly),
            *expand_group_by(group_by=group_by),
            *expand_bool("prune", bool_=prune),
            *expand_bool("repack-cacheable-only", bool_=repack_cacheable_only),
            *expand_bool("repack-small", bool_=repack_small),
            *expand_bool("repack-uncompressed", bool_=repack_uncompressed),
            *expand_tag(tag=tag),
            print=True,
        )
    _LOGGER.info("Finished forgetting snapshots in %s", repo)


__all__ = ["forget"]
