# Copyright 2016-2025 Louis Paternault
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

"""Generic tests."""

import argparse
import sys

import argdispatch

from . import SuppressStandard, TestArgparse


class TestParse(TestArgparse):
    """Test that subparsers definition, and method `parse_args`, works."""

    def test_add_parser(self):
        """Test the legacy `add_parser` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        parser_foo = sub.add_parser("foo")
        parser_foo.set_defaults(sub="foo")
        parser_bar = sub.add_parser("bar")
        parser_bar.set_defaults(sub="bar")
        with self.subTest():
            self.assertEqual(parser.parse_args("foo".split()).sub, "foo")
        with self.subTest():
            self.assertEqual(parser.parse_args("bar".split()).sub, "bar")
        with self.subTest():
            with SuppressStandard():
                with self.assertExit(2):
                    parser.parse_args("baz".split())

    def test_several_subparsers(self):
        """Test what happens when several subparsers are defined."""
        with SuppressStandard():
            parser = argdispatch.ArgumentParser()
            parser.add_subparsers()
            if sys.version_info < (3, 12):
                # Up to python3.11, program exits when adding two parsers
                with self.assertExit(2):
                    parser.add_subparsers()
            elif sys.version_info < (3, 14):
                # Starting with python3.12, an exception is raised when adding two parsers
                with self.assertRaises(argparse.ArgumentError):
                    parser.add_subparsers()
            else:
                # Starting with python3.14, a different exception is raised when adding two parsers
                with self.assertRaises(ValueError):
                    parser.add_subparsers()


class TestErrors(TestArgparse):
    """Test various errors."""

    def test_nocommand(self):
        """Test what happens when no subcommand is given."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_module("foo")

        self.assertIsInstance(parser.parse_args("".split()), argdispatch.Namespace)

        sub.required = True
        sub.dest = "subcommand"
        with SuppressStandard():
            with self.assertExit(2):
                parser.parse_args("".split())
