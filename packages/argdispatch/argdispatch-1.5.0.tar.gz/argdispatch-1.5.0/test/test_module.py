# Copyright 2016-2026 Louis Paternault
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

# type: ignore[reportMissingImports]

"""Tests of the add_module() and add_submodules() methods."""

import argdispatch

from . import TestArgparse, pythonpath


class TestModule(TestArgparse):
    """Test that add_submodules() and add_module() work."""

    @pythonpath("pythonpath1", "pythonpath2.zip")
    def test_module1(self):
        """Test the `add_module` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_module("foo")
        sub.add_module("foo.bar", "bar")
        sub.add_module("zipfoo")
        sub.add_module("zipfoo.zipbar", "zipbar")
        with self.subTest():
            with self.assertStdoutMatches(r"^Running python module foo.__main__\s*$"):
                with self.assertExit(0):
                    parser.parse_args("foo".split())
            with self.assertStdoutMatches(
                r"^Running python module foo.bar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("bar".split())
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module zipfoo.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("zipfoo".split())
            with self.assertStdoutMatches(
                r"^Running python module zipfoo.zipbar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("zipbar".split())

    @pythonpath("pythonpath1", "pythonpath2.zip")
    def test_module2(self):
        """Test the `add_module` method."""
        #  pylint: disable=import-outside-toplevel, import-error
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        import foo
        import zipfoo

        sub.add_module(foo)
        sub.add_module(foo.bar, "bar")
        sub.add_module(zipfoo)
        sub.add_module(zipfoo.zipbar, "zipbar")
        with self.subTest():
            with self.assertStdoutMatches(r"^Running python module foo.__main__\s*$"):
                with self.assertExit(0):
                    parser.parse_args("foo".split())
            with self.assertStdoutMatches(
                r"^Running python module foo.bar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("bar".split())
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module zipfoo.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("zipfoo".split())
            with self.assertStdoutMatches(
                r"^Running python module zipfoo.zipbar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("zipbar".split())

    @pythonpath("pythonpath1", "pythonpath2.zip")
    def test_relative_module(self):
        """Test the `add_submodules` method, with relative modules."""
        #  pylint: disable=import-outside-toplevel, import-error
        from foo import bar
        from zipfoo import zipbar

        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_module(bar)
        sub.add_module(zipbar)
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module zipfoo.zipbar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("zipfoo.zipbar".split())
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module foo.bar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("foo.bar".split())

    @pythonpath("pythonpath1")
    def test_ignore_error(self):
        """Test the `add_module` method."""
        parser = argdispatch.ArgumentParser(prog="test")
        sub = parser.add_subparsers()

        with self.subTest():
            sub.add_module("foo.importerror", onerror=argdispatch.IGNORE)

        with self.subTest():
            with self.assertStdoutMatches(
                r"foo",
                count=0,
            ):
                with self.assertExit(0):
                    parser.parse_args("--help".split())

    @pythonpath("pythonpath1", "pythonpath2.zip")
    def test_add_submodules1(self):
        """Test the `add_submodules` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_submodules("foo")
        sub.add_submodules("zipfoo")
        sub.add_submodules("foo.notmain")
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module foo.bar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("bar".split())
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module zipfoo.zipbar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("zipbar".split())

    @pythonpath("pythonpath1", "pythonpath2.zip")
    def test_add_submodules2(self):
        """Test the `add_submodules` method."""
        #  pylint: disable=import-outside-toplevel, import-error
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        import foo
        import zipfoo

        sub.add_submodules(foo)
        sub.add_submodules(zipfoo)
        sub.add_submodules(foo.notmain)
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module foo.bar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("bar".split())
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module zipfoo.zipbar.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("zipbar".split())

    @pythonpath("pythonpath3")
    def test_forcemain1(self):
        """Test the forcemain option"""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()

        #  pylint: disable=import-outside-toplevel, import-error, multiple-imports
        import notapackage
        import withinit
        import withinit2
        import withmain
        import withoutinit

        with self.subTest():
            sub.add_module(withmain, forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module(notapackage, forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module(withinit, forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module(withinit2, forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module(withoutinit, forcemain=True)
        with self.subTest():
            sub.add_module(withoutinit, forcemain=True, onerror=argdispatch.IGNORE)

    @pythonpath("pythonpath3")
    def test_forcemain2(self):
        """Test the forcemain option"""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()

        with self.subTest():
            sub.add_module("withmain", forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module("notapackage", forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module("withinit", forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module("withinit2", forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module("withoutinit", forcemain=True)
        with self.subTest():
            sub.add_module("withoutinit", forcemain=True, onerror=argdispatch.IGNORE)


class TestErrors(TestArgparse):
    """Test various errors."""

    def test_invalid_module_arguments(self):
        """Test invalid type of `add_module()` and `add_submodules()` arguments."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()

        with self.subTest():
            with self.assertRaises(TypeError):
                sub.add_module(1429)
        with self.subTest():
            with self.assertRaises(TypeError):
                sub.add_submodules(42)

    @pythonpath("pythonpath1", "pythonpath2.zip")
    def test_module(self):
        """Test the `add_module` method, with modules that cannot be imported."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module("???doesnotexist???")
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module("importerror")

    def test_relative_module(self):
        """Test the `add_submodules` method, with relative modules."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        with self.assertRaises(NotImplementedError):
            sub.add_submodules(".foo")

    @pythonpath("pythonpath1", "pythonpath2.zip")
    def test_add_submodules(self):
        """Test the `add_submodules` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        with self.subTest():
            sub.add_submodules("foo", onerror=argdispatch.IGNORE)
        with self.subTest():
            with self.assertRaises(Exception):
                sub.add_submodules("foo", onerror=argdispatch.RAISE)


class TestPath(TestArgparse):
    """Test the ``path`` argument."""

    @pythonpath("pythonpath3")
    def test_module_or_package(self):
        """Test various errors related to modules and packages."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module("withinit", forcemain=True)
        with self.subTest():
            with self.assertRaises(ImportError):
                sub.add_module("withoutinit", forcemain=True)
        sub.add_module("notapackage")
        sub.add_module("withinit2.foo")
        sub.add_module("withmain")
        with self.subTest():
            with self.assertStdoutMatches(r"^Running python module notapackage\s*$"):
                with self.assertExit(0):
                    parser.parse_args("notapackage".split())
        with self.subTest():
            with self.assertStdoutMatches(r"^Running python module withinit2.foo\s*$"):
                with self.assertExit(0):
                    parser.parse_args("withinit2.foo".split())
        with self.subTest():
            with self.assertStdoutMatches(
                r"^Running python module withmain.__main__\s*$"
            ):
                with self.assertExit(0):
                    parser.parse_args("withmain".split())


class TestHelp(TestArgparse):
    """Test that subcommand help works."""

    @pythonpath("pythonpath1", "pythonpath2.zip")
    def test_module(self):
        """Test of help for ``add_module`` method."""
        parser = argdispatch.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_module("foo", "foo1")
        sub.add_module("foo", "foo2", help="This is the help of foo2.")

        with self.subTest():
            with self.assertStdoutMatches(
                """foo1.*This is the docstring of module foo."""
            ):
                with self.assertExit(0):
                    parser.parse_args("--help".split())

        with self.subTest():
            with self.assertStdoutMatches("""foo2.*This is the help of foo2."""):
                with self.assertExit(0):
                    parser.parse_args("--help".split())
