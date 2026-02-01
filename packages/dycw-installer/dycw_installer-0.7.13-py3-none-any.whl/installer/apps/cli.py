from __future__ import annotations

from typing import TYPE_CHECKING

import utilities.click
from click import argument, option
from utilities.click import Str
from utilities.core import PermissionsLike, is_pytest, set_up_logging

from installer.apps.click import (
    force_option,
    group_option,
    owner_option,
    path_binaries_option,
    perms_binary_option,
    perms_config_option,
    perms_option,
    token_option,
)
from installer.apps.lib import (
    set_up_age,
    set_up_apt_package,
    set_up_bat,
    set_up_bottom,
    set_up_curl,
    set_up_delta,
    set_up_direnv,
    set_up_docker,
    set_up_dust,
    set_up_eza,
    set_up_fd,
    set_up_fzf,
    set_up_git,
    set_up_jq,
    set_up_just,
    set_up_neovim,
    set_up_pve_fake_subscription,
    set_up_restic,
    set_up_ripgrep,
    set_up_rsync,
    set_up_sops,
    set_up_starship,
    set_up_uv,
    set_up_zoxide,
    setup_ruff,
    setup_sd,
    setup_shellcheck,
    setup_shfmt,
    setup_taplo,
    setup_watchexec,
    setup_yq,
)
from installer.click import retry_option, ssh_option, sudo_option
from installer.configs.click import etc_option, home_option, root_option, shell_option

if TYPE_CHECKING:
    from utilities.shellingham import Shell
    from utilities.types import PathLike, Retry, SecretLike


@argument("package", type=str)
@sudo_option
@ssh_option
@force_option
@retry_option
def apt_package_sub_cmd(
    *, package: str, sudo: bool, ssh: str | None, force: bool, retry: Retry | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_apt_package(package, sudo=sudo, ssh=ssh, force=force, retry=retry)


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def age_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_age(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def bat_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_bat(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def bottom_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_bottom(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@sudo_option
@ssh_option
@force_option
@retry_option
def curl_sub_cmd(
    *, sudo: bool, ssh: str | None, force: bool, retry: Retry | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_curl(sudo=sudo, ssh=ssh, force=force, retry=retry)


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def delta_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_delta(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_binary_option
@owner_option
@group_option
@etc_option
@shell_option
@home_option
@perms_config_option
@root_option
@ssh_option
@force_option
@retry_option
def direnv_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms_binary: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    shell: Shell | None,
    etc: bool,
    home: PathLike,
    perms_config: PermissionsLike,
    root: PathLike | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_direnv(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms_binary=perms_binary,
        owner=owner,
        group=group,
        etc=etc,
        shell=shell,
        home=home,
        perms_config=perms_config,
        root=root,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@sudo_option
@ssh_option
@option("--user", type=Str(), default=None, help="User to add to the 'docker' group")
@force_option
@retry_option
def docker_sub_cmd(
    *, sudo: bool, ssh: str | None, user: str | None, force: bool, retry: Retry | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_docker(sudo=sudo, ssh=ssh, user=user, force=force, retry=retry)


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def dust_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_dust(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def eza_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_eza(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def fd_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_fd(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_binary_option
@owner_option
@group_option
@etc_option
@shell_option
@home_option
@perms_config_option
@root_option
@ssh_option
@force_option
@retry_option
def fzf_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms_binary: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    etc: bool,
    shell: Shell | None,
    home: PathLike,
    perms_config: PermissionsLike,
    root: PathLike | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_fzf(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms_binary=perms_binary,
        owner=owner,
        group=group,
        etc=etc,
        shell=shell,
        home=home,
        perms_config=perms_config,
        root=root,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@sudo_option
@ssh_option
@force_option
@retry_option
def git_sub_cmd(
    *, sudo: bool, ssh: str | None, force: bool, retry: Retry | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_git(sudo=sudo, ssh=ssh, force=force, retry=retry)


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def jq_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_jq(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def just_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_just(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def neovim_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_neovim(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@ssh_option
@force_option
@retry_option
def pve_fake_subscription_sub_cmd(
    *, token: SecretLike | None, ssh: str | None, force: bool, retry: Retry | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_pve_fake_subscription(token=token, ssh=ssh, force=force, retry=retry)


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def restic_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_restic(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def ripgrep_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_ripgrep(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@sudo_option
@ssh_option
@force_option
@retry_option
def rsync_sub_cmd(
    *, sudo: bool, ssh: str | None, force: bool, retry: Retry | None
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_rsync(sudo=sudo, ssh=ssh, force=force, retry=retry)


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
def ruff_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_ruff(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
def sd_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_sd(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
def shellcheck_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_shellcheck(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
def shfmt_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_shfmt(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@ssh_option
@force_option
@retry_option
def sops_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_sops(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_binary_option
@owner_option
@group_option
@etc_option
@shell_option
@home_option
@perms_config_option
@root_option
@option(
    "--starship-toml", type=utilities.click.Path(exist="file if exists"), default=None
)
@ssh_option
@force_option
@retry_option
def starship_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms_binary: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    etc: bool,
    shell: Shell | None,
    home: PathLike | None,
    perms_config: PermissionsLike,
    root: PathLike | None,
    starship_toml: PathLike | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_starship(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms_binary=perms_binary,
        owner=owner,
        group=group,
        etc=etc,
        shell=shell,
        home=home,
        perms_config=perms_config,
        root=root,
        starship_toml=starship_toml,
        ssh=ssh,
        force=force,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
def taplo_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_taplo(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


@ssh_option
@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
@retry_option
def uv_sub_cmd(
    *,
    ssh: str | None,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_uv(
        ssh=ssh,
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        retry=retry,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
def watchexec_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_watchexec(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_option
@owner_option
@group_option
def yq_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    setup_yq(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


@token_option
@path_binaries_option
@sudo_option
@perms_binary_option
@owner_option
@group_option
@etc_option
@shell_option
@home_option
@perms_config_option
@root_option
@ssh_option
@force_option
@retry_option
def zoxide_sub_cmd(
    *,
    token: SecretLike | None,
    path_binaries: PathLike,
    sudo: bool,
    perms_binary: PermissionsLike,
    owner: str | int | None,
    group: str | int | None,
    etc: bool,
    shell: Shell | None,
    home: PathLike,
    perms_config: PermissionsLike,
    root: PathLike | None,
    ssh: str | None,
    force: bool,
    retry: Retry | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    set_up_zoxide(
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms_binary=perms_binary,
        owner=owner,
        group=group,
        etc=etc,
        shell=shell,
        home=home,
        perms_config=perms_config,
        root=root,
        ssh=ssh,
        force=force,
        retry=retry,
    )


__all__ = [
    "age_sub_cmd",
    "apt_package_sub_cmd",
    "bat_sub_cmd",
    "bottom_sub_cmd",
    "curl_sub_cmd",
    "delta_sub_cmd",
    "direnv_sub_cmd",
    "dust_sub_cmd",
    "eza_sub_cmd",
    "fd_sub_cmd",
    "fzf_sub_cmd",
    "git_sub_cmd",
    "jq_sub_cmd",
    "just_sub_cmd",
    "neovim_sub_cmd",
    "pve_fake_subscription_sub_cmd",
    "restic_sub_cmd",
    "ripgrep_sub_cmd",
    "rsync_sub_cmd",
    "ruff_sub_cmd",
    "sd_sub_cmd",
    "shellcheck_sub_cmd",
    "shfmt_sub_cmd",
    "sops_sub_cmd",
    "starship_sub_cmd",
    "taplo_sub_cmd",
    "uv_sub_cmd",
    "watchexec_sub_cmd",
    "yq_sub_cmd",
    "zoxide_sub_cmd",
]
