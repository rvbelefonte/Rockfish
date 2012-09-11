"""
Argument parser for the rockfish programs.
"""
import argparse
#from rockfish.core.util import get_version

#VERSION = (0, 1, 0, 'alpha', 0)
#__version__ = get_version(VERSION)
__version__ = '0'

class ArgumentParser(argparse.ArgumentParser):
    """
    Base class for the rockfish argument parser.
    """

    def __init__(self, *args, **kwargs):
        argparse.ArgumentParser.__init__(self, *args, **kwargs)
        self.add_argument('--version', action='version', version='%(prog)s ' +
                          str(__version__))
