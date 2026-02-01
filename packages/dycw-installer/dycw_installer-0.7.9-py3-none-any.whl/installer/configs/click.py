from __future__ import annotations

from click import Choice, option
from utilities.click import Path
from utilities.constants import HOME
from utilities.shellingham import SHELL, Shell
from utilities.typing import get_literal_elements

from installer.configs.constants import FILE_SYSTEM_ROOT

etc_option = option(
    "--etc",
    is_flag=True,
    default=False,
    help="Set up in '/etc/profile.d/*.sh' instead of '~/.{bash,zsh}rc'",
)
home_option = option(
    "--home",
    type=Path(exist="dir if exists"),
    default=None,
    help=f"Path to the home directory. Defaults to {str(HOME)!r} for the current system",
)
permit_root_login_option = option(
    "--permit-root-login", is_flag=True, default=False, help="Permit root login"
)
shell_option = option(
    "--shell",
    type=Choice(get_literal_elements(Shell), case_sensitive=False),
    default=None,
    help=f"System shell. Defaults to {SHELL!r} for the current system",
)
root_option = option(
    "--root",
    type=Path(exist="dir if exists"),
    default=None,
    help=f"File system root. Defaults to {str(FILE_SYSTEM_ROOT)!r} for the current system",
)


__all__ = ["etc_option", "home_option", "permit_root_login_option", "root_option"]
