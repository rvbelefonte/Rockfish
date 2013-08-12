import os
import sys

from numpy import array
from obspy.core import read, Stream, UTCDateTime
from rockfish.antelope.utils import add_antelope_path
from rockfish.antelope.dbobjects import Dbrecord, DbrecordList 
# Antelope path to python tools not added by default install
add_antelope_path()               # adds path if not there
from antelope.datascope import *  # all is necessary for db query variables
from rockfish.utils.loaders import get_example_file

if __name__ == "__main__":


    # read Antelope database
    database = get_example_file('demo')

    print database

    db = dbopen(database, 'r')
    db = dblookup(db, table='wfdisc')

    for db.record in range(db.nrecs()):

        fname = db.filename()
        print fname

        _st = read(fname)


