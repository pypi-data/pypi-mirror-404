from __future__ import annotations

from click import group, version_option
from utilities.click import CONTEXT_SETTINGS

from installer import __version__
from installer.apps.cli import (
    age_sub_cmd,
    apt_package_sub_cmd,
    bat_sub_cmd,
    bottom_sub_cmd,
    curl_sub_cmd,
    delta_sub_cmd,
    direnv_sub_cmd,
    docker_sub_cmd,
    dust_sub_cmd,
    eza_sub_cmd,
    fd_sub_cmd,
    fzf_sub_cmd,
    git_sub_cmd,
    jq_sub_cmd,
    just_sub_cmd,
    neovim_sub_cmd,
    pve_fake_subscription_sub_cmd,
    restic_sub_cmd,
    ripgrep_sub_cmd,
    rsync_sub_cmd,
    ruff_sub_cmd,
    sd_sub_cmd,
    shellcheck_sub_cmd,
    shfmt_sub_cmd,
    sops_sub_cmd,
    starship_sub_cmd,
    taplo_sub_cmd,
    uv_sub_cmd,
    watchexec_sub_cmd,
    yq_sub_cmd,
    zoxide_sub_cmd,
)
from installer.clone.cli import git_clone_sub_cmd
from installer.configs.cli import (
    setup_authorized_keys_sub_cmd,
    setup_ssh_config_sub_cmd,
    setup_sshd_sub_cmd,
)


@group(**CONTEXT_SETTINGS)
@version_option(version=__version__)
def cli() -> None: ...


_ = cli.command(name="apt-package", help="Set up an 'apt' package", **CONTEXT_SETTINGS)(
    apt_package_sub_cmd
)
_ = cli.command(name="age", help="Set up 'age'", **CONTEXT_SETTINGS)(age_sub_cmd)
_ = cli.command(name="bat", help="Set up 'bat'", **CONTEXT_SETTINGS)(bat_sub_cmd)
_ = cli.command(name="btm", help="Set up 'btm'", **CONTEXT_SETTINGS)(bottom_sub_cmd)
_ = cli.command(name="curl", help="Set up 'curl'", **CONTEXT_SETTINGS)(curl_sub_cmd)
_ = cli.command(name="delta", help="Set up 'delta'", **CONTEXT_SETTINGS)(delta_sub_cmd)
_ = cli.command(name="direnv", help="Set up 'direnv'", **CONTEXT_SETTINGS)(
    direnv_sub_cmd
)
_ = cli.command(name="docker", help="Set up 'docker'", **CONTEXT_SETTINGS)(
    docker_sub_cmd
)
_ = cli.command(name="dust", help="Set up 'dust'", **CONTEXT_SETTINGS)(dust_sub_cmd)
_ = cli.command(name="eza", help="Set up 'eza'", **CONTEXT_SETTINGS)(eza_sub_cmd)
_ = cli.command(name="fd", help="Set up 'fd'", **CONTEXT_SETTINGS)(fd_sub_cmd)
_ = cli.command(name="fzf", help="Set up 'fzf'", **CONTEXT_SETTINGS)(fzf_sub_cmd)
_ = cli.command(name="jq", help="Set up 'jq'", **CONTEXT_SETTINGS)(jq_sub_cmd)
_ = cli.command(name="git", help="Set up 'git'", **CONTEXT_SETTINGS)(git_sub_cmd)
_ = cli.command(name="just", help="Set up 'just'", **CONTEXT_SETTINGS)(just_sub_cmd)
_ = cli.command(name="neovim", help="Set up 'neovim'", **CONTEXT_SETTINGS)(
    neovim_sub_cmd
)
_ = cli.command(
    name="pve-fake-subscription",
    help="Set up 'pve-fake-subscription'",
    **CONTEXT_SETTINGS,
)(pve_fake_subscription_sub_cmd)
_ = cli.command(name="restic", help="Set up 'restic'", **CONTEXT_SETTINGS)(
    restic_sub_cmd
)
_ = cli.command(name="ripgrep", help="Set up 'ripgrep'", **CONTEXT_SETTINGS)(
    ripgrep_sub_cmd
)
_ = cli.command(name="ruff", help="Set up 'ruff'", **CONTEXT_SETTINGS)(ruff_sub_cmd)
_ = cli.command(name="rsync", help="Set up 'rsync'", **CONTEXT_SETTINGS)(rsync_sub_cmd)
_ = cli.command(name="sd", help="Set up 'sd'", **CONTEXT_SETTINGS)(sd_sub_cmd)
_ = cli.command(name="shellcheck", help="Set up 'shellcheck'", **CONTEXT_SETTINGS)(
    shellcheck_sub_cmd
)
_ = cli.command(name="shfmt", help="Set up 'shfmt'", **CONTEXT_SETTINGS)(shfmt_sub_cmd)
_ = cli.command(name="sops", help="Set up 'sops'", **CONTEXT_SETTINGS)(sops_sub_cmd)
_ = cli.command(name="starship", help="Set up 'starship'", **CONTEXT_SETTINGS)(
    starship_sub_cmd
)
_ = cli.command(name="taplo", help="Set up 'taplo'", **CONTEXT_SETTINGS)(taplo_sub_cmd)
_ = cli.command(name="uv", help="Set up 'uv'", **CONTEXT_SETTINGS)(uv_sub_cmd)
_ = cli.command(name="watchexec", help="Set up 'watchexec'", **CONTEXT_SETTINGS)(
    watchexec_sub_cmd
)
_ = cli.command(name="yq", help="Set up 'yq'", **CONTEXT_SETTINGS)(yq_sub_cmd)
_ = cli.command(name="zoxide", help="Set up 'zoxide'", **CONTEXT_SETTINGS)(
    zoxide_sub_cmd
)


_ = cli.command(
    name="git-clone", help="Clone a repo with a deploy key.", **CONTEXT_SETTINGS
)(git_clone_sub_cmd)


_ = cli.command(
    name="setup-authorized-keys",
    help="Set up the SSH authorized keys",
    **CONTEXT_SETTINGS,
)(setup_authorized_keys_sub_cmd)
_ = cli.command(
    name="setup-ssh-config", help="Set up the SSH config", **CONTEXT_SETTINGS
)(setup_ssh_config_sub_cmd)
_ = cli.command(
    name="setup-sshd-config", help="Set up the SSHD config", **CONTEXT_SETTINGS
)(setup_sshd_sub_cmd)


if __name__ == "__main__":
    cli()
