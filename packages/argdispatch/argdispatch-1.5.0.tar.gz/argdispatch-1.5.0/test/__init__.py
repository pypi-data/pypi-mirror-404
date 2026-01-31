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

"""Tests"""

import contextlib
import os
import re
import sys
import tempfile
import unittest

import argdispatch

from .redirector import redirect_stdout


class SuppressStandard:
    """A context manager suppressing standard output and error

    Adapted from an original work:
    By jeremiahbuddha https://stackoverflow.com/users/772487/jeremiahbuddha
    Copied from http://stackoverflow.com/q/11130156
    Licensed under CC by-sa 3.0.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, output=True, error=True):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = (os.dup(1), os.dup(2))

        self.output = output
        self.error = error

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        if self.output:
            os.dup2(self.null_fds[0], 1)
        if self.error:
            os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        if self.output:
            os.dup2(self.save_fds[0], 1)
        if self.error:
            os.dup2(self.save_fds[1], 2)
        # Close the null files
        os.close(self.null_fds[0])
        os.close(self.null_fds[1])


def testdatapath(*paths):
    """Return the given path, relative to the test data directory."""
    return os.path.join(os.path.dirname(__file__), "data", *paths)


class pythonpath(contextlib.ContextDecorator):
    """Decorator to extend ``sys.path``."""

    # pylint: disable=invalid-name, too-few-public-methods

    def __init__(self, *path):
        self.path = path

    def __enter__(self):
        sys.path = [testdatapath(path) for path in self.path] + sys.path
        return self

    def __exit__(self, *exc):
        sys.path = sys.path[len(self.path) :]
        return False


class binpath(contextlib.ContextDecorator):
    """Decorator to replace ``PATH`` argument variable."""

    # pylint: disable=invalid-name, too-few-public-methods

    def __init__(self, *path):
        self.path = path

    def __enter__(self):
        # pylint: disable=attribute-defined-outside-init
        # Making the python executable callable
        self.pythondir = tempfile.TemporaryDirectory()
        os.symlink(sys.executable, os.path.join(self.pythondir.name, "python"))
        # Setting path
        self.oldpath = os.environ.get("PATH")
        os.environ["PATH"] = ":".join(
            [self.pythondir.name] + [testdatapath(path) for path in self.path]
        )
        return self

    def __exit__(self, *exc):
        if self.oldpath is not None:
            os.environ["PATH"] = self.oldpath
        self.pythondir.cleanup()
        return False


class TestArgparse(unittest.TestCase):
    """Generic test class, defining some utilities."""

    @staticmethod
    def _ArgumentParser():
        """Return an `ArgumentParser` object."""
        # pylint: disable=invalid-name
        return argdispatch.ArgumentParser(prog=sys.executable)

    @contextlib.contextmanager
    def assertExit(self, code=None):
        """Assert that code calls :func:`sys.exit`.

        :param code: If not ``None``, fails if exit code is different from this argument.
        """
        # pylint: disable=invalid-name
        with self.assertRaises(SystemExit) as context:
            yield
        if code is None:
            return
        self.assertEqual(code, context.exception.code)

    @contextlib.contextmanager
    def assertStdoutMatches(self, pattern, *, count=None):
        """Assert that standard output matches the given pattern.

        :param int count: If not ``None``, fails if number of matches is
            different from this argument.
        """
        # pylint: disable=invalid-name
        with tempfile.NamedTemporaryFile() as writefile:
            with redirect_stdout(writefile.name):
                yield
            with open(writefile.name, encoding="utf8") as readfile:
                stdout = "".join(readfile.readlines())
        found = re.findall(pattern, stdout, flags=re.MULTILINE)
        if count is None:
            if not found:
                raise AssertionError(f"Pattern '{pattern}' not found in '{stdout}'.")
        else:
            self.assertEqual(len(found), count)
