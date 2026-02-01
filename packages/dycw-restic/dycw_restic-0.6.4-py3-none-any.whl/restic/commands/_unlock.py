from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import to_logger
from utilities.subprocess import run
from utilities.types import PathLike

from restic._constants import RESTIC_PASSWORD, RESTIC_PASSWORD_FILE
from restic._repo import Repo
from restic._utilities import expand_bool, yield_password

if TYPE_CHECKING:
    from utilities.types import PathLike, SecretLike

    from restic._repo import Repo


_LOGGER = to_logger(__name__)


def unlock(
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    remove_all: bool = False,
) -> None:
    _LOGGER.info("Unlocking %s...", repo)
    with (
        repo.yield_env(),
        yield_password(password=password, password_file=password_file),
    ):
        run(
            "restic", "unlock", *expand_bool("remove-all", bool_=remove_all), print=True
        )
    _LOGGER.info("Finished unlocking %s", repo)


__all__ = ["unlock"]
