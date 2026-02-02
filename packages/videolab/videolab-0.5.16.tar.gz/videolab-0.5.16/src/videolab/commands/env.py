"""Module for displaying environment information."""

# Copyright (c) 2025,2026 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import platform
import sys
from typing import TYPE_CHECKING, Any

from videolab import __version__

if TYPE_CHECKING:
    import argparse


def env_command(_args: argparse.Namespace) -> None:
    """Show environment information."""
    print(f"videolab: {__version__}")  # noqa: T201
    print(f"python: {sys.version.splitlines()[0]}")  # noqa: T201
    print(f"platform: {platform.platform()}")  # noqa: T201


def register_subcommand(subparsers: argparse._SubParsersAction[Any]) -> None:
    """Register the 'env' subcommand."""
    env_parser = subparsers.add_parser("env", help="show environment information")
    env_parser.set_defaults(func=env_command)
