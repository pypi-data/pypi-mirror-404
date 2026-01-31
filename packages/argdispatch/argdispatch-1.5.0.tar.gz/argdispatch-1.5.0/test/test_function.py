# Copyright 2016-2021 Louis Paternault
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

"""Tests of the add_function() method."""

import sys

import argdispatch

from . import TestArgparse


def function_foo(args):
    """This is the docstring of function foo."""
    # pylint: disable=consider-using-f-string
    print("Running function_foo({})".format(", ".join(args)))
    sys.exit(1)


def function_bar(args):
    """This is the docstring of function bar."""
    # pylint: disable=consider-using-f-string
    print("Running function_bar({})".format(", ".join(args)))
    return 1


def function_none(args):
    """This is the docstring of function none."""
    # pylint: disable=consider-using-f-string
    print("Running function_none({})".format(", ".join(args)))


def function_nodocstring(args):
    # pylint: disable=missing-docstring, unused-argument
    pass


def function_emptydocstring(args):  # pylint: disable=unused-argument, empty-docstring
    # pylint: disable=trailing-whitespace
    """ """


class TestParse(TestArgparse):
    """Test that subparsers definition, and method `parse_args`."""

    def test_function(self):
        """Test the `add_function` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_function(function_foo)
        sub.add_function(function_bar, "bar")
        sub.add_function(function_foo, "foo")
        with self.subTest():
            with self.assertStdoutMatches(r"^Running function_foo\(arg\)$"):
                with self.assertExit(1):
                    parser.parse_args("foo arg".split())
        with self.subTest():
            with self.assertStdoutMatches(r"^Running function_bar\(arg\)$"):
                with self.assertExit(1):
                    parser.parse_args("bar arg".split())
        with self.subTest():
            with self.assertStdoutMatches(r"^Running function_foo\(arg\)$"):
                with self.assertExit(1):
                    parser.parse_args("function_foo arg".split())

    def test_function_return_none(self):
        """Test the `add_function` method, with a function returning ``None``."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_function(function_none, "none")
        with self.assertStdoutMatches(r"^Running function_none\(--some, arguments\)$"):
            with self.assertExit(None):
                parser.parse_args("none --some arguments".split())


class TestHelp(TestArgparse):
    """Test that subcommand help works."""

    def test_function(self):
        """Test of the ``add_function`` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_function(function_foo, "foo1")
        sub.add_function(function_foo, "foo2", help="This is an hard-coded help")

        with self.subTest():
            with self.assertStdoutMatches(
                """foo1.*This is the docstring of function foo."""
            ):
                with self.assertExit(0):
                    parser.parse_args("--help".split())

        with self.subTest():
            with self.assertStdoutMatches("""foo2.*This is an hard-coded help"""):
                with self.assertExit(0):
                    parser.parse_args("--help".split())

    def test_empty_help(self):
        """Test that automatic help works with empty or non-existent docstrings."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_function(function_nodocstring, "none")
        sub.add_function(function_emptydocstring, "empty")

        with self.subTest():
            with self.assertStdoutMatches(r"^\s*none\s*$"):
                with self.assertExit(0):
                    parser.parse_args("--help".split())

        with self.subTest():
            with self.assertStdoutMatches(r"^\s*empty\s*$"):
                with self.assertExit(0):
                    parser.parse_args("--help".split())
