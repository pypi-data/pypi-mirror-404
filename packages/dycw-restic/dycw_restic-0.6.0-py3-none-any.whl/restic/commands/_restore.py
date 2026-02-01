from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import TemporaryDirectory, one, to_logger
from utilities.subprocess import cp, run

from restic._constants import LATEST, RESTIC_PASSWORD, RESTIC_PASSWORD_FILE
from restic._utilities import (
    expand_bool,
    expand_dry_run,
    expand_exclude,
    expand_exclude_i,
    expand_include,
    expand_include_i,
    expand_tag,
    expand_target,
    yield_password,
)
from restic.commands._snapshots import snapshots

if TYPE_CHECKING:
    from utilities.types import MaybeSequenceStr, PathLike, SecretLike

    from restic._repo import Repo


_LOGGER = to_logger(__name__)


def restore(
    repo: Repo,
    target: PathLike,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    delete: bool = False,
    dry_run: bool = False,
    exclude: MaybeSequenceStr | None = None,
    exclude_i: MaybeSequenceStr | None = None,
    include: MaybeSequenceStr | None = None,
    include_i: MaybeSequenceStr | None = None,
    tag: MaybeSequenceStr | None = None,
    snapshot: str = LATEST,
) -> None:
    _LOGGER.info("Restoring snapshot %s of %s to %r...", snapshot, repo, str(target))
    with (
        repo.yield_env(),
        yield_password(password=password, password_file=password_file),
        TemporaryDirectory() as temp,
    ):
        run(
            "restic",
            "restore",
            *expand_bool("delete", bool_=delete),
            *expand_dry_run(dry_run=dry_run),
            *expand_exclude(exclude=exclude),
            *expand_exclude_i(exclude_i=exclude_i),
            *expand_include(include=include),
            *expand_include_i(include_i=include_i),
            *expand_tag(tag=tag),
            *expand_target(temp),
            "--verify",
            snapshot,
            print=True,
        )
        snaps = snapshots(repo, password=password, return_=True)
        path = one(snaps[-1].paths)
        src = temp / path.relative_to(path.anchor)
        cp(src, target)
    _LOGGER.info(
        "Finished restoring snapshot %s of %s to %r", snapshot, repo, str(target)
    )


__all__ = ["restore"]
