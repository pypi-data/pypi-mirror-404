from __future__ import annotations

from typing import TYPE_CHECKING

from click import argument, group, option, version_option
from utilities.click import CONTEXT_SETTINGS, ListStrs, Path, SecretStr, Str
from utilities.core import is_pytest, set_up_logging

from restic import __version__
from restic._click import (
    ClickRepo,
    dry_run_option,
    exclude_i_option,
    exclude_option,
    group_by_option,
    include_i_option,
    include_option,
    keep_daily_option,
    keep_hourly_option,
    keep_last_option,
    keep_monthly_option,
    keep_weekly_option,
    keep_within_daily_option,
    keep_within_hourly_option,
    keep_within_monthly_option,
    keep_within_option,
    keep_within_weekly_option,
    keep_within_yearly_option,
    keep_yearly_option,
    password_file_option,
    password_option,
    prune_option,
    repack_cacheable_only_option,
    repack_small_option,
    repack_uncompressed_option,
    repo_argument,
    sleep_option,
    tag_option,
)
from restic._constants import (
    LATEST,
    READ_CONCURRENCY,
    RESTIC_PASSWORD,
    RESTIC_PASSWORD_FILE,
)
from restic.commands._backup import backup
from restic.commands._copy import copy
from restic.commands._forget import forget
from restic.commands._init import init
from restic.commands._restore import restore
from restic.commands._snapshots import snapshots
from restic.commands._unlock import unlock

if TYPE_CHECKING:
    from utilities.types import Duration, MaybeSequenceStr, PathLike, SecretLike

    from restic._repo import Repo


@group(**CONTEXT_SETTINGS)
@version_option(version=__version__)
def cli() -> None: ...


@cli.command(name="init", **CONTEXT_SETTINGS)
@repo_argument
@password_option
@password_file_option
def init_sub_cmd(
    *, repo: Repo, password: SecretLike | None, password_file: PathLike | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    init(repo, password=password, password_file=password_file)


@cli.command(name="backup", **CONTEXT_SETTINGS)
@argument("path", type=Path())
@repo_argument
@password_option
@password_file_option
@dry_run_option
@exclude_option
@exclude_i_option
@option(
    "--read-concurrency",
    type=int,
    default=READ_CONCURRENCY,
    help="Read `n` files concurrently",
)
@option(
    "--tag-backup",
    type=ListStrs(),
    default=None,
    help="Add tags for the snapshot in the format `tag[,tag,...]`",
)
@option(
    "--run-forget",
    is_flag=True,
    default=True,
    help="Automatically run the 'forget' command",
)
@keep_last_option
@keep_hourly_option
@keep_daily_option
@keep_weekly_option
@keep_monthly_option
@keep_yearly_option
@keep_within_option
@keep_within_hourly_option
@keep_within_daily_option
@keep_within_weekly_option
@keep_within_monthly_option
@keep_within_yearly_option
@group_by_option
@prune_option
@repack_cacheable_only_option
@repack_small_option
@repack_uncompressed_option
@option(
    "--tag-forget",
    type=ListStrs(),
    default=None,
    help="Only consider snapshots including `tag[,tag,...]`",
)
@sleep_option
def backup_sub_cmd(
    *,
    path: PathLike,
    repo: Repo,
    password: SecretLike | None,
    password_file: PathLike | None,
    dry_run: bool,
    exclude: MaybeSequenceStr | None,
    exclude_i: MaybeSequenceStr | None,
    read_concurrency: int,
    tag_backup: MaybeSequenceStr | None,
    run_forget: bool,
    keep_last: int | None,
    keep_hourly: int | None,
    keep_daily: int | None,
    keep_weekly: int | None,
    keep_monthly: int | None,
    keep_yearly: int | None,
    keep_within: str | None,
    keep_within_hourly: str | None,
    keep_within_daily: str | None,
    keep_within_weekly: str | None,
    keep_within_monthly: str | None,
    keep_within_yearly: str | None,
    group_by: MaybeSequenceStr | None,
    prune: bool,
    repack_cacheable_only: bool,
    repack_small: bool,
    repack_uncompressed: bool,
    tag_forget: MaybeSequenceStr | None,
    sleep: Duration | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    backup(
        path,
        repo,
        password=password,
        password_file=password_file,
        dry_run=dry_run,
        exclude=exclude,
        exclude_i=exclude_i,
        read_concurrency=read_concurrency,
        tag_backup=tag_backup,
        run_forget=run_forget,
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
        tag_forget=tag_forget,
        sleep=sleep,
    )


@cli.command(name="copy", **CONTEXT_SETTINGS)
@argument("src", type=ClickRepo())
@argument("dest", type=ClickRepo())
@option(
    "--src-password",
    type=SecretStr(),
    default=RESTIC_PASSWORD,
    help="Restic source password",
)
@option(
    "--src-password-file",
    type=Path(exist="file if exists"),
    default=RESTIC_PASSWORD_FILE,
    help="Restic source password file",
)
@option(
    "--dest-password",
    type=SecretStr(),
    default=RESTIC_PASSWORD,
    help="Restic destination password",
)
@option(
    "--dest-password-file",
    type=Path(exist="file if exists"),
    default=RESTIC_PASSWORD_FILE,
    help="Restic destination password file",
)
@tag_option
@sleep_option
def copy_sub_cmd(
    *,
    src: Repo,
    dest: Repo,
    src_password: SecretLike | None,
    src_password_file: PathLike | None,
    dest_password: SecretLike | None,
    dest_password_file: PathLike | None,
    tag: MaybeSequenceStr | None,
    sleep: Duration | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    copy(
        src,
        dest,
        src_password=src_password,
        src_password_file=src_password_file,
        dest_password=dest_password,
        dest_password_file=dest_password_file,
        tag=tag,
        sleep=sleep,
    )


@cli.command(name="forget", **CONTEXT_SETTINGS)
@repo_argument
@password_option
@password_file_option
@dry_run_option
@keep_last_option
@keep_hourly_option
@keep_daily_option
@keep_weekly_option
@keep_monthly_option
@keep_yearly_option
@keep_within_option
@keep_within_hourly_option
@keep_within_daily_option
@keep_within_weekly_option
@keep_within_monthly_option
@keep_within_yearly_option
@group_by_option
@prune_option
@repack_cacheable_only_option
@repack_small_option
@repack_uncompressed_option
@tag_option
def forget_sub_cmd(
    *,
    repo: Repo,
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
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    forget(
        repo,
        password=password,
        password_file=password_file,
        dry_run=dry_run,
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
        tag=tag,
    )


@cli.command(name="restore", **CONTEXT_SETTINGS)
@repo_argument
@argument("target", type=Path(exist=False))
@password_option
@password_file_option
@option(
    "--delete",
    is_flag=True,
    default=False,
    help="Delete files from target directory if they do not exist in snapshot",
)
@dry_run_option
@exclude_option
@exclude_i_option
@include_option
@include_i_option
@option(
    "--tag",
    type=ListStrs(),
    default=None,
    help='Only consider snapshots including `tag[,tag,...]`, when snapshot ID "latest" is given',
)
@option("--snapshot", type=Str(), default=LATEST, help="Snapshot ID to restore")
def restore_sub_cmd(
    *,
    repo: Repo,
    target: PathLike,
    password: SecretLike | None,
    password_file: PathLike | None,
    delete: bool,
    dry_run: bool,
    exclude: MaybeSequenceStr | None,
    exclude_i: MaybeSequenceStr | None,
    include: MaybeSequenceStr | None,
    include_i: MaybeSequenceStr | None,
    tag: MaybeSequenceStr | None,
    snapshot: str,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    restore(
        repo,
        target,
        password=password,
        password_file=password_file,
        delete=delete,
        dry_run=dry_run,
        exclude=exclude,
        exclude_i=exclude_i,
        include=include,
        include_i=include_i,
        tag=tag,
        snapshot=snapshot,
    )


@cli.command(name="snapshots", **CONTEXT_SETTINGS)
@repo_argument
@password_option
@password_file_option
def snapshots_sub_cmd(
    *, repo: Repo, password: SecretLike | None, password_file: PathLike | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    snapshots(repo, password=password, password_file=password_file)


@cli.command(name="unlock", **CONTEXT_SETTINGS)
@repo_argument
@password_option
@password_file_option
@option(
    "--remove-all",
    is_flag=True,
    default=False,
    help="Remove all locks, even non-stale ones",
)
def unlock_sub_cmd(
    *,
    repo: Repo,
    password: SecretLike | None,
    password_file: PathLike | None,
    remove_all: bool,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    unlock(repo, password=password, password_file=password_file, remove_all=remove_all)


if __name__ == "__main__":
    cli()
