# Copyright 2016-2022 Louis Paternault
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

import argdispatch

from . import SuppressStandard, TestArgparse, binpath, testdatapath


class TestParse(TestArgparse):
    """Test that subparsers definition, and method `parse_args`."""

    @binpath("binpath1", "binpath2")
    def test_executable(self):
        """Test the `add_executable` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_executable("bin11")
        sub.add_executable("bin12", "foo")
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin11$"):
                with self.assertExit(0):
                    parser.parse_args("bin11".split())
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin11 --some arguments$"):
                with self.assertExit(0):
                    parser.parse_args("bin11 --some arguments".split())
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin12 bar baz$"):
                with self.assertExit(0):
                    parser.parse_args("foo bar baz".split())

    @binpath("binpath1", "binpath2")
    def test_pattern_executables(self):
        """Test the `add_pattern_executables` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_pattern_executables(".*2$")
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin12$"):
                with self.assertExit(0):
                    parser.parse_args("bin12".split())
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin22$"):
                with self.assertExit(0):
                    parser.parse_args("bin22".split())
        with self.subTest():
            with SuppressStandard():
                with self.assertExit(2):
                    parser.parse_args("bin11".split())

    @binpath("binpath1", "binpath2")
    def test_pattern_named_group(self):
        """Test the `add_pattern_executables` method, with a named group."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_pattern_executables("^(?P<command>.*)2$")
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin12$"):
                with self.assertExit(0):
                    parser.parse_args("bin1".split())
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin22$"):
                with self.assertExit(0):
                    parser.parse_args("bin2".split())
        with self.subTest():
            with SuppressStandard():
                with self.assertExit(2):
                    parser.parse_args("bin12".split())

    @binpath("binpath1", "binpath2")
    def test_prefix_executables(self):
        """Test the `add_prefix_executables` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_prefix_executables("bin1")
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin11$"):
                with self.assertExit(0):
                    parser.parse_args("1".split())
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin12$"):
                with self.assertExit(0):
                    parser.parse_args("2".split())
        with self.subTest():
            with SuppressStandard():
                with self.assertExit(2):
                    parser.parse_args("bin11".split())


class TestErrors(TestArgparse):
    """Test various errors."""

    @binpath("doesnotexist")
    def test_non_existent_path(self):
        """Test the `add_prefix_executables` method, with a non-existent path."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()

        # Nothing special to test here, excepted that this should not raise any Exception.
        sub.add_prefix_executables("bin")

    @binpath("binpath1", "binpath1")
    def test_double_path(self):
        """Test the `add_prefix_executables` method, with a path appearing twice."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_prefix_executables("bin")

        with self.assertStdoutMatches(r"^\s*11\s*", count=1):
            with self.assertExit(0):
                parser.parse_args("--help".split())


class TestPath(TestArgparse):
    """Test the ``path`` argument."""

    def test_add_executable(self):
        """Test with executables that do not exist."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        with self.subTest():
            # Nothing should fail, although executable `bin21` does not exists in path
            sub.add_executable("bin21")
        with self.subTest():
            with self.assertRaises(FileNotFoundError):
                parser.parse_args("bin21".split())

    def test_add_prefix_executables(self):
        """Test various errors with the ``add_prefix_executables`` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_prefix_executables("bin", path=[testdatapath("binpath1")])
        with self.subTest():
            with self.assertStdoutMatches(r"^Running .*bin11$"):
                with self.assertExit(0):
                    parser.parse_args("11".split())
        with self.subTest():
            with SuppressStandard():
                with self.assertExit(2):
                    parser.parse_args("21".split())


class TestHelp(TestArgparse):
    """Test that subcommand help works."""

    def test_executable(self):
        """Test of help for ``add_executable`` method."""
        parser = self._ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_executable("foo1")
        sub.add_executable("foo2", help="This is the help of foo2.")

        with self.subTest():
            with self.assertStdoutMatches(r"foo1"):
                with self.assertExit(0):
                    parser.parse_args("--help".split())

        with self.subTest():
            with self.assertStdoutMatches(r"foo2.*This is the help of foo2."):
                with self.assertExit(0):
                    parser.parse_args("--help".split())
