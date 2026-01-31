import sys


def some_function(args):
    """Documentation for some function."""
    print("Running some function({})".format(", ".join(args)))
    sys.exit(3)
