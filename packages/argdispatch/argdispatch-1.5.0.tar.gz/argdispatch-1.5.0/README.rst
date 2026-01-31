argdispatch 🐈 Drop-in replacement for `argparse` dispatching subcommand calls to functions, modules or binaries
================================================================================================================

If your parser has a few subcommands, you can parse them with ``argparse``. If you have more, you still can, but you will get a huge, unreadable code. This module makes this easier by dispatching subcommand calls to functions, modules or binaries.

Examples
--------

Example 1 : Manual definition of subcommands
""""""""""""""""""""""""""""""""""""""""""""

For instance, consider the following code for ``mycommand.py``:

.. code-block:: python

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

Then, each function, module or binary does whatever it wants with the arguments.

Example 2 : Automatic definition of subcommands
"""""""""""""""""""""""""""""""""""""""""""""""

With programs like `git <http://git-scm.com/>`_, if a ``git-foo`` binary exists, then calling ``git foo --some=arguments`` is equivalent to ``git-foo --some=arguments``. The following code, in ``myprogram.py`` copies this behaviour:

.. code-block:: python

   import sys
   from argdispatch import ArgumentParser

   if __name__ == "__main__":
       parser = ArgumentParser()
       subparser = parser.add_subparsers()

       subparser.add_submodules("myprogram")
       subparser.add_prefix_executables("myprogram-")

       parser.parse_args()

With this program, given that binary ``myprogram-foo`` and python module ``myprogram.bar.__main__.py`` exist:

* ``myprogram foo -v --arg=2`` is equivalent to ``myprogram-foo -v --arg=2``;
* ``myprogram bar -v --arg=2`` is equivalent to ``python -m myprogram.bar -v --arg=2``.

Example 3 : Defining subcommands with entry points
--------------------------------------------------

Now that your program is popular, people start writing plugins. Great! You want to allow them to add subcommands to your program. To do so, simply use this code:

.. code-block:: python

   import sys
   from argdispatch import ArgumentParser

   if __name__ == "__main__":
       parser = ArgumentParser()
       subparser = parser.add_subparsers()

       # You probably should only have one of those.
       subparser.add_entrypoints_functions("myprogram.subcommand.function")
       subparser.add_entrypoints_modules("myprogram.subcommand.module")

       parser.parse_args()

With this code, plugin writers can add lines like those in their ``setup.cfg``:

.. code-block:: cfg

   [options.entry_points]
   myprogram.subcommand.function =
       foo = mypluginfoo:myfunction
   myprogram.subcommand.module =
       bar = mypluginbar

Then, given than function ``myfunction()`` exists in module ``mypluginfoo``, and than module ``mypluginbar`` exists:

* ``myprogram foo -v --arg=2`` is equivalent to the python code ``myfunction(['-v', '--arg=2'])``;
* ``myprogram bar -v --arg=2`` is equivalent to ``python -m mypluginbar -v --arg=2``.

Documentation
"""""""""""""

The complete documentation is available on `readthedocs <http://argdispatch.readthedocs.io>`_.

To compile it from source, download and run::

      cd doc && make html

What's new?
-----------

See `changelog <https://framagit.org/spalax/argdispatch/blob/main/CHANGELOG.md>`_.

Download and install
--------------------

* From sources:

  * Download: https://pypi.python.org/pypi/argdispatch
  * Install (in a `virtualenv`, if you do not want to mess with your distribution installation system)::

        python3 -m pip install .

* From pip::

    pip install argdispatch

* Quick and dirty Debian (and Ubuntu?) package

  This requires `stdeb <https://github.com/astraw/stdeb>`_ to be installed::

      python3 setup.py --command-packages=stdeb.command bdist_deb
      sudo dpkg -i deb_dist/argdispatch-<VERSION>_all.deb
