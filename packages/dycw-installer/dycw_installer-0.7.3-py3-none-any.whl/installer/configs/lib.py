from __future__ import annotations

from pathlib import Path
from shlex import join
from typing import TYPE_CHECKING, assert_never

import utilities.subprocess
from utilities.constants import HOME
from utilities.core import (
    PermissionsLike,
    always_iterable,
    normalize_multi_line_str,
    normalize_str,
    repr_str,
    to_logger,
    write_text,
)
from utilities.shellingham import SHELL, Shell
from utilities.subprocess import (
    BASH_LS,
    chmod,
    chmod_cmd,
    chown,
    chown_cmd,
    maybe_sudo_cmd,
    mkdir,
    mkdir_cmd,
    tee,
    tee_cmd,
)

from installer.configs.constants import FILE_SYSTEM_ROOT
from installer.utilities import ensure_line_or_lines, split_ssh

if TYPE_CHECKING:
    from utilities.types import MaybeSequenceStr, PathLike, Retry


_LOGGER = to_logger(__name__)


##


def setup_authorized_keys(
    keys: list[str],
    /,
    *,
    home: PathLike = HOME,
    ssh: str | None = None,
    sudo: bool = False,
    perms: PermissionsLike | None = None,
    owner: str | int | None = None,
    group: str | int | None = None,
    batch_mode: bool = False,
    retry: Retry | None = None,
) -> None:
    """Set up the SSH authorized keys."""
    _LOGGER.info("Setting up authorized keys...")
    path = Path(home, ".ssh/authorized_keys")
    text = normalize_str("\n".join(keys))
    if ssh is None:
        tee(path, text, sudo=sudo)
        if perms is not None:
            chmod(path, perms, sudo=sudo, recursive=True)
        if (owner is not None) or (group is not None):
            chown(path, sudo=sudo, recursive=True, user=owner, group=group)
    else:
        user, hostname = split_ssh(ssh)
        utilities.subprocess.ssh(
            user,
            hostname,
            *maybe_sudo_cmd(*tee_cmd(path), sudo=sudo),
            batch_mode=batch_mode,
            input=text,
            retry=retry,
            logger=_LOGGER,
        )
        if perms is not None:
            utilities.subprocess.ssh(
                user,
                hostname,
                *maybe_sudo_cmd(*chmod_cmd(path, perms, recursive=True), sudo=sudo),
                retry=retry,
                logger=_LOGGER,
            )
        if (owner is not None) or (group is not None):
            utilities.subprocess.ssh(
                user,
                hostname,
                *maybe_sudo_cmd(
                    *chown_cmd(path, recursive=True, user=owner, group=group), sudo=sudo
                ),
                retry=retry,
                logger=_LOGGER,
            )


##


def setup_shell_config(
    bash: MaybeSequenceStr,
    zsh: MaybeSequenceStr,
    fish: MaybeSequenceStr,
    /,
    *,
    etc: str | None = None,
    shell: Shell = SHELL,
    home: PathLike = HOME,
    perms: PermissionsLike | None = None,
    owner: str | int | None = None,
    group: str | int | None = None,
    root: PathLike = FILE_SYSTEM_ROOT,
) -> None:
    match etc, shell:
        case None, "bash" | "posix" | "sh":
            path = Path(home, ".bashrc")
            ensure_line_or_lines(path, bash, perms=perms, owner=owner, group=group)
        case None, "zsh":
            path = Path(home, ".zshrc")
            ensure_line_or_lines(path, zsh, perms=perms, owner=owner, group=group)
        case None, "fish":
            path = Path(home, ".config/fish/config.fish")
            ensure_line_or_lines(path, fish, perms=perms, owner=owner, group=group)
        case str(), "bash" | "posix" | "sh":
            path = Path(root, f"etc/profile.d/{etc}.sh")
            lines = ["#!/usr/bin/env sh", "", *always_iterable(bash)]
            text = normalize_str("\n".join(always_iterable(lines)))
            write_text(
                path, text, overwrite=True, perms=perms, owner=owner, group=group
            )
        case str(), _:
            msg = f"Invalid shell for 'etc': {repr_str(shell)}"
            raise ValueError(msg)
        case never:
            assert_never(never)


##


def setup_ssh_config(
    *,
    home: PathLike = HOME,
    ssh: str | None = None,
    sudo: bool = False,
    retry: Retry | None = None,
) -> None:
    """Set up the SSH config."""
    _LOGGER.info("Setting up SSH config...")
    config = Path(home, ".ssh/config")
    config_d = Path(home, ".ssh/config.d")
    text = normalize_str(f"Include {config_d}/*.conf")
    if ssh is None:
        tee(config, text, sudo=sudo)
        mkdir(config_d, sudo=sudo)
    else:
        user, hostname = split_ssh(ssh)
        cmds: list[list[str]] = [mkdir_cmd(config, parent=True), mkdir_cmd(config_d)]
        utilities.subprocess.ssh(
            user,
            hostname,
            *BASH_LS,
            input="\n".join(map(join, cmds)),
            retry=retry,
            logger=_LOGGER,
        )
        utilities.subprocess.ssh(
            user, hostname, *tee_cmd(config), input=text, retry=retry, logger=_LOGGER
        )


##


def setup_sshd_config(
    *,
    permit_root_login: bool = False,
    root: PathLike = FILE_SYSTEM_ROOT,
    ssh: str | None = None,
    sudo: bool = False,
    retry: Retry | None = None,
) -> None:
    _LOGGER.info("Setting up SSHD config...")
    path = Path(root, "etc/ssh/sshd_config.d/default.conf")
    text = sshd_config(permit_root_login=permit_root_login)
    if ssh is None:
        tee(path, text, sudo=sudo)
    else:
        user, hostname = split_ssh(ssh)
        path = Path("/etc/ssh/sshd_config.d/default.conf")
        utilities.subprocess.ssh(
            user,
            hostname,
            *maybe_sudo_cmd(*tee_cmd(path), sudo=sudo),
            input=text,
            retry=retry,
            logger=_LOGGER,
        )


def sshd_config(*, permit_root_login: bool = False) -> str:
    yes_no = "yes" if permit_root_login else "no"
    return normalize_multi_line_str(f"""
        PasswordAuthentication no
        PermitRootLogin {yes_no}
        PubkeyAcceptedAlgorithms ssh-ed25519
        PubkeyAuthentication yes
    """)


__all__ = [
    "setup_authorized_keys",
    "setup_shell_config",
    "setup_ssh_config",
    "setup_sshd_config",
    "sshd_config",
]
