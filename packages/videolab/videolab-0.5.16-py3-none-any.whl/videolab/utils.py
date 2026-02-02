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

"""Utility functions for file path manipulation and common operations."""

import argparse
import functools
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import av
import av.error

logger = logging.getLogger(__name__)


def handle_video_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Handle common video processing exceptions decorator."""

    @functools.wraps(func)
    def wrapper(args: argparse.Namespace) -> None:
        try:
            func(args)
        except (av.error.FFmpegError, ValueError) as e:
            logger.error(str(e))
            if args.verbose:
                logger.exception("Detailed error information:")
        except FileNotFoundError:
            logger.error("Input file '%s' not found.", args.input_file)

    return wrapper


def generate_output_filename(
    input_file: str,
    output_file: str | None,
    suffix: str,
) -> Path:
    """Generate an output filename based on the input file and a suffix.

    If an explicit output file is provided, it is returned as a Path object.
    """
    if output_file is not None:
        return Path(output_file)

    input_path = Path(input_file)
    return input_path.with_stem(f"{input_path.stem}_{suffix}")
