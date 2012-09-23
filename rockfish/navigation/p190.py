"""
Support for working with UKOOA P1/90 files.
"""
import os
import logging
import warnings
from rockfish.database.database import RockfishDatabaseConnection

# Table for the 'Header record specification'
HEADER_TABLE = 'headers'
HEADER_FIELDS = [
    #(name, sql_type, default_value, is_not_null, is_primary)
    ('record_id', 'TEXT', None, True, False),
    ('type', 'TEXT', None, True, False),
    ('type_modifier', 'TEXT', None, True, False),
    ('description', 'TEXT', None, True, False),
    ('value', 'TEXT', None, True, False)]
# Table for "TYPE 1 : GRID OR GEOGRAPHICAL COORDINATES"
COORDINATE_TABLE = 'coordinates'
COORDINATE_IDS = {'S':'Centre of Source',
                  'G':'Receiver Group',
                  'Q':'Bin Centre',
                  'A':'Antenna Position',
                  'T':'Tailbuoy Position',
                  'C':'Common Mid Point',
                  'V':'Vessel Reference Point',
                  'E':'Echo Sounder',
                  'Z':'Other, defined in H0800'}
COORDINATE_FIELDS = [
    #(name, sql_type, default_value, is_not_null, is_primary)
    ('point_number', 'TEXT', None, True, False),
    ('record_id', 'TEXT', None, True, False),
    ('record_description', 'TEXT', None, True, False),
    ('line_name', 'TEXT', None, True, False),
    ('spare', 'TEXT', None, False, False),
    ('vessel_id', 'TEXT', None, False, False),
    ('source_id', 'TEXT', None, False, False),
    ('tailbuoy_id', 'TEXT', None, False, False),
    ('latitude', 'TEXT', None, True, False),
    ('longitude', 'TEXT', None, True, False),
    ('easting', 'TEXT', None, True, False),
    ('northing', 'TEXT', None, True, False),
    ('water_depth_or_elev', 'TEXT', None, True, False),
    ('day_of_year', 'TEXT', None, True, False),
    ('time', 'TEXT', None, True, False),
    ('spare2', 'TEXT', None, False, False)]
# Table for "TYPE 1, ITEM 16: RECEIVER GROUP RECORDS (3-D OFFSHORE SURVEYS)"
RECEIVER_TABLE = 'receiver_groups'
RECEIVER_FIELDS = [
    #(name, sql_type, default_value, is_not_null, is_primary)
    ('line_name', 'TEXT', None, True, False),
    ('source_point_number', 'INTEGER', None, True, False),
    ('receiver_group_number', 'INTEGER', None, True, False),
    ('easting', 'REAL', None, True, False),
    ('northing', 'REAL', None, True, False),
    ('cable_depth', 'REAL', None, True, False),
    ('streamer_id', 'INTEGER', None, True, False)]

class P190EllipseError(Exception):
    """
    Raised if there is a problem with the ellipse used by P190 geodetic
    calculations.
    """
    pass
        
class P190(RockfishDatabaseConnection):
    """
    Class for working with UKOOA P1/90 data.
    """

    def __init__(self, filename=None, database=':memory:', *args, **kwargs):
        """
        Class for working with UKOOA P1/90 data.

        :param filename: Optional. Filename of a P1/90 file to read data from.
            Default is to create an empty P190 class instance.
        :param database: Optional. Filename of a SQLite database to store P1/90
            data in. Default is to create a temporary database in memory.
        :param *args: Optional.  Arguments to pass to
            :class:`sqlite3.Connection`
        :param *kwargs: Optional.  Keyword arguments to pass to
            :class:`sqlite3.Connection`
        """
        RockfishDatabaseConnection.__init__(self, database, *args, **kwargs)
        self.HEADER_TABLE = HEADER_TABLE
        self.COORDINATE_TABLE = COORDINATE_TABLE
        self.RECEIVER_TABLE = RECEIVER_TABLE
        self._create_tables()
        self.filename = filename
        self.read()

    def read(self, filename=None):
        """
        Read data from a P1/90 file and store it in the database.
        
        :param file: Optional.  Filename of a P1/90 file to read data from.
            Default is to read data from the file associated with the current
            P190 instance (self.file).
        """
        if filename is None:
            file = open(self.filename)
        else:
            file = open(filename)
        self._read(file)

    def _read(self, file):
        """
        Read data from a file-like object and store it in the database.

        :param file: A file like object with the file pointer set at the
            beginning of a p190 file.
        """
        for i, line in enumerate(file):
            try:
                if line[0] == 'H':
                    self._read_header_line(line)
                elif line[0] in COORDINATE_IDS:
                    line_name, source_point_number = \
                        self._read_coordinate_line(line)
                elif line[0] == 'R':
                    self._read_receiver_line(line, line_name,
                                             source_point_number)
            except:
                msg = "Skipping invalid record on line {:d} of {:}."\
                        .format(i, file.name)
                warnings.warn(msg)
        self.commit()

    def _read_header_line(self, line):
        """
        Parse a single header record.

        :param line: String record from the header section of a p190 file.
        """
        assert line[0] == 'H', "Line is not a header record."
        d = {'record_id':line[0],
             'type':line[1:3],
             'type_modifier':line[3:5],
             'description':line[5:32].strip(),
             'value':line[32:80].strip()}
        self._insert(self.HEADER_TABLE, **d)

    def _read_coordinate_line(self, line):
        """
        Parse a single coordinate record.
        
        :param line: String for a coordinate record in a p190 file.
        """
        assert line[0] in COORDINATE_IDS, "Line is not a coordinate record."
        d = {'record_id':line[0],
             'record_description':COORDINATE_IDS[line[0]],
             'line_name':line[1:13].strip(),
             'spare':line[13:16],
             'vessel_id':line[16],
             'source_id':line[17],
             'tailbuoy_id':line[18],
             'point_number':line[19:25],
             'latitude':line[25:35],
             'longitude':line[35:46],
             'easting':line[46:55],
             'northing':line[55:64],
             'water_depth_or_elev':line[64:70],
             'day_of_year':line[70:73],
             'time':line[73:79],
             'spare2':line[79]}
        if d['record_id'] == 'Z':
            sql = 'SELECT value FROM ' + self.HEADER_TABLE
            sql += " WHERE record_id='H' AND type='08' AND type_modifier='00'"
            description = self.execute(sql).fetchone()
            if len(description) > 0:
                d['record_description'] = description[0]
            else:
                msg = """
                      Record type of id='Z' should be defined by
                      'H0800', but 'H0800' has not been defined.
                      """.strip()
                warnings.warn(msg)
        self._insert(self.COORDINATE_TABLE, **d)
        return d['line_name'], d['point_number']

    def _read_receiver_line(self, line, line_name, source_point_number):
        """
        Parse a single reciever record.
        
        :param line: String for a receiver group record in a p190 file.
        """
        assert line[0] == 'R', "Line is not a reciever group record."
        i2 = 1
        for i in range(0,3):
            i1 = i2
            i2 = (i + 1) * 26 + 1
            _line = line[i1:i2]
            d = {'source_point_number':source_point_number,
                 'line_name':line_name,
                 'receiver_group_number':_line[0:4],
                 'easting':_line[4:13],
                 'northing':_line[13:22],
                 'cable_depth':_line[22:26],
                 'streamer_id':line[79]}
            self._insert(self.RECEIVER_TABLE, **d)

    def write(self, filename, output_format='p190', table=':all:'):
        """
        Write P1/90 navigation data.

        :param filename: Filename to write data to.
        :param output_format: Optional. Format to write out data in. Supported
            formats are 'p190' and 'csv'. Default is 'p190'.
        """
        if output_format is 'p190':
            self._write_p190(filename)
        elif output_format is 'csv':
            self._write_csv(filename)
        else:
            msg = "Writing to format '{:}' is not supported"\
                    .fileformat(output_format)
            raise NotImplementedError(msg)

    def _write_csv(self, filename, tables=None, include_p190_header=False):
        """
        Write P1/90 data in comma-separated value format.
        
        :param filename: Filename to write data to. If more than one table is
            exported, files are named as 
            ``<dirname>/<basename>.<table_name>.csv``.
        :param table: Optional. List of database table names to write data
            from. Default is data from each table in the database.
        :param include_p190_header: Optional. Determines whether or not to
            include the p190 header records in a commented block at the top of
            each csv file. Default is False.
        """
        if tables is None:
            tables = [self.HEADER_TABLE, self.COORDINATE_TABLE,
                      self.RECEIVER_TABLE]
        if include_p190_header:
            header = ['#{:}\n'.format(line) for line in
                    self._get_p190_header().split('\n')]
        for table in tables:
            if len(tables) > 1:
                _filename = '{:}/{:}.{:}.csv'.format(os.path.dirname(filename),
                    os.path.basename(filename).replace('.csv',''),table)
            else:
                _filename = filename
            file = open(_filename, 'w')
            if include_p190_header:
                file.write(header)
            fields = self._get_fields(table)
            file.write(', '.join(fields))
            file.write('\n')
            sql = 'SELECT ' + ','.join(fields) + ' FROM ' + table
            for row in self.execute(sql):
                file.write(', '.join([str(row[f]) for f in fields]))
                file.write('\n')
            
    def _write_p190(self, filename):
        """
        Write P1/90 data in the UKOOA P1/90 format.
        
        :param file: Open file-like object with write-access.
        """
        file = open(filename, 'w')
        # Write header
        file.write(self._get_p190_header())
        # Write shot and reciever records
        sql = 'SELECT line_name,point_number FROM ' + self.COORDINATE_TABLE
        sql += ' ORDER BY day_of_year,time'
        for row in self.execute(sql).fetchall():
            # Write the coordinate records for this shot point
            sql = 'SELECT record_id,line_name,spare,vessel_id,source_id,'
            sql += 'tailbuoy_id,point_number,latitude,longitude,easting,'
            sql += 'northing,water_depth_or_elev,day_of_year,time,spare2'
            sql += ' FROM ' + self.COORDINATE_TABLE
            sql += " WHERE line_name='{:}' AND point_number={:}"\
                    .format(row['line_name'], row['point_number'])
            for coord in self.execute(sql).fetchall():
                sng = '{:1s}{:12s}{:3s}{:1s}{:1s}{:1s}{:6s}{:10s}{:10s}'\
                        '{:9s}{:9s}{:6s}{:3s}{:6s}{:1s}\n'\
                        .format(*[str(v) for v in coord])
                file.write(sng)
            # Write the receiver records for this shot point
            sql = 'SELECT * FROM ' + self.RECEIVER_TABLE
            sql += " WHERE line_name='{:}' and source_point_number={:}"\
                    .format(coord['line_name'], coord['point_number'])
            sql += " ORDER BY receiver_group_number"
            for i,rec in enumerate(self.execute(sql).fetchall()):
                if i%3 == 0:
                    sng = 'R'
                dat = [int(rec['receiver_group_number']),
                       float(rec['easting']),
                       float(rec['northing']),
                       float(rec['cable_depth'])]
                sng += '{:04d}{:9.1f}{:9.1f}{:4.1f}'.format(*dat)
                if i%3 == 2:
                    sng += '{:1d}\n'.format(int(rec['streamer_id']))
                    file.write(sng)

    def print_header(self):
        """
        Prints the P1/90 formated header.
        """
        print self._get_p190_header()

    def _get_p190_header(self):
        """
        Get header data in the P1/90 format.
        """
        sql = 'SELECT record_id,type,type_modifier,description,value'
        sql += ' FROM ' + self.HEADER_TABLE
        sql += ' ORDER BY record_id,type,type_modifier'
        sng = ""
        for row in self.execute(sql).fetchall():
            sng += "{:1s}{:2s}{:2s}{:27s}{:48s}\n".format(*row)
        return sng

    def _create_tables(self):
        """
        Create database tables if they do not already exist.
        """
        self._create_table_if_not_exists(self.HEADER_TABLE,
                                         HEADER_FIELDS)
        self._create_table_if_not_exists(self.COORDINATE_TABLE,
                                         COORDINATE_FIELDS)
        self._create_table_if_not_exists(self.RECEIVER_TABLE,
                                         RECEIVER_FIELDS)

    def _set_ellipse(self, ellps=None):
        """
        Sets the ellipse for coordinate calculations.
        
        :param ellps: Optional. If given, set ``ELLIPSE`` to custom value. Should
            be a :mod:`pyproj` ellipse.  Default is to use the ellipse name in
            the p190 header.
        """
        if ellps is None:
            sql = 'SELECT value FROM ' + self.HEADER_TABLE
            sql += " WHERE record_id='H' AND type='14' AND type_modifier='00'"
            value = self.execute(sql).fetchone()
            if len(value) == 1:
                self.ELLIPSE = value[0]
            else:
                raise P190EllipseError('Could not find ellipse in header.')
        else:
            self.ELLIPSE = ellps
        logging.debug("set ELLIPSE='%s'", self.ELLIPSE)
