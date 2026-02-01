from __future__ import annotations

from typing import TYPE_CHECKING

import utilities.click
from click import argument, option
from utilities.click import Str
from utilities.core import is_pytest, set_up_logging

from installer.click import retry_option
from installer.clone.constants import GIT_CLONE_HOST
from installer.clone.lib import git_clone

if TYPE_CHECKING:
    from utilities.types import PathLike, Retry


@argument("key", type=utilities.click.Path(exist="existing file"))
@argument("owner", type=Str())
@argument("repo", type=Str())
@option("--host", type=Str(), default=GIT_CLONE_HOST, help="Repository host")
@retry_option
@option("--port", type=int, default=None, help="Repository port")
@option(
    "--dest",
    type=utilities.click.Path(exist="dir if exists"),
    default=None,
    help="Path to clone to",
)
@option("--branch", type=Str(), default=None, help="Branch to check out")
def git_clone_sub_cmd(
    *,
    key: PathLike,
    owner: str,
    repo: str,
    host: str,
    retry: Retry | None,
    port: int | None,
    dest: PathLike,
    branch: str | None,
) -> None:
    if is_pytest():
        return
    set_up_logging(__name__, root=True)
    git_clone(
        key, owner, repo, host=host, retry=retry, port=port, dest=dest, branch=branch
    )


__all__ = ["git_clone_sub_cmd"]
