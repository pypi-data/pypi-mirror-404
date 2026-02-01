from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, assert_never, override

from pydantic import SecretStr
from utilities.core import TemporaryFile, always_iterable, yield_temp_environ
from utilities.pydantic import extract_secret

from restic._constants import (
    RESTIC_PASSWORD,
    RESTIC_PASSWORD_FILE,
    RESTIC_PASSWORD_FILE_ENV_VAR,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from utilities.types import MaybeSequenceStr, PathLike, SecretLike


def expand_bool(flag: str, /, *, bool_: bool = False) -> list[str]:
    return [f"--{flag}"] if bool_ else []


def expand_dry_run(*, dry_run: bool = False) -> list[str]:
    return expand_bool("dry-run", bool_=dry_run)


def expand_exclude(*, exclude: MaybeSequenceStr | None = None) -> list[str]:
    return _expand_list("exclude", arg=exclude)


def expand_exclude_i(*, exclude_i: MaybeSequenceStr | None = None) -> list[str]:
    return _expand_list("iexclude", arg=exclude_i)


def expand_group_by(*, group_by: MaybeSequenceStr | None = None) -> list[str]:
    return [] if group_by is None else ["--group-by", ",".join(group_by)]


def expand_include(*, include: MaybeSequenceStr | None = None) -> list[str]:
    return _expand_list("include", arg=include)


def expand_include_i(*, include_i: MaybeSequenceStr | None = None) -> list[str]:
    return _expand_list("iinclude", arg=include_i)


def expand_keep(freq: str, /, *, n: int | None = None) -> list[str]:
    return [] if n is None else [f"--keep-{freq}", str(n)]


def expand_keep_within(freq: str, /, *, duration: str | None = None) -> list[str]:
    return [] if duration is None else [f"--keep-{freq}", duration]


def expand_read_concurrency(n: int, /) -> list[str]:
    return ["--read-concurrency", str(n)]


def expand_tag(*, tag: MaybeSequenceStr | None = None) -> list[str]:
    return _expand_list("tag", arg=tag)


def expand_target(target: PathLike, /) -> list[str]:
    return ["--target", str(target)]


##


@contextmanager
def yield_password(
    *,
    password: SecretLike | None = RESTIC_PASSWORD,
    password_file: PathLike | None = RESTIC_PASSWORD_FILE,
    env_var: str = RESTIC_PASSWORD_FILE_ENV_VAR,
) -> Iterator[None]:
    match password, password_file:
        case SecretStr() | str(), _:
            with (
                TemporaryFile(text=extract_secret(password)) as temp,
                yield_temp_environ({env_var: str(temp)}),
            ):
                yield
        case _, Path() | str():
            with yield_temp_environ({env_var: str(password_file)}):
                yield
        case None, None:
            raise YieldPasswordError
        case never:
            assert_never(never)


@dataclass(order=True, unsafe_hash=True, kw_only=True, slots=True)
class YieldPasswordError(Exception):
    @override
    def __str__(self) -> str:
        return "At least 1 of 'password' and/or 'password_file' must be given"


##


def _expand_list(flag: str, /, *, arg: MaybeSequenceStr | None = None) -> list[str]:
    result: list[str] = []
    if arg is not None:
        for a in always_iterable(arg):
            result.extend([f"--{flag}", a])
    return result


__all__ = [
    "YieldPasswordError",
    "expand_bool",
    "expand_dry_run",
    "expand_exclude",
    "expand_exclude_i",
    "expand_group_by",
    "expand_include",
    "expand_include_i",
    "expand_keep",
    "expand_keep_within",
    "expand_read_concurrency",
    "expand_tag",
    "expand_target",
    "yield_password",
]
