# Copyright 2020-2022 Louis Paternault
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests of the add_executable(), add_prefix_executables(), add_pattern_executables() methods."""

import importlib
from unittest.mock import patch

import argdispatch

from . import TestArgparse, pythonpath


class _MockEntrypointFunction:
    """Fake function entry to be returned as an entry point."""

    # pylint: disable=too-few-public-methods

    def __init__(self, name, function):
        self.name = name
        self.module, self.function = function

    def load(self):
        """Import the module and return its function."""
        return getattr(
            importlib.import_module(self.module),
            self.function,
        )


class _MockEntrypointModule:
    """Fake module entry to be returned as an entry point."""

    # pylint: disable=too-few-public-methods

    def __init__(self, name, module):
        self.name = name
        self.module = module

    def load(self):
        """Import and return the module."""
        return importlib.import_module(self.module)


_ENTRY_POINTS = {
    "testfunction": [
        _MockEntrypointFunction("func", ("tagada", "some_function")),
        _MockEntrypointFunction("fail", ("???doesnotexist", "some_function")),
    ],
    "testmodules": [
        _MockEntrypointModule("mod", "tsoin"),
        _MockEntrypointModule("fail", "???doesnotexist"),
    ],
    "testnotpackages": [
        _MockEntrypointModule("mod", "tsoin"),
        _MockEntrypointModule("notapackage", "notapackage"),
    ],
    "testmissingmain": [
        _MockEntrypointModule("mod", "tsoin"),
        _MockEntrypointModule("missingmain", "missingmain"),
    ],
}


def _mock_iter_entry_points(group):
    yield from _ENTRY_POINTS[group]


class TestParse(TestArgparse):
    """Test that subparsers definition, and method `parse_args`."""

    @patch("importlib.metadata.entry_points", new=_mock_iter_entry_points)
    @pythonpath("pythonpath4")
    def test_entry_points(self):
        """Test the entry_points functions."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()

        with self.subTest():
            sub.add_entrypoints_functions("testfunction", onerror=argdispatch.IGNORE)
            sub.add_entrypoints_modules("testmodules", onerror=argdispatch.IGNORE)

        with self.subTest():
            with self.assertStdoutMatches(r"^Running some function\(arg\)$"):
                with self.assertExit(3):
                    parser.parse_args("func arg".split())

        with self.subTest():
            with self.assertStdoutMatches(r"Running python module tsoin.__main__ arg"):
                with self.assertExit(0):
                    parser.parse_args("mod arg".split())


class TestErrors(TestArgparse):
    """Test various errors."""

    @patch("importlib.metadata.entry_points", new=_mock_iter_entry_points)
    @pythonpath("pythonpath4")
    def test_onerror(self):
        """Test the entry_points functions."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()

        with self.subTest():
            with self.assertRaises(Exception):
                sub.add_entrypoints_functions("testfunction", onerror=argdispatch.RAISE)

        with self.subTest():
            with self.assertRaises(Exception):
                sub.add_entrypoints_modules("testmodules", onerror=argdispatch.RAISE)

    @patch("importlib.metadata.entry_points", new=_mock_iter_entry_points)
    @pythonpath("pythonpath4")
    def test_forcemain1(self):
        """Test the entry_points functions."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()

        with self.subTest():
            with self.assertRaises(Exception):
                sub.add_entrypoints_modules(
                    "testnotpackages", onerror=argdispatch.RAISE, forcemain=True
                )

        with self.subTest():
            with self.assertRaises(Exception):
                sub.add_entrypoints_modules(
                    "testmissingmain", onerror=argdispatch.RAISE, forcemain=True
                )

    @patch("importlib.metadata.entry_points", new=_mock_iter_entry_points)
    @pythonpath("pythonpath4")
    def test_forcemain2(self):
        """Test the entry_points functions."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()

        with self.subTest():
            sub.add_entrypoints_modules(
                "testnotpackages", onerror=argdispatch.RAISE, forcemain=False
            )
            sub.add_entrypoints_modules(
                "testmissingmain", onerror=argdispatch.RAISE, forcemain=False
            )

    @patch("importlib.metadata.entry_points", new=_mock_iter_entry_points)
    @pythonpath("pythonpath4")
    def test_forcemain3(self):
        """Test the entry_points functions."""
        parser = argdispatch.ArgumentParser(prog="test")
        sub = parser.add_subparsers()

        with self.subTest():
            sub.add_entrypoints_modules(
                "testnotpackages", onerror=argdispatch.IGNORE, forcemain=True
            )
            sub.add_entrypoints_modules(
                "testmissingmain", onerror=argdispatch.IGNORE, forcemain=True
            )

        with self.subTest():
            with self.assertStdoutMatches(
                r"notapackage",
                count=0,
            ):
                with self.assertExit(0):
                    parser.parse_args("--help".split())
