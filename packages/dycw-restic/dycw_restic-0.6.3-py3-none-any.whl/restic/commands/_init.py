from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import to_logger
from utilities.subprocess import run

from restic._constants import RESTIC_PASSWORD, RESTIC_PASSWORD_FILE
from restic._utilities import yield_password

if TYPE_CHECKING:
    from utilities.types import PathLike, SecretLike

    from restic._repo import Repo


_LOGGER = to_logger(__name__)


def init(
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
) -> None:
    _LOGGER.info("Initializing %s...", repo)
    with (
        repo.yield_env(),
        yield_password(password=password, password_file=password_file),
    ):
        run("restic", "init", print=True)
    _LOGGER.info("Finished initializing %s", repo)


__all__ = ["init"]
