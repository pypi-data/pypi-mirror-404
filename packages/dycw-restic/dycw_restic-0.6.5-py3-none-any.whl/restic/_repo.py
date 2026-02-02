from __future__ import annotations

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from re import search
from typing import TYPE_CHECKING, Self, override

from utilities.core import (
    ExtractGroupError,
    ExtractGroupsError,
    GetEnvError,
    extract_group,
    extract_groups,
    get_env,
    yield_temp_environ,
)
from utilities.pydantic import ensure_secret

from restic._constants import (
    BACKBLAZE_APPLICATION_KEY,
    BACKBLAZE_APPLICATION_KEY_ENV_VAR,
    BACKBLAZE_KEY_ID,
    BACKBLAZE_KEY_ID_ENV_VAR,
    RESTIC_REPOSITORY_ENV_VAR,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import SecretStr
    from utilities.types import SecretLike


type Repo = Backblaze | Local | SFTP
type RepoLike = Repo | str


##


@dataclass(order=True, slots=True)
class Backblaze:
    """A Backblaze repo."""

    key_id: SecretStr
    application_key: SecretStr
    bucket: str
    path: Path

    @override
    def __eq__(self, other: object, /) -> bool:
        return (
            isinstance(other, type(self))
            and (self.key_id.get_secret_value() == other.key_id.get_secret_value())
            and (
                self.application_key.get_secret_value()
                == other.application_key.get_secret_value()
            )
            and (self.bucket == other.bucket)
            and (self.path == other.path)
        )

    @override
    def __hash__(self) -> int:
        return hash((
            self.key_id.get_secret_value(),
            self.application_key.get_secret_value(),
            self.bucket,
            self.path,
        ))

    @classmethod
    def parse(
        cls,
        text: str,
        /,
        *,
        key_id: SecretLike | None = BACKBLAZE_KEY_ID,
        application_key: SecretLike | None = BACKBLAZE_APPLICATION_KEY,
    ) -> Self:
        if key_id is None:
            try:
                key_id_use = get_env(BACKBLAZE_KEY_ID_ENV_VAR)
            except GetEnvError:
                raise BackblazeKeyIdMissingError from None
        else:
            key_id_use = key_id
        if application_key is None:
            try:
                application_key_use = get_env(BACKBLAZE_APPLICATION_KEY_ENV_VAR)
            except GetEnvError:
                raise BackblazeApplicationKeyMissingError from None
        else:
            application_key_use = application_key
        pattern = r"^b2:([^@:]+):([^@+]+)$"
        try:
            bucket, path = extract_groups(pattern, text)
        except ExtractGroupsError:
            raise BackblazeInvalidStrError(pattern=pattern, text=text) from None
        return cls(
            key_id=ensure_secret(key_id_use),
            application_key=ensure_secret(application_key_use),
            bucket=bucket,
            path=Path(path),
        )

    @property
    def repository(self) -> str:
        return f"b2:{self.bucket}:{self.path}"

    @contextmanager
    def yield_env(self, env_var: str = RESTIC_REPOSITORY_ENV_VAR, /) -> Iterator[None]:
        with yield_temp_environ(
            {env_var: self.repository},
            B2_ACCOUNT_ID=self.key_id.get_secret_value(),
            B2_ACCOUNT_KEY=self.application_key.get_secret_value(),
        ):
            yield


@dataclass(order=True, unsafe_hash=True, kw_only=True, slots=True)
class BackblazeParseError(Exception): ...


@dataclass(order=True, unsafe_hash=True, kw_only=True, slots=True)
class BackblazeKeyIdMissingError(BackblazeParseError):
    @override
    def __str__(self) -> str:
        return f"Key ID missing; use env var {BACKBLAZE_KEY_ID_ENV_VAR!r}"


@dataclass(order=True, unsafe_hash=True, kw_only=True, slots=True)
class BackblazeApplicationKeyMissingError(BackblazeParseError):
    @override
    def __str__(self) -> str:
        return f"Application key missing; use env var {BACKBLAZE_APPLICATION_KEY_ENV_VAR!r})"


@dataclass(order=True, unsafe_hash=True, kw_only=True, slots=True)
class BackblazeInvalidStrError(BackblazeParseError):
    pattern: str
    text: str

    @override
    def __str__(self) -> str:
        return f"Text must be of the form {self.pattern!r}; got {self.text!r}"


##


@dataclass(order=True, unsafe_hash=True, slots=True)
class Local:
    """A local repo."""

    path: Path

    @classmethod
    def parse(cls, text: str, /) -> Self:
        pattern = r"^local:([^@:]+)$"
        try:
            path = extract_group(pattern, text)
        except ExtractGroupError:
            raise LocalParseError(pattern=pattern, text=text) from None
        return cls(Path(path))

    @property
    def repository(self) -> str:
        return f"local:{self.path}"

    @contextmanager
    def yield_env(self, env_var: str = RESTIC_REPOSITORY_ENV_VAR, /) -> Iterator[None]:
        with yield_temp_environ({env_var: self.repository}):
            yield


@dataclass(order=True, unsafe_hash=True, kw_only=True, slots=True)
class LocalParseError(Exception):
    pattern: str
    text: str

    @override
    def __str__(self) -> str:
        return f"Text must be of the form {self.pattern!r}; got {self.text!r}"


##


@dataclass(order=True, unsafe_hash=True, slots=True)
class SFTP:
    """An SFTP repo."""

    user: str
    hostname: str
    path: Path

    @classmethod
    def parse(cls, text: str, /) -> Self:
        pattern = r"^sftp:([^@:]+)@([^@:]+):([^@:]+)$"
        try:
            user, hostname, path = extract_groups(pattern, text)
        except ExtractGroupsError:
            raise SFTPParseError(pattern=pattern, text=text) from None
        return cls(user, hostname, Path(path))

    @property
    def repository(self) -> str:
        return f"sftp:{self.user}@{self.hostname}:{self.path}"

    @contextmanager
    def yield_env(self, env_var: str = RESTIC_REPOSITORY_ENV_VAR, /) -> Iterator[None]:
        with yield_temp_environ({env_var: self.repository}):
            yield


@dataclass(order=True, unsafe_hash=True, kw_only=True, slots=True)
class SFTPParseError(Exception):
    pattern: str
    text: str

    @override
    def __str__(self) -> str:
        return f"Text must be of the form {self.pattern!r}; got {self.text!r}"


##


def parse_repo(text: str, /) -> Repo:
    try:
        return Backblaze.parse(text)
    except BackblazeParseError as error:
        if search("b2", text):
            raise ParseRepoBackblazeError(text=str(error)) from None
    with suppress(SFTPParseError):
        return SFTP.parse(text)
    try:
        return Local.parse(text)
    except LocalParseError:
        return Local(Path(text))


@dataclass(order=True, unsafe_hash=True, kw_only=True, slots=True)
class ParseRepoBackblazeError(Exception):
    text: str

    @override
    def __str__(self) -> str:
        return self.text


##


__all__ = [
    "SFTP",
    "Backblaze",
    "BackblazeApplicationKeyMissingError",
    "BackblazeInvalidStrError",
    "BackblazeKeyIdMissingError",
    "BackblazeParseError",
    "Local",
    "LocalParseError",
    "ParseRepoBackblazeError",
    "Repo",
    "RepoLike",
    "SFTPParseError",
    "parse_repo",
]
