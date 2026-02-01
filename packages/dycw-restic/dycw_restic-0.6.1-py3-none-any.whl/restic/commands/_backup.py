from __future__ import annotations

from re import MULTILINE, search
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from utilities.core import duration_to_seconds, sync_sleep, to_logger
from utilities.subprocess import run
from whenever import TimeDelta

from restic._constants import READ_CONCURRENCY, RESTIC_PASSWORD, RESTIC_PASSWORD_FILE
from restic._utilities import (
    expand_dry_run,
    expand_exclude,
    expand_exclude_i,
    expand_read_concurrency,
    expand_tag,
    yield_password,
)
from restic.commands._forget import forget
from restic.commands._init import init

if TYPE_CHECKING:
    from utilities.types import Duration, MaybeSequenceStr, PathLike, SecretLike

    from restic._repo import Repo


_LOGGER = to_logger(__name__)


def backup(
    path: PathLike,
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    dry_run: bool = False,
    exclude: MaybeSequenceStr | None = None,
    exclude_i: MaybeSequenceStr | None = None,
    read_concurrency: int = READ_CONCURRENCY,
    tag_backup: MaybeSequenceStr | None = None,
    run_forget: bool = True,
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
    tag_forget: MaybeSequenceStr | None = None,
    sleep: Duration | None = None,
) -> None:
    _LOGGER.info("Backing up %r to %s...", str(path), repo)
    try:
        _backup_core(
            path,
            repo,
            password=password,
            password_file=password_file,
            dry_run=dry_run,
            exclude=exclude,
            exclude_i=exclude_i,
            read_concurrency=read_concurrency,
            tag=tag_backup,
        )
    except CalledProcessError as error:
        if search(
            "Is there a repository at the following location?",
            error.stderr,
            flags=MULTILINE,
        ):
            _LOGGER.info("Auto-initializing repo...")
            init(repo, password=password, password_file=password_file)
            _backup_core(
                path,
                repo,
                password=password,
                password_file=password_file,
                dry_run=dry_run,
                exclude=exclude,
                exclude_i=exclude_i,
                read_concurrency=read_concurrency,
                tag=tag_backup,
            )
        else:
            raise
    if run_forget and (
        (keep_last is not None)
        or (keep_hourly is not None)
        or (keep_daily is not None)
        or (keep_weekly is not None)
        or (keep_monthly is not None)
        or (keep_yearly is not None)
        or (keep_within is not None)
        or (keep_within_hourly is not None)
        or (keep_within_daily is not None)
        or (keep_within_weekly is not None)
        or (keep_within_monthly is not None)
        or (keep_within_yearly is not None)
    ):
        forget(
            repo,
            password=password,
            password_file=password_file,
            keep_last=keep_last,
            keep_hourly=keep_hourly,
            keep_daily=keep_daily,
            keep_weekly=keep_weekly,
            keep_monthly=keep_monthly,
            keep_yearly=keep_yearly,
            keep_within=keep_within,
            keep_within_hourly=keep_within_hourly,
            keep_within_daily=keep_within_daily,
            keep_within_weekly=keep_within_weekly,
            keep_within_monthly=keep_within_monthly,
            keep_within_yearly=keep_within_yearly,
            group_by=group_by,
            prune=prune,
            repack_cacheable_only=repack_cacheable_only,
            repack_small=repack_small,
            repack_uncompressed=repack_uncompressed,
            tag=tag_forget,
        )
    if sleep is None:
        _LOGGER.info("Finished backing up %r to %s", path, repo)
    else:
        delta = TimeDelta(seconds=duration_to_seconds(sleep))
        _LOGGER.info(
            "Finished backing up %r to %s; sleeping for %s...", str(path), repo, delta
        )
        sync_sleep(delta)
        _LOGGER.info("Finishing sleeping for %s", delta)


def _backup_core(
    path: PathLike,
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    dry_run: bool = False,
    exclude: MaybeSequenceStr | None = None,
    exclude_i: MaybeSequenceStr | None = None,
    read_concurrency: int = READ_CONCURRENCY,
    tag: MaybeSequenceStr | None = None,
) -> None:
    with (
        repo.yield_env(),
        yield_password(password=password, password_file=password_file),
    ):
        run(
            "restic",
            "backup",
            *expand_dry_run(dry_run=dry_run),
            *expand_exclude(exclude=exclude),
            *expand_exclude_i(exclude_i=exclude_i),
            *expand_read_concurrency(read_concurrency),
            *expand_tag(tag=tag),
            str(path),
            print=True,
        )
