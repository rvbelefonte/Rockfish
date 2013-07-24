"""
Support for building and managing traveltime databases

Features
========

    - Stores traveltimes in a pyspatiallite database


Data tables
===========

events
------

Table of event names

times
-----

Table of traveltimes.

receiver_ids
------

Table of source and receiver locations for each receiver_id.

model_lines
-----------

Table defining 2D model lines.  Used for projecting 3D source and receiver
coordinates onto 2D lines.


Geometry Views
==============

source_receiver_paths
---------------------

Straight-line paths connecting source points to receiver points for each
traveltime.

source_points, receiver_points
------------------------------

Source and receiver locations for each traveltime.

VM Tomography Views
===================

vmtomo_picks
------------

vmtomo_sources
--------------

vmtomo_receivers
----------------

"""
import os
import logging
from pyspatialite.dbapi2 import Connection as SQLiteConnection
from pyspatialite.dbapi2 import IntegrityError
from rockfish.utils.user_input import query_yes_no

DEFAULT_EPSG = 4326

EPSG_SETUP_SQL = os.path.join(os.path.dirname(__file__), 'epsg-sqlite.sql')

# XXX dev
logging.basicConfig(level='DEBUG')


sql_POINT_XYZ = lambda x, y, z, epsg:\
        "GeomFromText('POINTZ({:} {:} {:})', {:})".format(x, y, z, epsg)

sql_POINT_XY = lambda x, y, epsg:\
        "GeomFromText('POINT({:} {:})', {:})".format(x, y, epsg)

def pad(value):

    if str(value).startswith('GeomFromText'):
        return value
    elif type(value) in [unicode, str]:
        return "'{:}'".format(value)
    else:
        return '{:}'.format(value)


class IntegrityError(IntegrityError):
    """
    Raised when database lacks required tables or data.
    """
    pass

class DatabaseConnection(SQLiteConnection):
    """
    Base class for interacting with databases
    """
    def __init__(self, *args, **kwargs): 
        database = kwargs.pop('database', ':memory:')
        if database == ':memory:':
            logging.warn('Creating new database in memory.')
        elif os.path.isfile(database):
            logging.info('Connecting to existing database: {:}'\
                         .format(database))
        else:
            logging.info('Creating new database: {:}'.format(database))
        SQLiteConnection.__init__(self, database, *args, **kwargs)

    def _init_spatial_metadata(self):

        sql = 'SELECT InitSpatialMetadata()'
        self.execute(sql)

    def executefile(self, sqlfile):
        """
        Read a sqlite script and execute it.
        """
        with open(sqlfile, 'r') as f:
            sql = f.read()
        logging.debug('SQL:\n{:}'.format(sql))
        return self.executescript(sql)

    def execute(self, *args):
        """
        Execute sql code
        """
        logging.debug('SQL: ' + ' '.join([str(a) for a in args]))
        return SQLiteConnection.execute(self, *args)

    def _get_tables(self):
        """
        Returns a list of tables in the database.
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        return [d[0] for d in self.execute(sql)]
    TABLES = property(_get_tables)

    def _get_views(self):
        """
        Returns a list of views in the database.
        """
        sql = "SELECT name FROM sqlite_master WHERE type='view'"
        return [d[0] for d in self.execute(sql)]
    VIEWS = property(_get_views)

    def _get_pragma(self, table):
        """
        Return the SQLite PRAGMA information.

        :param table: Name of table to get PRAGMA for.
        :type table: ``str``
        """
        sql = 'PRAGMA table_info({:})'.format(table)
        return self.execute(sql).fetchall()

    def _get_fields(self, table):
        """
        Return a list of fields for a table.

        :param table: Name of table to get primary fields for.
        :type table: ``str``
        """
        return [str(row[1]) for row in self._get_pragma(table)]
    
    def _build_field_dict(self):
        
        fields = {}
        for t in self.TABLES:
            fields[t] = self._get_fields(t)
        return fields
    TABLE_FIELDS = property(_build_field_dict)

    def _get_primary_fields(self, table):
        """
        Return a list of primary fields for a table.

        :param table: Name of table to get primary fields for.
        :type table: ``str``
        """
        primary_fields = []
        for row in self._get_pragma(table):
            if row[5] == 1:
                primary_fields.append(str(row[1]))
        logging.debug('found primary fields: ' + str(primary_fields))
        return primary_fields

    def _get_required_fields(self, table):
        """
        Return a list of fields that have NOT NULL set.

        :param table: Name of table to get required fields for.
        :type table: ``str``
        """
        required_fields = []
        for row in self._get_pragma(table):
            if row[3] == 1:
                required_fields.append(str(row[1]))
        logging.debug('found required fields: ' + str(required_fields))
        return required_fields

    def _insert(self, table, **kwargs):
        """
        Adds an entry to a table.

        :param table: Name of table to add data to.
        :type table: ``str``
        :param **kwargs: keyword=value arguments for fields in the ``events``
            table.
        """
        sql = 'INSERT INTO %s (%s)' \
              % (table, ', '.join([k for k in kwargs]))
        sql += ' VALUES (%s)' % ', '.join(['?' for k in kwargs])
        data = tuple([kwargs[k] for k in kwargs])
        self.execute(sql, data)

    def _delete(self, table, **kwargs):
        """
        Remove an entry from a table.

        :param table: Name of table to remove data from.
        :type table: ``str``
        :param **kwargs: keyword=value arguments for fields to match when
            choosing rows to remove.
        """
        sql = "DELETE FROM %s" % table
        sql += " WHERE " + ' and '.join(['{:}="{:}"'.format(k, kwargs[k])\
                                         for k in kwargs])
        logging.debug("calling: self.execute('%s')" % sql)
        self.execute(sql)

    def _update(self, table, **kwargs):
        """
        Update data in a table.

        :param table: Name of table to update data in.
        :type table: ``str``
        :param **kwargs: keyword=value arguments for fields in table.
        """
        pvalues = self._select_field_values(table, **kwargs)
        sql = 'UPDATE %s SET ' % table
        sql += ', '.join(['{:}="{:}"'.format(k, kwargs[k]) for k in kwargs])
        sql += ' WHERE '
        sql += ' and '.join(['{:}="{:}"'.format(k, pvalues[k])
                             for k in pvalues])
        logging.debug("calling: self.execute('%s')" % sql)
        self.execute(sql)

    def _insertupdate(self, table, **kwargs):
        """
        Update matching data if it exists, or add it if it does not exist.

        Existing data to replace are choosen by searching for rows with
        matching primary fields.

        :param table: Name of table to update data in.
        :type table: ``str``
        :param **kwargs: keyword=value arguments for fields in table.
        """
        pvalues = self._select_primary_field_values(table, **kwargs)
        count = self._count(table, **pvalues)
        logging.debug('found %s existing values', count)
        if self._count(table, **pvalues) > 0:
            logging.debug('updating existing...')
            # just update existing
            self._update(table, **kwargs)
        else:
            logging.debug('adding new...')
            # add a new row
            self._insert(table, **kwargs)

    def _count(self, table, **kwargs):
        """
        Get the number of rows in a table.

        :param table: Name of table to get count from.
        :type table: ``str``
        :param **kwargs: keyword=value arguments for fields in table.
        """
        sql = 'SELECT COUNT(*) FROM %s' % table
        if len(kwargs) > 0:
            values = ['{:}="{:}"'.format(k, kwargs[k]) for k in kwargs]
            sql += ' WHERE ' + ' and '.join(values)
        return self.execute(sql).fetchall()[0][0]



class TraveltimeDatabaseConnection(DatabaseConnection):
    """
    Class for managing a database of traveltimes.
    """
    def __init__(self, *args, **kwargs): 

        self.EPSG = kwargs.pop('epsg', DEFAULT_EPSG)
        rebuild = kwargs.pop('rebuild', False)
        DatabaseConnection.__init__(self, *args, **kwargs)

        self.setup(rebuild=rebuild)
        self.verify()

    def setup(self, rebuild=False):
        """
        Sets up default tables, views, and triggers for a new database.
        """
        if rebuild:
            msg = 'Rebuilding tables may result in data loss.\n'
            msg += 'Do you really want to rebuild tables? '
            rebuild = query_yes_no(msg)

        self._init_spatial_metadata()
        self._create_source_table(rebuild=rebuild)
        self._create_receiver_table(rebuild=rebuild)
        self._create_events_table(rebuild=rebuild)
        self._create_picks_table(rebuild=rebuild)
        self._create_rays_table(rebuild=rebuild)
        self._create_epsg_definitions(rebuild=rebuild)

    def _create_epsg_definitions(self, rebuild=False, view='epsg'):

        if rebuild:
            sql = 'DROP VIEW IF EXISTS {:}'.format(view)
            self.execute(sql)

        logging.info("(Re)creating view '{:}'".format(view))
        sql = 'CREATE VIEW {:} AS'.format(view)
        sql += ' SELECT srid, ref_sys_name as name, proj4text as proj_params'
        sql += ' FROM spatial_ref_sys'
        self.execute(sql)
        

    def _create_source_table(self, rebuild=False, table='source_pts'):

        if rebuild:
            sql = 'DROP TABLE IF EXISTS {:}'.format(table)
            self.execute(sql)
        elif table in self.TABLES:
            return

        # create main data fields
        logging.info("(Re)creating table '{:}'".format(table))
        sql = 'CREATE TABLE {:} ('.format(table)
        sql += """
                sid INTEGER NOT NULL,
	            PRIMARY KEY (sid));
               """
        self.execute(sql)

        # create XYZ geometry collumn
        sql = "SELECT AddGeometryColumn('{:}', 'geom',"\
                .format(table)
        sql += " {:}, 'POINT', 'XYZ')".format(self.EPSG)
        self.execute(sql)


    def _create_receiver_table(self, rebuild=False, table='receiver_pts'):

        if rebuild:
            sql = 'DROP TABLE IF EXISTS {:}'.format(table)
            self.execute(sql)
        elif table in self.TABLES:
            return

        # create main data fields
        logging.info("(Re)creating table '{:}'".format(table))
        sql = 'CREATE TABLE {:} ('.format(table)
        sql += """
                rid INTEGER NOT NULL,
	            PRIMARY KEY (rid));
               """
        self.execute(sql)

        # create XYZ geometry collumn
        sql = "SELECT AddGeometryColumn('{:}', 'geom',"\
                .format(table)
        sql += " {:}, 'POINT', 'XYZ')".format(self.EPSG)
        self.execute(sql)


    def _create_events_table(self, rebuild=False, table='events'):

        if rebuild:
            sql = 'DROP TABLE IF EXISTS {:}'.format(table)
            self.execute(sql)
        elif table in self.TABLES:
            return

        logging.info("(Re)creating table '{:}'".format(table))
        sql = 'CREATE TABLE {:} ('.format(table)
        sql += """
	            event TEXT NOT NULL,
                vmtomo_branch INTEGER,
          	    vmtomo_subbranch INTEGER,
	            PRIMARY KEY (event));
               """
        self.execute(sql)

    def _create_picks_table(self, rebuild=False, table='picks'):

        if rebuild:
            sql = 'DROP TABLE IF EXISTS {:}'.format(table)
            self.execute(sql)
        elif table in self.TABLES:
            return

        logging.info("(Re)creating table '{:}'".format(table))
        sql = 'CREATE TABLE {:} ('.format(table)
        sql += """
        	   event TEXT NOT NULL,
	           sid INTEGER NOT NULL,
	           rid INTEGER NOT NULL,
	           time FLOAT NOT NULL,
	           error FLOAT NOT NULL,
	           trace_in_file INTEGER,
	           data_file TEXT,
	           PRIMARY KEY (event, sid, rid),
	           FOREIGN KEY (sid) REFERENCES source_pts(sid),
	           FOREIGN KEY (rid) REFERENCES receiver_pts(rid),
	           FOREIGN KEY (event) REFERENCES events(event));
               """
        self.execute(sql)

    def _create_rays_table(self, rebuild=False, table='rays'):

        if rebuild:
            sql = 'DROP TABLE IF EXISTS {:}'.format(table)
            self.execute(sql)
        elif table in self.TABLES:
            return

        logging.info("(Re)creating table '{:}'".format(table))
        sql = 'CREATE TABLE {:} ('.format(table)
        sql += """
        	   event TEXT NOT NULL,
	           source_id INTEGER NOT NULL,
	           receiver_id INTEGER NOT NULL,
	           time FLOAT NOT NULL,
	           path BLOB NOT NULL,
	           PRIMARY KEY (event, source_id, receiver_id),
	           FOREIGN KEY (source_id, receiver_id)
                    REFERENCES receiver_ids(source_id, receiver_id),
	           FOREIGN KEY (event) REFERENCES events(event));
               """
        self.execute(sql)

    def verify(self):
        """
        Check that database has all of the required tables and data
        """
        self._verify_epsg()
        for table in ['events', 'picks', 'rays', 'receiver_pts',
                      'source_pts']:
            if table not in self.TABLES:
                raise IntegrityError("Table '{:}' does not exist."\
                                     .format(table))
            else:
                logging.info("Found required table '{:}'.".format(table))

    def _verify_epsg(self):
        """
        Checks that projection set by EPSG is in the projection table
        """
        sql = 'SELECT srid, name, proj_params FROM epsg WHERE srid={:}'\
                .format(self.EPSG)
        d = self.execute(sql).fetchall()
        if len(d) != 1:
            raise IntegrityError('SRID {:} not in EPSG table.'\
                                 .format(self.EPSG))
        else:
            _d = d[0]
            logging.info('Primary projection is set to: {:} {:} {:}'\
                         .format(_d[0], _d[1], _d[2]))


    def _sort_pick_data(self, **kwargs):

        tables = ['events', 'picks', 'receiver_pts', 'source_pts']

        data = {} 
        for table in tables:
            data[table] = {}

        # special handling of XY geometry fields
        epsg = kwargs.pop('epsg', self.EPSG)
        if all(k in kwargs for k in ['sx', 'sy', 'sz']):
            sx = kwargs.pop('sx')
            sy = kwargs.pop('sy')
            sz = kwargs.pop('sz')
            data['source_pts']['geom'] = sql_POINT_XYZ(sx, sy, sz, epsg) 
            
        if all(k in kwargs for k in ['rx', 'ry', 'rz']):
            rx = kwargs.pop('rx')
            ry = kwargs.pop('ry')
            rz = kwargs.pop('rz')
            data['receiver_pts']['geom'] = sql_POINT_XYZ(rx, ry, rz, epsg)

        fields = [k for k in kwargs]
        for field in fields:
            for table in tables:
                if field in self._get_fields(table):
                    data[table][field] = kwargs[field]

        if self._count('receiver_pts', rid=kwargs['rid']) == 1:
            data['receiver_pts'] = {}

        if self._count('source_pts', sid=kwargs['sid']) == 1:
            data['source_pts'] = {}


        logging.debug('Sorted pick data as: {:}'.format(data))
                    
        return data

    def insert_pick(self, **kwargs):
        """
        Inserts a new traveltime
        """
        insert_order = ['receiver_pts', 'source_pts', 'events', 'picks']

        data = self._sort_pick_data(**kwargs)
        for table in insert_order:
            if len(data[table]) > 0:
                sql = "INSERT INTO {:} (".format(table)
                sql += ', '.join([k for k in data[table]])
                sql += ") VALUES ("
                sql += ", ".join([pad(data[table][k]) for k in data[table]])
                sql += ')'
                self.execute(sql)
        self.commit()
    
    def update_pick(self, **kwargs): 
        """
        Updates an existing traveltime, or adds a new one.
        """
        raise NotImplementedError

    def delete_pick(self, **kwargs):
        """
        Removes an existing traveltime.
        """
        raise NotImplementedError

    def insert_geom_from_SEGY(self, segy, epsg=DEFAULT_EPSG):
        """
        Inserts source and receiver geometry from a SEGYFile
        """
        for tr in segy.traces:
            rid = tr.header.ensemble_number
            rx = tr.header.scaled_source_coordinate_x
            ry = tr.header.scaled_source_coordinate_y
            rz = tr.header.datum_elevation_at_receiver_group
            geom = format_point_sql(rx, ry, epsg)
        
            if self._count('receiver_pts', rid=rid) == 0:
                sql = 'INSERT INTO receiver_pts(rid, rz, geom)'
                sql += ' VALUES({:}, {:}, {:})'.format(rid, rz, geom)
                self.execute(sql)

            sid = tr.header.trace_number_within_the_ensemble
            sx = tr.header.scaled_source_coordinate_x
            sy = tr.header.scaled_source_coordinate_y
            sz = tr.header.scaled_datum_elevation_at_source
            geom = format_point_sql(sx, sy, epsg)

            if self._count('source_pts', sid=sid) == 0:
                sql = 'INSERT INTO source_pts(sid, sz, geom)'
                sql += ' VALUES({:}, {:}, {:})'.format(sid, sz, geom)
                self.execute(sql)

            logging.info('ensemble=rid: {:}, trace=sid: {:}'\
                         .format(rid, sid))

        self.commit()

    def create_2d_line(self, sol, eol=None, epsg=DEFAULT_EPSG, filter=None):
        """
        Creates a new 2D line to project receiver_ids onto.
        """
        raise NotImplementedError
