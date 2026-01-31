from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import utilities.subprocess
from utilities.constants import HOME, PWD
from utilities.core import always_iterable, to_logger, write_text
from utilities.subprocess import HOST_KEY_ALGORITHMS, cp, ssh_keyscan

from installer.clone.constants import GIT_CLONE_HOST
from installer.configs.lib import setup_ssh_config

if TYPE_CHECKING:
    from collections.abc import Iterator

    from utilities.types import PathLike, Retry


_LOGGER = to_logger(__name__)


##


def git_clone(
    key: PathLike,
    owner: str,
    repo: str,
    /,
    *,
    home: PathLike = HOME,
    host: str = GIT_CLONE_HOST,
    retry: Retry | None = None,
    port: int | None = None,
    dest: PathLike = PWD,
    branch: str | None = None,
) -> None:
    _LOGGER.info("Cloning repository...")
    setup_ssh_config(home=home)
    _set_up_deploy_key(key, home=home)
    _set_up_ssh_conf(key, home=home, host=host, port=port)
    _set_up_known_hosts(  # last step
        host=host, home=home, retry=retry, port=port
    )
    stem = Path(key).stem
    utilities.subprocess.git_clone(f"git@{stem}:{owner}/{repo}", dest, branch=branch)


def _set_up_deploy_key(path: PathLike, /, *, home: PathLike = HOME) -> None:
    _LOGGER.info("Setting up deploy key...")
    dest = _get_path_deploy_key(path, home=home)
    cp(path, dest, perms="u=rw,g=,o=")


def _get_path_deploy_key(path: PathLike, /, *, home: PathLike = HOME) -> Path:
    stem = Path(path).stem
    return Path(home, ".ssh/deploy-keys", stem)


def _set_up_known_hosts(
    *,
    host: str = GIT_CLONE_HOST,
    home: PathLike = HOME,
    retry: Retry | None = None,
    port: int | None = None,
) -> None:
    _LOGGER.info("Setting up known hosts...")
    ssh_keyscan(host, path=Path(home, ".ssh/known_hosts"), retry=retry, port=port)


def _set_up_ssh_conf(
    path: PathLike,
    /,
    *,
    home: PathLike = HOME,
    host: str = GIT_CLONE_HOST,
    port: int | None = None,
) -> None:
    _LOGGER.info("Setting up ...")
    config = _get_path_conf(path, home=home)
    text = "\n".join(_yield_conf_lines(path, home=home, host=host, port=port))
    write_text(config, text, overwrite=True)


def _get_path_conf(path: PathLike, /, *, home: PathLike = HOME) -> Path:
    stem = Path(path).stem
    return Path(home, f".ssh/config.d/{stem}.conf")


def _yield_conf_lines(
    path: PathLike,
    /,
    *,
    home: PathLike = HOME,
    host: str = GIT_CLONE_HOST,
    port: int | None = None,
) -> Iterator[str]:
    stem = Path(path).stem
    yield f"Host {stem}"
    for line in _yield_conf_lines_core(path, home=home, host=host, port=port):
        yield f"    {line}"


def _yield_conf_lines_core(
    path: PathLike,
    /,
    *,
    home: PathLike = HOME,
    host: str = GIT_CLONE_HOST,
    port: int | None = None,
) -> Iterator[str]:
    yield "User git"
    yield f"HostName {host}"
    if port is not None:
        yield f"Port {port}"
    yield f"IdentityFile {_get_path_deploy_key(path, home=home)}"
    yield "IdentitiesOnly yes"
    yield "BatchMode yes"
    yield f"HostKeyAlgorithms {','.join(always_iterable(HOST_KEY_ALGORITHMS))}"
    yield "StrictHostKeyChecking yes"


__all__ = ["git_clone"]
