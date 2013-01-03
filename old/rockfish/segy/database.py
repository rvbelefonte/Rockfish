"""
Database methods for SEG-Y files.
"""
import sqlite3

TRACE_TABLE = 'trace_headers'

class SEGYHeaderDatabase(sqlite3.Connection):
    """
    Perform SQLite database methods on SEG-Y headers.
    """
    def __init__(self, segy, *args, **kwargs):
        if 'database' not in kwargs:
            database = ':memory:'
        else:
            database = kwargs['database']
        self.TRACE_TABLE = TRACE_TABLE
        sqlite3.Connection.__init__(self, database)
        # enable case-insensative keyword access to data rows
        self.row_factory = sqlite3.Row
        # add header values of interest to the database
        self.init_header_database(segy, *args)

    def init_header_database(self, segy, *args):
        """
        (Re)builds header data table.

        :param segy: :class:`SEGYFile` instance with ``traces[:].header``
        :param *args: Valid trace header attributes to store in the database.
        """
        sql = 'DROP TABLE IF EXISTS %s' %self.TRACE_TABLE
        self.execute(sql)

        sql = 'CREATE TABLE %s (' %self.TRACE_TABLE
        sql += ', '.join(['%s real' % a for a in args])
        sql += ')'
        self.execute(sql)

        sql = 'INSERT INTO %s (%s)' \
            %(self.TRACE_TABLE, ', '.join([a for a in args]))
        sql += ' VALUES (%s)' % ', '.join(['?' for a in args])
        data = []
        for tr in segy.traces:
            data.append(tuple([self._get_header_attribute(tr.header, a)\
                               for a in args]))
        self.executemany(sql, data)
        self.commit()

    def _get_header_attribute(self, header, attribute):
        """
        Gets a header attribute from the unpacked header if it is not already
        unpacked.  Allows for accessing attributes by a programatically-set
        name.
        
        :param attribute: Name of an attribute to get value for.
        """
        try:
            return header.__getattribute__(attribute)
        except AttributeError:
            return header.__getattr__(attribute)
