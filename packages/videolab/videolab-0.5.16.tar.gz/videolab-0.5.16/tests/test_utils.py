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

import argparse
from unittest.mock import MagicMock

import av.error
import pytest

from videolab.utils import handle_video_errors


def test_handle_video_errors_ffmpeg_error(caplog: pytest.LogCaptureFixture) -> None:
    @handle_video_errors
    def func(args: argparse.Namespace) -> None:
        raise av.error.FFmpegError(1, "FFmpeg error")

    args = argparse.Namespace(input_file="test.mp4", verbose=False)
    func(args)
    assert "FFmpeg error" in caplog.text


def test_handle_video_errors_file_not_found_error(caplog: pytest.LogCaptureFixture) -> None:
    @handle_video_errors
    def func(args: argparse.Namespace) -> None:
        raise FileNotFoundError("File not found")

    args = argparse.Namespace(input_file="nonexistent.mp4", verbose=False)
    func(args)
    assert "Input file 'nonexistent.mp4' not found." in caplog.text


def test_handle_video_errors_value_error(caplog: pytest.LogCaptureFixture) -> None:
    @handle_video_errors
    def func(args: argparse.Namespace) -> None:
        raise ValueError("Value error")

    args = argparse.Namespace(input_file="test.mp4", verbose=False)
    func(args)
    assert "Value error" in caplog.text


def test_handle_video_errors_value_error_verbose(caplog: pytest.LogCaptureFixture) -> None:
    @handle_video_errors
    def func(args: argparse.Namespace) -> None:
        raise ValueError("Value error")

    args = argparse.Namespace(input_file="test.mp4", verbose=True)
    func(args)
    assert "Value error" in caplog.text
    assert "Detailed error information" in caplog.text
