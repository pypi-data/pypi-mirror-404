from __future__ import annotations

from typing import assert_never, override

from click import Context, Parameter, ParamType, argument, option
from utilities.click import ListStrs, Path, SecretStr

from restic._constants import RESTIC_PASSWORD, RESTIC_PASSWORD_FILE
from restic._repo import (
    SFTP,
    Backblaze,
    Local,
    ParseRepoBackblazeError,
    Repo,
    RepoLike,
    parse_repo,
)

# parameters


class ClickRepo(ParamType):
    name = "repo"

    @override
    def __repr__(self) -> str:
        return self.name.upper()

    @override
    def convert(
        self, value: RepoLike, param: Parameter | None, ctx: Context | None
    ) -> Repo:
        match value:
            case Backblaze() | Local() | SFTP():
                return value
            case str():
                try:
                    return parse_repo(value)
                except ParseRepoBackblazeError as error:
                    return self.fail(str(error), param, ctx)
            case never:
                assert_never(never)


# options


dry_run_option = option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Just print what would have been done",
)
password_option = option(
    "--password", type=SecretStr(), default=RESTIC_PASSWORD, help="Restic password"
)
password_file_option = option(
    "--password-file",
    type=Path(exist="file if exists"),
    default=RESTIC_PASSWORD_FILE,
    help="Restic password file",
)
repo_argument = argument("repo", type=ClickRepo())
sleep_option = option(
    "--sleep", type=int, default=None, help="Sleep after a successful run"
)
tag_option = option(
    "--tag",
    type=ListStrs(),
    default=None,
    help="Only consider snapshots including tag[,tag,...]",
)


# options - backup


exclude_option = option(
    "--exclude", type=ListStrs(), default=None, help="Exclude a pattern"
)
exclude_i_option = option(
    "--exclude-i",
    type=ListStrs(),
    default=None,
    help="Exclude a pattern but ignores the casing of filenames",
)
include_option = option(
    "--include", type=ListStrs(), default=None, help="Include a pattern"
)
include_i_option = option(
    "--include-i",
    type=ListStrs(),
    default=None,
    help="Include a pattern but ignores the casing of filenames",
)


# options - forget


keep_last_option = option(
    "--keep-last", type=int, default=None, help="Keep the last n snapshots"
)
keep_hourly_option = option(
    "--keep-hourly", type=int, default=None, help="Keep the last n hourly snapshots"
)
keep_daily_option = option(
    "--keep-daily", type=int, default=None, help="Keep the last n daily snapshots"
)
keep_weekly_option = option(
    "--keep-weekly", type=int, default=None, help="Keep the last n weekly snapshots"
)
keep_monthly_option = option(
    "--keep-monthly", type=int, default=None, help="Keep the last n monthly snapshots"
)
keep_yearly_option = option(
    "--keep-yearly", type=int, default=None, help="Keep the last n yearly snapshots"
)
keep_within_option = option(
    "--keep-within",
    type=str,
    default=None,
    help="Keep snapshots that are newer than duration relative to the latest snapshot",
)
keep_within_hourly_option = option(
    "--keep-within-hourly",
    type=str,
    default=None,
    help="Keep hourly snapshots that are newer than duration relative to the latest snapshot",
)
keep_within_daily_option = option(
    "--keep-within-daily",
    type=str,
    default=None,
    help="Keep daily snapshots that are newer than duration relative to the latest snapshot",
)
keep_within_weekly_option = option(
    "--keep-within-weekly",
    type=str,
    default=None,
    help="Keep weekly snapshots that are newer than duration relative to the latest snapshot",
)
keep_within_monthly_option = option(
    "--keep-within-monthly",
    type=str,
    default=None,
    help="Keep monthly snapshots that are newer than duration relative to the latest snapshot",
)
keep_within_yearly_option = option(
    "--keep-within-yearly",
    type=str,
    default=None,
    help="Keep yearly snapshots that are newer than duration relative to the latest snapshot",
)
group_by_option = option(
    "--group-by",
    type=ListStrs(),
    default=None,
    help="Group snapshots by host, paths and/or tags",
)
prune_option = option(
    "--prune",
    is_flag=True,
    default=True,
    help="Automatically run the 'prune' command if snapshots have been removed",
)
repack_cacheable_only_option = option(
    "--repack-cacheable-only",
    is_flag=True,
    default=False,
    help="Only repack packs which are cacheable",
)
repack_small_option = option(
    "--repack-small",
    is_flag=True,
    default=True,
    help="Repack pack files below 80% of target pack size",
)
repack_uncompressed_option = option(
    "--repack-uncompressed",
    is_flag=True,
    default=True,
    help="Repack all uncompressed data",
)


__all__ = [
    "ClickRepo",
    "dry_run_option",
    "exclude_i_option",
    "exclude_option",
    "group_by_option",
    "include_i_option",
    "include_option",
    "keep_daily_option",
    "keep_hourly_option",
    "keep_last_option",
    "keep_monthly_option",
    "keep_weekly_option",
    "keep_within_daily_option",
    "keep_within_hourly_option",
    "keep_within_monthly_option",
    "keep_within_option",
    "keep_within_weekly_option",
    "keep_within_yearly_option",
    "keep_yearly_option",
    "password_file_option",
    "password_option",
    "prune_option",
    "repack_cacheable_only_option",
    "repack_small_option",
    "repack_uncompressed_option",
    "repo_argument",
    "sleep_option",
    "tag_option",
]
