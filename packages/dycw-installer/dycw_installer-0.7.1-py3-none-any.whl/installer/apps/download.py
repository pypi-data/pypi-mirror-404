from __future__ import annotations

from contextlib import contextmanager
from re import IGNORECASE, search
from typing import TYPE_CHECKING, Any

from github import Github
from github.Auth import Token
from requests import get
from utilities.core import (
    OneNonUniqueError,
    TemporaryDirectory,
    one,
    to_logger,
    yield_bz2,
    yield_gzip,
    yield_lzma,
)
from utilities.inflect import counted_noun
from utilities.pydantic import extract_secret

from installer.apps.constants import (
    C_STD_LIB_GROUP,
    CHUNK_SIZE,
    GITHUB_TOKEN,
    MACHINE_TYPE_GROUP,
    SYSTEM_NAME_GROUP,
    TIMEOUT,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from utilities.types import MaybeSequenceStr, SecretLike


_LOGGER = to_logger(__name__)


##


@contextmanager
def yield_asset(
    owner: str,
    repo: str,
    /,
    *,
    tag: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    match_system: bool = False,
    match_c_std_lib: bool = False,
    match_machine: bool = False,
    not_matches: MaybeSequenceStr | None = None,
    endswith: MaybeSequenceStr | None = None,
    not_endswith: MaybeSequenceStr | None = None,
) -> Iterator[Path]:
    """Yield a GitHub asset."""
    _LOGGER.info("Yielding asset...")
    gh = Github(auth=None if token is None else Token(extract_secret(token)))
    repository = gh.get_repo(f"{owner}/{repo}")
    if tag is None:
        release = repository.get_latest_release()
    else:
        release = next(r for r in repository.get_releases() if search(tag, r.tag_name))
    assets = list(release.get_assets())
    _LOGGER.info("Got %s: %s", counted_noun(assets, "asset"), [a.name for a in assets])
    if match_system:
        assets = [
            a
            for a in assets
            if any(search(c, a.name, flags=IGNORECASE) for c in SYSTEM_NAME_GROUP)
        ]
        _LOGGER.info(
            "Post system name group %s, got %s: %s",
            SYSTEM_NAME_GROUP,
            counted_noun(assets, "asset"),
            [a.name for a in assets],
        )
    if match_c_std_lib and (C_STD_LIB_GROUP is not None):
        assets = [
            a
            for a in assets
            if any(search(c, a.name, flags=IGNORECASE) for c in C_STD_LIB_GROUP)
        ]
        _LOGGER.info(
            "Post 'match_c_std_lib' %s, got %s: %s",
            C_STD_LIB_GROUP,
            counted_noun(assets, "asset"),
            [a.name for a in assets],
        )
    if match_machine:
        assets = [
            a
            for a in assets
            if any(search(m, a.name, flags=IGNORECASE) for m in MACHINE_TYPE_GROUP)
        ]
        _LOGGER.info(
            "Post 'match_machine' %s, got %s: %s",
            MACHINE_TYPE_GROUP,
            counted_noun(assets, "asset"),
            [a.name for a in assets],
        )
    if not_matches is not None:
        assets = [
            a for a in assets if all(search(p, a.name) is None for p in not_matches)
        ]
        _LOGGER.info(
            "Post 'not_matches', got %s: %s",
            counted_noun(assets, "asset"),
            [a.name for a in assets],
        )
    if endswith is not None:
        assets = [a for a in assets if any(a.name.endswith(e) for e in endswith)]
        _LOGGER.info(
            "Post 'endswith', got %s: %s",
            counted_noun(assets, "asset"),
            [a.name for a in assets],
        )
    if not_endswith is not None:
        assets = [
            a for a in assets if all(not a.name.endswith(e) for e in not_endswith)
        ]
        _LOGGER.info(
            "Post 'not_endswith', got %s: %s",
            counted_noun(assets, "asset"),
            [a.name for a in assets],
        )
    try:
        asset = one(assets)
    except OneNonUniqueError as error:
        raise OneNonUniqueError(
            iterables=([a.name for a in assets],),
            first=error.first.name,
            second=error.second.name,
        ) from None
    headers: dict[str, Any] = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {extract_secret(token)}"
    with TemporaryDirectory() as temp_dir:
        with get(
            asset.browser_download_url, headers=headers, timeout=TIMEOUT, stream=True
        ) as resp:
            resp.raise_for_status()
            dest = temp_dir / asset.name
            with dest.open(mode="wb") as fh:
                fh.writelines(resp.iter_content(chunk_size=CHUNK_SIZE))
        _LOGGER.info("Yielding %r...", str(dest))
        yield dest


##


@contextmanager
def yield_bz2_asset(
    owner: str,
    repo: str,
    /,
    *,
    tag: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    match_system: bool = False,
    match_c_std_lib: bool = False,
    match_machine: bool = False,
    not_matches: MaybeSequenceStr | None = None,
    not_endswith: MaybeSequenceStr | None = None,
) -> Iterator[Path]:
    _LOGGER.info("Yielding BZ2 asset...")
    with (
        yield_asset(
            owner,
            repo,
            tag=tag,
            token=token,
            match_system=match_system,
            match_c_std_lib=match_c_std_lib,
            match_machine=match_machine,
            not_matches=not_matches,
            not_endswith=not_endswith,
        ) as temp1,
        yield_bz2(temp1) as temp2,
    ):
        yield temp2


##


@contextmanager
def yield_gzip_asset(
    owner: str,
    repo: str,
    /,
    *,
    tag: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    match_system: bool = False,
    match_c_std_lib: bool = False,
    match_machine: bool = False,
    not_matches: MaybeSequenceStr | None = None,
    endswith: MaybeSequenceStr | None = None,
    not_endswith: MaybeSequenceStr | None = None,
) -> Iterator[Path]:
    _LOGGER.info("Yielding Gzip asset...")
    with (
        yield_asset(
            owner,
            repo,
            tag=tag,
            token=token,
            match_system=match_system,
            match_c_std_lib=match_c_std_lib,
            match_machine=match_machine,
            not_matches=not_matches,
            endswith=endswith,
            not_endswith=not_endswith,
        ) as temp1,
        yield_gzip(temp1) as temp2,
    ):
        yield temp2


##


@contextmanager
def yield_lzma_asset(
    owner: str,
    repo: str,
    /,
    *,
    tag: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    match_system: bool = False,
    match_c_std_lib: bool = False,
    match_machine: bool = False,
    not_matches: MaybeSequenceStr | None = None,
    endswith: MaybeSequenceStr | None = None,
    not_endswith: MaybeSequenceStr | None = None,
) -> Iterator[Path]:
    _LOGGER.info("Yielding LZMA asset...")
    with (
        yield_asset(
            owner,
            repo,
            tag=tag,
            token=token,
            match_system=match_system,
            match_c_std_lib=match_c_std_lib,
            match_machine=match_machine,
            not_matches=not_matches,
            endswith=endswith,
            not_endswith=not_endswith,
        ) as temp1,
        yield_lzma(temp1) as temp2,
    ):
        yield temp2


__all__ = ["yield_asset", "yield_bz2_asset", "yield_gzip_asset", "yield_lzma_asset"]
