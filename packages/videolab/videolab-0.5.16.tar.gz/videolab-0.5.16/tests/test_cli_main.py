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

import sys
import subprocess
from pathlib import Path


def test_cli_main_invocation() -> None:
    # Run the module as a script to cover the if __name__ == "__main__": block
    # We use -c to import and check or just run it with -h to avoid any logic
    result = subprocess.run(
        [sys.executable, "-m", "videolab.cli", "-h"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "usage: videolab" in result.stdout
