"""
Database methods for SEG-Y files.
"""
from rockfish.database.database import RockfishDatabaseConnection
from rockfish.segy.header import TRACE_HEADER_FORMAT


TRACE_TABLE = 'trace_headers'

# Standard header fields
TRACE_FIELDS = [
    #(name, sql_type, default_value, is_not_null, is_primary)
    (_i[1], 'INTEGER', None, False, False) for _i in TRACE_HEADER_FORMAT]
TRACE_FIELDS[-1] = ('unassigned', 'BLOB', None, False, False)

# Extra header values
TRACE_FIELDS += [
    #(name, sql_type, default_value, is_not_null, is_primary)
    ('assembled_datetime_recorded', 'TEXT', None, False, False),
    ('computed_azimuth_in_deg', 'REAL', None, False, False),
    ('computed_backazimuth_in_deg', 'REAL', None, False, False),
    ('computed_source_receiver_offset_in_m', 'REAL', None, False, False),
    ('endian', 'TEXT', None, False, False),
    ('scaled_datum_elevation_at_receiver_group', 'REAL', None, False, False),
    ('scaled_datum_elevation_at_source', 'REAL', None, False, False),
    ('scaled_receiver_group_elevation', 'REAL', None, False, False),
    ('scaled_group_coordinate_x', 'REAL', None, False, False),
    ('scaled_group_coordinate_y', 'REAL', None, False, False),
    ('scaled_source_coordinate_x', 'REAL', None, False, False),
    ('scaled_source_coordinate_y', 'REAL', None, False, False),
    ('scaled_source_depth_below_surface', 'REAL', None, False, False),
    ('scaled_surface_elevation_at_source', 'REAL', None, False, False),
    ('scaled_water_depth_at_source', 'REAL', None, False, False)]


class SEGYHeaderDatabase(RockfishDatabaseConnection):
    """
    Perform SQLite database methods on SEG-Y headers.
    """
    def __init__(self, segy, *args, **kwargs):
        self.TRACE_TABLE = kwargs.pop('trace_table', TRACE_TABLE)
        self.TRACE_FIELDS = kwargs.pop('trace_fields', TRACE_FIELDS)
        if 'database' not in kwargs:
            database = ':memory:'
        else:
            database = kwargs['database']
        RockfishDatabaseConnection.__init__(self, database)
        # add header values to the database
        self.init_header_database(segy)

    def init_header_database(self, segy):
        """
        (Re)builds header data table.

        :param segy: :class:`SEGYFile` instance with ``traces[:].header``
        """
        sql = 'DROP TABLE IF EXISTS %s' %self.TRACE_TABLE
        self.execute(sql)

        self._create_table_if_not_exists(self.TRACE_TABLE, self.TRACE_FIELDS)

        sql = 'INSERT INTO %s (%s)' \
            %(self.TRACE_TABLE, ', '.join([a[0] for a in self.TRACE_FIELDS]))
        sql += ' VALUES (%s)' % ', '.join(['?' for a in self.TRACE_FIELDS])
        data = []
        for tr in segy.traces:
            data.append(tuple([str(
                self._get_header_attribute(tr.header, a[0]))\
                               for a in self.TRACE_FIELDS]))

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
