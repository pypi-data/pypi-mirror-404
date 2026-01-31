from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, assert_never

import utilities.subprocess
from utilities.core import (
    Permissions,
    PermissionsLike,
    ReadTextError,
    always_iterable,
    extract_groups,
    normalize_str,
    read_text,
    to_logger,
    write_text,
)
from utilities.pydantic import extract_secret
from utilities.subprocess import uv_tool_run_cmd

if TYPE_CHECKING:
    from collections.abc import Callable

    from utilities.shellingham import Shell
    from utilities.types import MaybeSequenceStr, PathLike, Retry, SecretLike


_LOGGER = to_logger(__name__)


##


def ensure_line_or_lines(
    path: PathLike,
    line_or_lines: MaybeSequenceStr,
    /,
    *,
    perms: PermissionsLike | None = None,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    text = normalize_str("\n".join(always_iterable(line_or_lines)))
    try:
        contents = read_text(path)
    except ReadTextError:
        write_text(path, text, perms=perms, owner=owner, group=group)
        return
    if text not in contents:
        with Path(path).open(mode="a") as fh:
            _ = fh.write(f"\n\n{text}")


##


def setup_local_or_remote(
    cmd: str,
    setup_local: Callable[[], None],
    /,
    *,
    ssh: str | None = None,
    force: bool = False,
    etc: bool = False,
    group: str | int | None = None,
    home: PathLike | None = None,
    owner: str | int | None = None,
    path_binaries: PathLike | None = None,
    perms: PermissionsLike | None = None,
    perms_binary: PermissionsLike | None = None,
    perms_config: PermissionsLike | None = None,
    root: PathLike | None = None,
    shell: Shell | None = None,
    starship_toml: PathLike | None = None,
    sudo: bool = False,
    token: SecretLike | None = None,
    user: str | None = None,
    retry: Retry | None = None,
) -> None:
    match ssh:
        case None:
            if (shutil.which(cmd) is None) or force:
                _LOGGER.info("Setting up %r...", cmd)
                setup_local()
            else:
                _LOGGER.info("%r is already set up", cmd)
        case str():
            ssh_user, ssh_hostname = split_ssh(ssh)
            _LOGGER.info("Setting up %r on %r...", cmd, ssh_hostname)
            args: list[str] = []
            if etc:
                args.append("--etc")
            if force:
                args.append("--force")
            if group is not None:
                args.extend(["--group", str(group)])
            if home is not None:
                args.extend(["--home", str(home)])
            if owner is not None:
                args.extend(["--owner", str(owner)])
            if path_binaries is not None:
                args.extend(["--path-binaries", str(path_binaries)])
            if perms is not None:
                args.extend(["--perms", str(Permissions.new(perms))])
            if perms_binary is not None:
                args.extend(["--perms-binary", str(Permissions.new(perms_binary))])
            if perms_config is not None:
                args.extend(["--perms-config", str(Permissions.new(perms_config))])
            if root is not None:
                args.extend(["--root", str(root)])
            if shell is not None:
                args.extend(["--shell", shell])
            if starship_toml is not None:
                args.extend(["--starship-toml", str(starship_toml)])
            if sudo:
                args.append("--sudo")
            if token is not None:
                args.extend(["--token", extract_secret(token)])
            if user is not None:
                args.extend(["--user", user])
            utilities.subprocess.ssh(
                ssh_user,
                ssh_hostname,
                *uv_tool_run_cmd(
                    "cli", cmd, *args, from_="dycw-installer[cli]", latest=True
                ),
                retry=retry,
                logger=_LOGGER,
            )
        case never:
            assert_never(never)


##


def split_ssh(text: str, /) -> tuple[str, str]:
    user, hostname = extract_groups(r"(.+)@(.+)$", text)
    return user, hostname


##


def ssh_uv_install(
    ssh: str,
    cmd: str,
    /,
    *args: str,
    etc: bool = False,
    group: str | int | None = None,
    home: PathLike | None = None,
    owner: str | int | None = None,
    path_binaries: PathLike | None = None,
    perms: PermissionsLike | None = None,
    perms_binary: PermissionsLike | None = None,
    perms_config: PermissionsLike | None = None,
    root: PathLike | None = None,
    shell: Shell | None = None,
    starship_toml: PathLike | None = None,
    sudo: bool = False,
    token: SecretLike | None = None,
    user: str | None = None,
    retry: Retry | None = None,
) -> None:
    ssh_user, ssh_hostname = split_ssh(ssh)
    _LOGGER.info("Setting up %r on %r...", cmd, ssh_hostname)
    parts: list[str] = []
    if etc:
        parts.append("--etc")
    if group is not None:
        parts.extend(["--group", str(group)])
    if home is not None:
        parts.extend(["--home", str(home)])
    if owner is not None:
        parts.extend(["--owner", str(owner)])
    if path_binaries is not None:
        parts.extend(["--path-binaries", str(path_binaries)])
    if perms is not None:
        parts.extend(["--perms", str(Permissions.new(perms))])
    if perms_binary is not None:
        parts.extend(["--perms-binary", str(Permissions.new(perms_binary))])
    if perms_config is not None:
        parts.extend(["--perms-config", str(Permissions.new(perms_config))])
    if root is not None:
        parts.extend(["--root", str(root)])
    if shell is not None:
        parts.extend(["--shell", shell])
    if starship_toml is not None:
        parts.extend(["--starship-toml", str(starship_toml)])
    if sudo:
        parts.append("--sudo")
    if token is not None:
        parts.extend(["--token", extract_secret(token)])
    if user is not None:
        parts.extend(["--user", user])
    utilities.subprocess.ssh(
        ssh_user,
        ssh_hostname,
        *uv_tool_run_cmd(
            "cli", cmd, *parts, *args, from_="dycw-installer[cli]", latest=True
        ),
        retry=retry,
        logger=_LOGGER,
    )


__all__ = ["ensure_line_or_lines", "split_ssh", "ssh_uv_install"]
