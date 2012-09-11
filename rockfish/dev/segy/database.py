"""
Database methods for SEG-Y files.
"""
import os
import sqlite3
from collections import OrderedDict
from rockfish.segy.segy import TRACE_HEADER_KEYS

# default table name
TRACE_TABLE = 'trace_headers'
# define SQLite data types for header attributes
TRACE_HEADER_TYPES = OrderedDict()
for k in TRACE_HEADER_KEYS:
    TRACE_HEADER_TYPES[k] = 'integer'
for k in ['scaled_datum_elevation_at_receiver_group',
    'scaled_datum_elevation_at_source', 'scaled_group_coordinate_x',
    'scaled_group_coordinate_y', 'scaled_receiver_group_elevation',
    'scaled_source_coordinate_x', 'scaled_source_coordinate_y',
    'scaled_source_depth_below_surface','scaled_surface_elevation_at_source',
    'scaled_water_depth_at_source']:
    TRACE_HEADER_TYPES[k] = 'real'
for k in ['assembled_datetime_recorded', 'endian']:
    TRACE_HEADER_TYPES[k] = 'text'
del(TRACE_HEADER_TYPES['unassigned'])
TRACE_HEADER_FIELDS = [k for k in TRACE_HEADER_TYPES]

class SEGYHeaderDatabase(sqlite3.Connection):
    """
    Perform SQLite database methods on SEG-Y headers.
    """
    def __init__(self, database=':memory:', segy=None, 
                 table_name=TRACE_TABLE, fields=None, force_new=False,
                 include_filename=False):
        """
        :param database: Optional. Name of the database file.  Default is to
            connect to a database in memory.
        :param segy: Optional. :class:`SEGYFile` with header data to load into
            the database. Default is just to create a build the header table
            if it does not already exist.
        :param table_name: Optional.  Name of the table to store header data
            in.  Default is ``'trace_headers'``.
        :param force_new: Optional.  If True, drops the existing trace header
            table and recreates it, destroying any existing data.  Default is
            False.
        :param include_filename: Optional.  If True, filename is stored along
            with each trace.  Default is False.
        """
        self.TRACE_TABLE = table_name 
        sqlite3.Connection.__init__(self, database)
        self.row_factory = sqlite3.Row
        if segy is not None:
            self.init_header_database(segy, fields=fields, force_new=force_new,
                                     include_filename=include_filename)
        else:
            if fields is None:
                fields = self._get_valid_header_fields(segy.traces[0].header)
            self._create_table(fields=fields, force_new=force_new, 
                               include_filename=include_filename)

    def init_header_database(self, segy, fields=None, force_new=False,
                             include_filename=False):
        """
        Convience function that creates a table and populates it with data. 

        :param segy: :class:`SEGYFile` instance with ``traces[:].header``
        :param fields: Optional. List of valid trace header attributes to store 
            in the database. Default is to store all available attributes.
        :param force_new: Optional.  If True, drops the existing trace header
            table and recreates it, destroying any existing data.  Default is
            False.
        :param include_filename: Optional.  If True, filename is stored along
            with each trace.  Default is False.
        """
        if fields is None:
            fields = self._get_valid_header_fields(segy.traces[0].header)
        self._create_table(fields=fields, force_new=force_new, 
                           include_filename=include_filename)
        self.append_from_segy(segy, fields=fields,
                              include_filename=include_filename)

    def append_from_segy(self, segy, fields=None,
                         include_filename=False):
        """
        Appends data from a SEGYFile instance.

        :param segy: :class:`SEGYFile` instance with ``traces[:].header``
        :param fields: Optional. List of valid trace header attributes to store 
            in the database. Default is to store all available attributes.
        :param include_filename: Optional.  If True, filename is stored along
            with each trace.  Default is False.
        """
        if fields is None:
            fields = self._get_valid_header_fields(segy.traces[0].header)
        if include_filename:
            filename = os.path.abspath(segy.file.name)
            extra_fields = ['filename']
        else:
            extra_fields = []
        sql = 'INSERT INTO %s (%s)' \
            %(self.TRACE_TABLE, ', '.join(fields + extra_fields))
        sql += ' VALUES (%s)' % ', '.join(['?' for f in fields + extra_fields])
        data = []
        for tr in segy.traces:
            data.append(tuple([self._get_header_attribute(tr.header, f)\
                               for f in fields]))
            if include_filename:
                data[-1] += (filename,)
        self.executemany(sql, data)
        self.commit()

    def _create_table(self, fields=TRACE_HEADER_FIELDS, force_new=False,
                      include_filename=False):
        """
        (Re)builds the trace header table.
        
        :param fields: Optional.  List of valid trace header attributes to
            create fields for.  Default is to create fields for all
            SEGYTraceHeader attributes.
        :param force_new: Optional.  If True, drops the existing trace header
            table and recreates it, destroying any existing data.  Default is
            False.
        :param include_filename: Optional.  If True, filename is stored along
            with each trace.  Default is False.
        """
        _fields = []
        for f in fields:
            if f in TRACE_HEADER_TYPES:
                _type = TRACE_HEADER_TYPES[f]
            else:
                _type = 'text'
            _fields.append('%s %s' %(f, _type))
        if include_filename:
            _fields.append('filename text')
        if force_new:
            sql = 'DROP TABLE IF EXISTS %s' %self.TRACE_TABLE
            self.execute(sql)
        sql = 'CREATE TABLE IF NOT EXISTS %s (' %self.TRACE_TABLE
        sql += ', '.join(_fields) + ')'
        self.execute(sql)
        self.commit()

    def _get_valid_header_fields(self, header):
        """
        Returns a list of header attributes that with a defined SQLite data
        type.
        """
        fields = []
        for f in dir(header):
            if f in TRACE_HEADER_FIELDS:
                fields.append(f)
        return fields

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
