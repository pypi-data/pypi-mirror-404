==========================================
Welcome to argdispatch's documentation!
==========================================

This module is a drop-in replacement for :mod:`argparse`, dispatching :meth:`subcommand <argparse.ArgumentParser.add_subparsers>` calls to functions, modules or executables.

.. contents::
  :local:
  :backlinks: none

Rationale
=========

If your parser has less than five subcommands, you can parse them with :mod:`argparse`. If you have more, you still can, but you will get a huge, unreadable code. This module makes this easier by dispatching subcommand calls to functions, modules or executables.

Example 1 : Manually define subcommands
---------------------------------------

For instance, consider the following code for ``mycommand.py``::

   import sys
   from argdispatch import ArgumentParser

   def foo(args):
       """A function associated to subcommand `foo`."""
       print("Doing interesting stuff")
       sys.exit(1)

   if __name__ == "__main__":
       parser = ArgumentParser()
       subparser = parser.add_subparsers()

       subparser.add_function(foo)
       subparser.add_module("bar")
       subparser.add_executable("baz")

        parser.parse_args()

With this simple code:

* ``mycommand.py foo -v --arg=2`` is equivalent to the python code ``foo(['-v', '--arg=2'])``;
* ``mycommand.py bar -v --arg=2`` is equivalent to ``python -m bar -v --arg=2``;
* ``mycommand.py baz -v --arg=2`` is equivalent to ``baz -v --arg=2``.

Then, each function, module or executable does whatever it wants with the arguments.

Example 2 : Automatic subcommand definition
-------------------------------------------

With programs like `git <http://git-scm.com/>`_, if a ``git-foo`` executable exists, then calling ``git foo --some=arguments`` is equivalent to ``git-foo --some=arguments``. The following code, in ``myprogram.py`` copies this behaviour::

   import sys
   from argdispatch import ArgumentParser

   if __name__ == "__main__":
       parser = ArgumentParser()
       subparser = parser.add_subparsers()

       subparser.add_submodules("myprogram")
       subparser.add_prefix_executables("myprogram-")

       parser.parse_args()

With this program, given that executable ``myprogram-foo`` and python module ``myprogram.bar.__main__.py`` exist:

* ``myprogram foo -v --arg=2`` is equivalent to ``myprogram-foo -v --arg=2``;
* ``myprogram bar -v --arg=2`` is equivalent to ``python -m myprogram.bar -v --arg=2``.

Example 3 : Defining subcommands with entry points
--------------------------------------------------

Now that your program is popular, people start writing plugins. Great! You want to allow them to add subcommands to your program. To do so, simply use this code::

   import sys
   from argdispatch import ArgumentParser

   if __name__ == "__main__":
       parser = ArgumentParser()
       subparser = parser.add_subparsers()

       # You probably should only have one of those.
       subparser.add_entrypoints_functions("myprogram.subcommands.functions")
       subparser.add_entrypoints_modules("myprogram.subcommands.modules")

       parser.parse_args()

With this code, plugin writers can add lines like those in their ``pyproject.toml``::

    [project.entry-points."myprogram.subcommands.functions"]
    foo = mypluginfoo:myfunction

    [project.entry-points."myprogram.subcommands.modules"]
    bar = mypluginbar

Then, given than function ``myfunction()`` exists in module ``mypluginfoo``, and than module ``mypluginbar`` exists:

* ``myprogram foo -v --arg=2`` is equivalent to the python code ``myfunction(['-v', '--arg=2'])``;
* ``myprogram bar -v --arg=2`` is equivalent to ``python -m mypluginbar -v --arg=2``.

Module documentation
====================

.. automodule:: argdispatch

.. _advanced:

Advanced usage
==============

This module works by subclassing two :mod:`argparse` classes:

* :class:`_SubCommandsDispatch` is a subclass of :class:`argparse._SubParsersAction`;
* :class:`ArgumentParser` is a subclass of :class:`argparse.ArgumentParser`.

The class doing all the job is :class:`_SubCommandsDispatch`.

.. autoclass:: _SubCommandsDispatch
  :no-members:

The only thing changed in :class:`ArgumentParser` is :meth:`ArgumentParser.add_subparsers`, which enforces argument ``action=_SubCommandsDispatch`` for parent method :meth:`argparse.ArgumentParser.add_subparsers`. Thus, it is also possible to use this module as following::

    import argparse
    import argdispatch

    parser = argparse.ArgumentParser(...)
    subparsers = parser.add_subparsers(action=argdispatch._SubCommandsDispatch)
    ...

Download and install
====================

See the `main project page <http://framagit.org/spalax/argdispatch>`_ for
instructions, and `changelog
<https://framagit.org/spalax/argdispatch/blob/main/CHANGELOG.md>`_.
