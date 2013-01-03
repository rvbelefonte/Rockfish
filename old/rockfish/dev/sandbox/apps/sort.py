#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command-line programs for sorting SEG-Y files.
"""
import sys
import argparse
import rockfish
from rockfish.segy.segy import TRACE_HEADER_FORMAT

__version__ = rockfish.__version__

class Sort(object):
    """
    Class for the view command-line program. 
    """
    def __init__(self, argv):
        """
        :param argv: Command-line arguments to pass to the argument parser.
        """
        self.parser = argparse.ArgumentParser(prog='sort',
                description='Sort a SEG-Y file by trace-header attributes.')
        self.parser.add_argument(dest='segyfile',metavar='INPUT_SEGY',type=str, 
                                 help='input SEG-Y file')
        self.parser.add_argument(dest='segyfile',metavar='OUTPUT_SEGY',type=str,
                                 help='output SEG-Y file')
        self.parser.add_argument('-k',dest='keys',default=None,
                                 metavar='key',
                                 choices=[k[1] for k in TRACE_HEADER_FORMAT], 
                                 nargs='+',help='sort keys')
        self.parser.add_argument('--version', action='version',
                                  version='%(prog)s ' + str(__version__))

        self.args = self.parser.parse_args(argv)


if __name__ == '__main__':

    prog = Sort(sys.argv[1:])
    print prog.args
    #prog.run()

