from __future__ import annotations

from typing import TYPE_CHECKING

from click import argument, option
from utilities.click import Str
from utilities.core import is_pytest, set_up_logging

from installer.click import retry_option, ssh_option, sudo_option
from installer.configs.click import home_option, permit_root_login_option, root_option
from installer.configs.lib import (
    setup_authorized_keys,
    setup_ssh_config,
    setup_sshd_config,
)

if TYPE_CHECKING:
    from utilities.types import PathLike, Retry


@argument("keys", type=Str(), nargs=-1)
@home_option
@ssh_option
@sudo_option
@option("--batch-mode", is_flag=True, default=None, help="SSH batch mode")
@retry_option
def setup_authorized_keys_sub_cmd(
    *,
    keys: tuple[str, ...],
    home: PathLike,
    ssh: str | None,
    sudo: bool,
    batch_mode: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_authorized_keys(
        list(keys), home=home, ssh=ssh, sudo=sudo, batch_mode=batch_mode, retry=retry
    )


@home_option
@ssh_option
@sudo_option
@retry_option
def setup_ssh_config_sub_cmd(
    *, home: PathLike, ssh: str | None, sudo: bool, retry: Retry | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_ssh_config(home=home, ssh=ssh, sudo=sudo, retry=retry)


@permit_root_login_option
@root_option
@ssh_option
@sudo_option
@retry_option
def setup_sshd_sub_cmd(
    *,
    permit_root_login: bool,
    root: PathLike,
    ssh: str | None,
    sudo: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_sshd_config(
        permit_root_login=permit_root_login, root=root, ssh=ssh, sudo=sudo, retry=retry
    )


__all__ = [
    "setup_authorized_keys_sub_cmd",
    "setup_ssh_config_sub_cmd",
    "setup_sshd_sub_cmd",
]
