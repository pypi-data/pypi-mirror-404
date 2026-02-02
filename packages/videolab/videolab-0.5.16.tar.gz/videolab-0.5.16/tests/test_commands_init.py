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

from unittest.mock import MagicMock, patch

from videolab.commands import discover_and_register


def test_discover_and_register_skips_modules_without_register() -> None:
    # Mock pkgutil.iter_modules
    with patch("pkgutil.iter_modules") as mock_iter:
        mock_iter.return_value = [
            (None, "module_with_register", False),
            (None, "module_without_register", False),
        ]

        # Mock importlib.import_module
        with patch("importlib.import_module") as mock_import:
            mock_module_with = MagicMock()
            mock_module_without = MagicMock()
            del mock_module_without.register_subcommand

            mock_import.side_effect = [mock_module_with, mock_module_without]

            mock_subparsers = MagicMock()
            discover_and_register(mock_subparsers)

            # verify module_with was called
            mock_module_with.register_subcommand.assert_called_once_with(mock_subparsers)
            # verify module_without was imported but not called (it doesn't have it)
            # nothing to assert other than it didn't crash
