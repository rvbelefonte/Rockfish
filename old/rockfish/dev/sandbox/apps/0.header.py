#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Work with SEG-Y trace headers.
"""
import sys
import warnings
from rockfish.apps.utils.argparser import ArgumentParser
from rockfish.segy.segy import readSEGY

class Header(object):
    """
    Base class for the header programs.
    """
    def __init__(self,argv=sys.argv[0]):
        """
        :param argv: Command-line arguments to read.
        """
        # Build the parser
        self.args = self.get_argparser(argv)
        # Load SEG-Y file
        self.sgy = readSEGY(self.args.segyfile)

    def get_argparser(self,argv):
        '''
        Parse command-line arguments and set up program help.

        :param argv: Command-line arguments to read.
        '''
        parser = ArgumentParser(description='Work with SEG-Y headers.',
                                         prog='header')
        parser.add_argument(dest='subcommand',metavar='<subcommand>',type=str)
        parser.add_argument(dest='segyfile',metavar='[SEG-Y file]',type=str, 
                            help='input SEG-Y format file')
        parser.add_argument(dest='options',metavar='[options]',type=str,
                            help='output sqlite database file')
        parser.add_argument(dest='args',metavar='[args]',type=str, 
                            help='output sqlite database file')

        return parser.parse_args()

    def run(self):
        """
        Executes the program.
        """
        print "running...",
        print "done."

class HeaderView(Header):
    """
    View SEG-Y trace headers.
    """
    def __init__(self,argv=sys.argv[0]):
        """
        :param argv: Command-line arguments to read.
        """
        self.argparser = self.get_argparser(argv)

    def get_argparser(self,argv):
        '''
        Parse command-line arguments and set up program help.

        :param argv: Command-line arguments to read.
        '''
        parser = ArgumentParser(description='View SEG-Y headers.'Work with SEG-Y headers.',
                                         prog='header')
        parser.add_argument(dest='subcommand',metavar='<subcommand>',type=str)
        parser.add_argument(dest='segyfile',metavar='[SEG-Y file]',type=str, 
                            help='input SEG-Y format file')
        parser.add_argument(dest='options',metavar='[options]',type=str,
                            help='output sqlite database file')
        parser.add_argument(dest='args',metavar='[args]',type=str, 
                            help='output sqlite database file')

        return parser.parse_args()

    def run(self):
        """
        Executes the program.
        """
        print "running...",
        print "done."


if __name__ == '__main__':

    prog = Header()
    prog.run()

