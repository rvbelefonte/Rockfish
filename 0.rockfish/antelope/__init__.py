# -*- coding: utf-8 -*-
#
#
"""
obspy antelope module
"""
from rockfish.antelope.core import (db2object, readANTELOPE)
from rockfish.antelope.dbobjects import (Dbrecord, DbrecordList)
from rockfish.antelope.dbpointers import (DbrecordPtr, DbrecordPtrList, AttribDbptr)
from rockfish.antelope.utils import (add_antelope_path, open_db_or_string)
