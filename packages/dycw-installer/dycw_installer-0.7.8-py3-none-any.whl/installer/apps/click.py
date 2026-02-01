from __future__ import annotations

from click import option
from utilities.click import Path, SecretStr, Str

from installer.apps.constants import (
    GITHUB_TOKEN,
    PATH_BINARIES,
    PERMISSIONS_BINARY,
    PERMISSIONS_CONFIG,
)

force_option = option(
    "--force",
    is_flag=True,
    default=False,
    help="Force the installation even if the command already exists",
)
group_option = option("--group", type=Str(), default=None, help="Binary group")
owner_option = option("--owner", type=Str(), default=None, help="Binary owner")
path_binaries_option = option(
    "--path-binaries",
    type=Path(exist="dir if exists"),
    default=PATH_BINARIES,
    help="Path to the binaries",
)
perms_option, perms_binary_option = [
    option(p, type=Str(), default=PERMISSIONS_BINARY, help="Binary permissions")
    for p in ["--perms", "--perms-binary"]
]
perms_config_option = option(
    "--perms-config", type=Str(), default=PERMISSIONS_CONFIG, help="Config permissions"
)
token_option = option(
    "--token", type=SecretStr(), default=GITHUB_TOKEN, help="GitHub token"
)


__all__ = [
    "force_option",
    "group_option",
    "owner_option",
    "path_binaries_option",
    "perms_binary_option",
    "perms_config_option",
    "perms_option",
    "token_option",
]
