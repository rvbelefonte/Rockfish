#!/usr/bin/env python
"""
Load SEG-Y trace header attributes into a SQLite database.
"""
import os
import argparse
import inspect
import sqlite3
import rockfish
import datetime
from rockfish.segy.segy import readSEGY
# XXX still in dev!
from rockfish.dev.segy.database import SEGYHeaderDatabase, TRACE_TABLE, TRACE_HEADER_TYPES

def get_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description='description: load SEG-Y trace header attributes into a SQLite database',
        prog=os.path.basename(__file__))
    parser.add_argument(dest='dbfile',metavar='DBFILE',type=str, help='output SQLite database file')
    parser.add_argument(dest='segyfiles',metavar='SEGYFILE',type=str,nargs='+',help='input SEG-Y file')
    parser.add_argument('-t','--table_name',dest='table_name', default=TRACE_TABLE, metavar='TABLENAME',
        help='name of table to add data to (default=SEGYTraceHeaders)')
    parser.add_argument('--no_standard_headers',dest='no_standard_headers',default=False,action='store_true',
        help='do not add data from the standard header fields')
    parser.add_argument('--scale_headers',dest='scale_headers',default=False,action='store_true',
        help='include real-valued versions of coordinates and elevations')
    parser.add_argument('--computed_headers',dest='computed_headers',default=False,action='store_true',
        help='include commonly-computed header attributes') 
    parser.add_argument('--include_filename',dest='include_filename',default=False,action='store_true',
        help='include filepath in table data') 
    parser.add_argument('-f','--force',dest='force',default=False,action='store_true',
        help='force creation of TABLENAME')
    parser.add_argument('--version', action='version', version='%(prog)s ' +
                            str(rockfish.__version__))
    return parser.parse_args()

def main():
    args = get_args()
    is_first_file = True
    for filename in args.segyfiles:
        segy = readSEGY(filename, unpack_headers = not args.no_standard_headers,
                        scale_headers=args.scale_headers,
                        computed_headers=args.computed_headers,
                        unpack_data=False)
        if is_first_file:
            sdb = SEGYHeaderDatabase(database=args.dbfile, segy=segy,
                                     table_name=args.table_name,
                                     force_new=args.force,
                                     include_filename=args.include_filename)
            is_first_file = False
        else:
            sdb.append_from_segy(segy)

if __name__ == '__main__':
    main()
