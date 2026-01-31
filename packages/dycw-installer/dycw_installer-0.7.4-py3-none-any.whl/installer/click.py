from __future__ import annotations

from click import Tuple, option
from utilities.click import Str

ssh_option = option("--ssh", type=Str(), default=None, help="SSH user & hostname")
sudo_option = option("--sudo", is_flag=True, default=False, help="Run as 'sudo'")
retry_option = option("--retry", type=Tuple([int, int]), default=None, help="SSH retry")


__all__ = ["retry_option", "ssh_option", "sudo_option"]
