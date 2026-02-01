from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

from pydantic import TypeAdapter
from utilities.core import to_logger
from utilities.subprocess import run
from utilities.types import PathLike

from restic._constants import RESTIC_PASSWORD, RESTIC_PASSWORD_FILE
from restic._models import Snapshot
from restic._repo import Repo
from restic._utilities import yield_password

if TYPE_CHECKING:
    from utilities.types import PathLike, SecretLike

    from restic._repo import Repo


_LOGGER = to_logger(__name__)


@overload
def snapshots(
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    return_: Literal[True],
    print: bool = False,
) -> list[Snapshot]: ...
@overload
def snapshots(
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    return_: Literal[False] = False,
    print: bool = False,
) -> None: ...
@overload
def snapshots(
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    return_: bool = False,
    print: bool = False,
) -> list[Snapshot] | None: ...
def snapshots(
    repo: Repo,
    /,
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    return_: bool = False,
    print: bool = False,  # noqa: A002
) -> list[Snapshot] | None:
    _LOGGER.info("Listing snapshots in %s...", repo)
    args: list[str] = ["restic", "snapshots"]
    if return_:
        args.append("--json")
    with (
        repo.yield_env(),
        yield_password(password=password, password_file=password_file),
    ):
        result = run(*args, print=print, return_=return_)
    _LOGGER.info("Finished listing snapshots in %s", repo)
    return None if result is None else TypeAdapter(list[Snapshot]).validate_json(result)


__all__ = ["snapshots"]
