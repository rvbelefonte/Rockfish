#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command-line programs to view SEG-Y headers.
"""
import sys
import argparse
import rockfish

__version__ = rockfish.__version__

class ViewSegyTraceHeaderTable(object):
    """
    Interactively look at a table of SEG-Y trace headers.

    :based on: Dan Lizarralde's program segy.
    """
    def __init__(self, argv):
        """
        :param argv: Command-line arguments to pass to the argument parser.
        """
        pass




class View(object):
    """
    Class for the view command-line program. 
    """
    def __init__(self, argv):
        """
        :param argv: Command-line arguments to pass to the argument parser.
        """
        self.modes = ['table']

        self.parser = argparse.ArgumentParser(prog='view',
                                              description='View SEG-Y headers.')
        self.parser.add_argument(dest='segyfile',metavar='SEGY',type=str, 
                                 help='input SEG-Y format file')
        self.parser.add_argument('-m','--mode',dest='mode',default='table',
                                 choices=self.modes,
                                 help='view mode')
        self.parser.add_argument('--version', action='version',
                                  version='%(prog)s ' + str(__version__))

        self.args = self.parser.parse_args(argv)


if __name__ == '__main__':

    prog = View(sys.argv[1:])
    print prog.args
    #prog.run()

