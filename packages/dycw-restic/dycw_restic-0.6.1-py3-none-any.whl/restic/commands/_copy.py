from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import duration_to_seconds, sync_sleep, to_logger
from utilities.subprocess import run
from whenever import TimeDelta

from restic._constants import (
    RESTIC_DEST_PASSWORD,
    RESTIC_DEST_PASSWORD_FILE,
    RESTIC_SRC_PASSWORD,
    RESTIC_SRC_PASSWORD_FILE,
)
from restic._utilities import expand_tag, yield_password

if TYPE_CHECKING:
    from utilities.types import Duration, MaybeSequenceStr, PathLike, SecretLike

    from restic._repo import Repo


_LOGGER = to_logger(__name__)


def copy(
    src: Repo,
    dest: Repo,
    /,
    *,
    src_password: SecretLike | None = RESTIC_SRC_PASSWORD,
    src_password_file: PathLike | None = RESTIC_SRC_PASSWORD_FILE,
    dest_password: SecretLike | None = RESTIC_DEST_PASSWORD,
    dest_password_file: PathLike | None = RESTIC_DEST_PASSWORD_FILE,
    tag: MaybeSequenceStr | None = None,
    sleep: Duration | None = None,
) -> None:
    _LOGGER.info("Copying snapshots from %s to %s...", src, dest)
    with (
        src.yield_env("RESTIC_FROM_REPOSITORY"),
        dest.yield_env(),
        yield_password(
            password=src_password,
            password_file=src_password_file,
            env_var="RESTIC_FROM_PASSWORD_FILE",
        ),
        yield_password(password=dest_password, password_file=dest_password_file),
    ):
        run("restic", "copy", *expand_tag(tag=tag), print=True)
    if sleep is None:
        _LOGGER.info("Finished copying snapshots from %r to %r", src, dest)
    else:
        delta = TimeDelta(seconds=duration_to_seconds(sleep))
        _LOGGER.info(
            "Finished copying snapshots from %s to %s; sleeping for %s...",
            src,
            dest,
            delta,
        )
        sync_sleep(sleep)
        _LOGGER.info("Finishing sleeping for %s", delta)


__all__ = ["copy"]
