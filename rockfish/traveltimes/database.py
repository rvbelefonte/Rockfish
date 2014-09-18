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
from rockfish.database.utils import format_search, format_row_factory
from rockfish.segy.segy import readSEGY 

DEFAULT_EPSG = 4326

EPSG_SETUP_SQL = os.path.join(os.path.dirname(__file__), 'epsg-sqlite.sql')

# XXX dev
#logging.basicConfig(level='DEBUG')


sql_POINT_XYZ = lambda x, y, z, epsg:\
        "GeomFromText('POINTZ({:} {:} {:})', {:})".format(x, y, z, epsg)

sql_POINT_XY = lambda x, y, epsg:\
        "GeomFromText('POINT({:} {:})', {:})".format(x, y, epsg)

sql_LINESTRING_XZ = lambda pts, epsg: "GeomFromText('LINESTRING({:})', {:})"\
        .format(', '.join(['{:} {:}'.format(p[0], p[1]) for p in pts]),
                epsg)

def pad(value):

    if str(value).startswith('GeomFromText'):
        return value
    elif type(value) in [unicode, str]:
        return "'{:}'".format(value)
    elif value == None:
        return "NULL"
    else:
        return '{:}'.format(value)


class DatabaseConnection(SQLiteConnection):
    """
    Base class for interacting with databases
    """
    def __init__(self, database, *args, **kwargs): 
        if database == ':memory:':
            logging.warn('Creating new database in memory.')
        elif os.path.isfile(database):
            logging.info('Connecting to existing database: {:}'\
                         .format(database))
        else:
            logging.info('Creating new database: {:}'.format(database))
        SQLiteConnection.__init__(self, database, *args, **kwargs)

    def _init_spatial_metadata(self):

        if 'spatial_ref_sys' not in self.TABLES:
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
    def __init__(self, database, *args, **kwargs): 

        self.EPSG = kwargs.pop('epsg', DEFAULT_EPSG)
        rebuild = kwargs.pop('rebuild', False)
        DatabaseConnection.__init__(self, database, *args, **kwargs)

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
        self._create_dummy_picks_table(rebuild=rebuild)
        self._create_rays_table(rebuild=rebuild)
        self._create_model_lines_table(rebuild=rebuild)
        self._create_model_lines_view(rebuild=rebuild)
        self._create_vminst_view(rebuild=rebuild)
        self._create_vmshots_view(rebuild=rebuild)
        self._create_vmpicks_view(rebuild=rebuild)
        self._create_vmdummypicks_view(rebuild=rebuild)

    def _create_epsg_definitions(self, rebuild=False, view='epsg'):

        if rebuild:
            sql = 'DROP VIEW IF EXISTS {:}'.format(view)
            self.execute(sql)
        else:
            return

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
                branch INTEGER,
          	    subbranch INTEGER,
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
               model_line TEXT,
	           trace_in_file INTEGER,
	           data_file TEXT,
	           PRIMARY KEY (event, sid, rid),
               FOREIGN KEY (model_line) REFERENCES model_lines(name),
	           FOREIGN KEY (sid) REFERENCES source_pts(sid),
	           FOREIGN KEY (rid) REFERENCES receiver_pts(rid),
	           FOREIGN KEY (event) REFERENCES events(event));
               """
        self.execute(sql)

    def _create_dummy_picks_table(self, rebuild=False, table='dummy_picks'):

        if rebuild:
            sql = 'DROP TABLE IF EXISTS {:}'.format(table)
            self.execute(sql)
        elif table in self.TABLES:
            return

        logging.info("(Re)creating table '{:}'".format(table))
        sql = 'CREATE TABLE {:} ('.format(table)
        sql += """
	           sid INTEGER NOT NULL,
	           rid INTEGER NOT NULL,
               model_line TEXT,
	           trace_in_file INTEGER,
	           data_file TEXT,
	           PRIMARY KEY (sid, rid, data_file),
               FOREIGN KEY (model_line) REFERENCES model_lines(name),
	           FOREIGN KEY (sid) REFERENCES source_pts(sid),
	           FOREIGN KEY (rid) REFERENCES receiver_pts(rid));
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
	           sid INTEGER NOT NULL,
	           rid INTEGER NOT NULL,
	           time FLOAT NOT NULL,
	           path BLOB NOT NULL,
               model_line TEXT,
               vm_model TEXT,
	           PRIMARY KEY (event, sid, rid, vm_model),
               FOREIGN KEY (model_line) REFERENCES model_lines(name),
	           FOREIGN KEY (rid) REFERENCES receiver_pts(rid)
	           FOREIGN KEY (sid) REFERENCES source_pts(sid)
	           FOREIGN KEY (event) REFERENCES events(event));
               """
        self.execute(sql)

    def _create_model_lines_table(self, rebuild=False, table='model_lines'):

        if rebuild:
            sql = 'DROP TABLE IF EXISTS {:}'.format(table)
            self.execute(sql)
        elif table in self.TABLES:
            return

        logging.info("(Re)creating table '{:}'".format(table))
        sql = 'CREATE TABLE {:} ('.format(table)
        sql += """
        	   name TEXT NOT NULL,
               vminst_view TEXT NOT NULL,
               vmshots_view TEXT NOT NULL,
               vmpicks_view TEXT NOT NULL,
               vmdummypicks_view TEXT NOT NULL,
               PRIMARY KEY (name)
               )
               """
        self.execute(sql)

        sql = "SELECT AddGeometryColumn('{:}', 'geom',"\
                .format(table)
        sql += " {:}, 'LINESTRING', 'XY')".format(self.EPSG)
        self.execute(sql)

    def _create_model_lines_view(self, rebuild=False,
                                 view='model_line_endpts'):

        if rebuild:
            sql = 'DROP VIEW IF EXISTS {:}'.format(view)
            self.execute(sql)
        elif view in self.VIEWS:
            return

        logging.info("(Re)creating view '{:}'".format(view))
        sql = 'CREATE VIEW {:}'.format(view)
        sql += ' AS SELECT name, StartPoint(geom) as sol'
        sql += ', EndPoint(geom) as eol, GLength(geom) as length'
        sql += ' FROM model_lines'
        self.execute(sql)
        self.commit()

    def _create_vminst_view(self, rebuild=False, view='vminst'):

        if rebuild:
            sql = 'DROP VIEW IF EXISTS {:}'.format(view)
            self.execute(sql)
        if view in self.VIEWS:
            return

        sql = 'CREATE VIEW {:}'.format(view)
        sql += ' AS SELECT rid, X(geom)/1000. AS rx, Y(geom)/1000. AS ry,'
        sql += ' -Z(geom)/1000. AS rz'
        sql += ' FROM receiver_pts'
        self.execute(sql)
        self.commit()

    def _create_vmshots_view(self, rebuild=False, view='vmshots'):

        if rebuild:
            sql = 'DROP VIEW IF EXISTS {:}'.format(view)
            self.execute(sql)
        if view in self.VIEWS:
            return

        sql = 'CREATE VIEW {:}'.format(view)
        sql += ' AS SELECT sid, X(geom)/1000. AS sx, Y(geom)/1000. AS sy,'
        sql += ' -Z(geom)/1000. AS sz'
        sql += ' FROM source_pts'
        self.execute(sql)
        self.commit()

    def _create_vmpicks_view(self, rebuild=False, view='vmpicks'):

        if rebuild:
            sql = 'DROP VIEW IF EXISTS {:}'.format(view)
            self.execute(sql)
        if view in self.VIEWS:
            return

        sql = 'CREATE VIEW {:}'.format(view)
        sql += ' AS SELECT p.rid as rid, p.sid as sid,'
        sql += ' e.branch as branch, e.subbranch as subbranch,'
        sql += ' Distance(r.geom, s.geom)/1000. as offset,'
        sql += ' p.time as time, p.error as error'
        sql += ' FROM events as e, picks as p'
        sql += ' INNER JOIN receiver_pts as r ON p.rid=r.rid'
        sql += ' INNER JOIN source_pts as s ON p.sid=s.sid'
        sql += ' ORDER BY data_file, trace_in_file, branch, subbranch'
        self.execute(sql)
        self.commit()

    def _create_vmdummypicks_view(self, rebuild=False, view='vmdummypicks'):

        if rebuild:
            sql = 'DROP VIEW IF EXISTS {:}'.format(view)
            self.execute(sql)
        if view in self.VIEWS:
            return

        sql = 'CREATE VIEW {:}'.format(view)
        sql += ' AS SELECT p.rid as rid, p.sid as sid,'
        sql += ' e.branch as branch, e.subbranch as subbranch,'
        sql += ' Distance(r.geom, s.geom)/1000. as offset,'
        sql += ' 0.0 as time, 0.0 as error, event, trace_in_file, data_file'
        sql += ' FROM events as e, dummy_picks as p'
        sql += ' INNER JOIN receiver_pts as r ON p.rid=r.rid'
        sql += ' INNER JOIN source_pts as s ON p.sid=s.sid'
        sql += ' ORDER BY data_file, trace_in_file, branch, subbranch'
        self.execute(sql)
        self.commit()



    def verify(self):
        """
        Check that database has all of the required tables and data
        """
        #XXXself._verify_epsg()
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

    def _check_count(self, table, min_count=1, **kwargs):
        """
        Verify that a table has a minimum number of rows
        """
        n = self._count(table, **kwargs)

        if n < min_count:
            msg = "Less than {:} rows".format(n)
            if len(kwargs) > 0:
                msg += ' matching {:}'.format(kwargs)
            
            msg += " in table '{:}'".format(table)

            raise IntegrityError(msg)

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

    def insert_geom_from_SEGY(self, segy, model_line=None,
                              rid_field='ensemble_number',
                              sid_field='trace_number_within_the_ensemble',
                              **kwargs):
        """
        Inserts source and receiver geometry from a SEGYFile
        """
        epsg = kwargs.pop('epsg', self.EPSG)
        for i, tr in enumerate(segy.traces):
            rid = tr.header.__getattribute__(rid_field)
            rx = tr.header.scaled_group_coordinate_x
            ry = tr.header.scaled_group_coordinate_y
            rz = tr.header.scaled_receiver_group_elevation 
            geom = sql_POINT_XYZ(rx, ry, rz, epsg)
        
            if self._count('receiver_pts', rid=rid) == 0:
                sql = 'INSERT INTO receiver_pts(rid, geom)'
                sql += ' VALUES({:}, {:})'.format(rid, geom)
                self.execute(sql)

            sid = tr.header.__getattribute__(sid_field)
            sx = tr.header.scaled_source_coordinate_x
            sy = tr.header.scaled_source_coordinate_y
            sz = -tr.header.scaled_source_depth_below_surface
            geom = sql_POINT_XYZ(sx, sy, sz, epsg)

            if self._count('source_pts', sid=sid) == 0:
                sql = 'INSERT INTO source_pts(sid, geom)'
                sql += ' VALUES({:}, {:})'.format(sid, geom)
                self.execute(sql)
           
            data_file = os.path.basename(segy.file.name)
            if self._count('dummy_picks', rid=rid, sid=sid,
                           data_file=data_file) == 0:
                sql = 'INSERT INTO dummy_picks'
                sql += '(sid, rid, model_line, trace_in_file, data_file)'
                sql += " VALUES({:}, {:}, '{:}', {:}, '{:}')"\
                        .format(sid, rid, model_line, i, data_file)
                self.execute(sql)

            logging.info('ensemble=rid: {:}, trace=sid: {:}'\
                         .format(rid, sid))

        self.commit()

    def insert_odt_picks(self, event, odtfile, line2segyfile, model_line=None,
                         vred=None, error=0.0,
                         rid_field='ensemble_number',
                         sid_field='trace_number_within_the_ensemble',
                         verify=False, load_segy_geom=True, **kwargs):
        """
        Insert picks from OpendTect
        """
        epsg = kwargs.pop('epsg', self.EPSG)
        segyfile0 = None
        f = open(odtfile, 'rb')
        for line in f:

            d = line.split()
            
            odt_line = d[0]
            sx = float(d[1])
            dy = float(d[2])
            trace_in_file = int(d[3])
            time_reduced = float(d[4])

            segyfile = line2segyfile(odt_line)
            data_file = os.path.basename(segyfile)

            if segyfile != segyfile0:
                segy = readSEGY(segyfile, unpack_headers=True)
                sql = 'DELETE FROM PICKS WHERE'
                sql += " data_file = '{:}' AND event='{:}'"\
                        .format(data_file, event)
                self.execute(sql)
                
                if load_segy_geom and\
                   (self._count('dummy_picks',
                               data_file=os.path.basename(segyfile)) == 0):
                    print 'Loading geometry from: {:}'.format(segyfile)
                    self.insert_geom_from_SEGY(segy, epsg=epsg,
                        model_line=model_line, rid_field=rid_field,
                        sid_field=sid_field)
            segyfile0 = segyfile

            try:
                tr = segy.traces[trace_in_file - 1]
            except IndexError:
                raise IndexError('Trace number {:} out of range for file {:}.'\
                                 .format(trace_in_file, segyfile))
                

            offset = abs(tr.header.computed_source_receiver_offset_in_m)
            rid = tr.header.__getattribute__(rid_field)
            sid = tr.header.__getattribute__(sid_field)

            if vred is not None:
                time = time_reduced + offset / 1000. / vred
            else:
                time = time_reduced

            if verify:
                self._check_count('receiver_pts', rid=rid)
                self._check_count('source_pts', sid=sid)

            dat = [pad(event), sid, rid, time, error, pad(model_line),
                   trace_in_file, pad(data_file)]

            sql = 'INSERT INTO picks(event, sid, rid, time, error,'
            sql += ' model_line, trace_in_file, data_file)'
            sql += ' VALUES(' + ', '.join([str(v) for v in dat]) + ')'


           
            print sql
            self.execute(sql)

        self.commit()


    def insert_rayfan(self, rays, model_line=None, vm_model=None):

        if vm_model is not None:
            sql = "DELETE FROM rays WHERE vm_model='{:}'"\
                    .format(vm_model)

        for rfn in rays.rayfans:

            rid = rfn.start_point_id

            for i in range(rfn.nrays):
                sid = rfn.end_point_ids[i]

                branch = rfn.event_ids[i]
                subbranch = rfn.event_subids[i]

                sql = 'SELECT event FROM events WHERE'
                sql += ' branch={:} AND subbranch={:}'\
                        .format(branch, subbranch)
                event = self.execute(sql).fetchone()[0]

                time = rfn.travel_times[i]
                path = rfn.paths[i]

                sql = 'INSERT INTO rays'
                sql += '(event, sid, rid, time, path, model_line, vm_model)'
                sql += " VALUES('{:}', {:}, {:}, {:}, '{:}', '{:}', '{:}')"\
                        .format(event, sid, rid, time, path, model_line,
                                vm_model)
                self.execute(sql)

        self.commit()

    def create_2d_model_line(self, name, pts, epsg=DEFAULT_EPSG):
        """
        Creates a new 2D line to project source, receiver points onto.
        """
        geom = sql_LINESTRING_XZ(pts, epsg)

        vminst = '{:}_vminst'.format(name)
        vmshots = '{:}_vmshots'.format(name)
        vmpicks = '{:}_vmpicks'.format(name)
        vmdummy = '{:}_vmdummypicks'.format(name)

        sql = 'INSERT INTO model_lines (name, geom, vminst_view,'
        sql += 'vmshots_view, vmpicks_view, vmdummypicks_view)'
        sql += "VALUES('{:}', {:}, '{:}', '{:}', '{:}', '{:}')"\
                .format(name, geom, vminst, vmshots, vmpicks, vmdummy)
        self.execute(sql)

        self.commit()

        # VM Tomography views
        # Receiver locations
        sql = 'DROP VIEW IF EXISTS {:}'.format(vminst)
        self.execute(sql)
        sql = 'CREATE VIEW {:}'.format(vminst)
        sql += ' AS SELECT r.rid AS rid,'
        sql += ' Distance(r.geom, StartPoint(m.geom))/1000.'
        sql += ' AS rx, 0.0 AS ry, -Z(r.geom)/1000. AS rz'
        sql += ' FROM receiver_pts AS r,'
        sql += " model_lines AS m WHERE m.name='{:}'".format(name)
        self.execute(sql)
        # Shot locations
        sql = 'DROP VIEW IF EXISTS {:}'.format(vmshots)
        self.execute(sql)
        sql = 'CREATE VIEW {:}'.format(vmshots)
        sql += ' AS SELECT s.sid AS sid,'
        sql += ' Distance(s.geom, StartPoint(m.geom))/1000.'
        sql += ' AS sx, 0.0 AS sy, -Z(s.geom)/1000. AS sz FROM source_pts AS s,'
        sql += " model_lines AS m WHERE m.name='{:}'".format(name)
        self.execute(sql)
        # Traveltime picks
        sql = 'DROP VIEW IF EXISTS {:}'.format(vmpicks)
        self.execute(sql)
        sql = 'CREATE VIEW {:}'.format(vmpicks)
        sql += ' AS SELECT p.rid as rid, p.sid as sid,'
        sql += ' e.branch as branch, e.subbranch as subbranch,'
        sql += ' Distance(r.geom, s.geom)/1000. as offset,'
        sql += ' p.time as time, p.error as error'
        sql += ' FROM events as e, picks as p'
        sql += ' INNER JOIN receiver_pts as r ON p.rid=r.rid'
        sql += ' INNER JOIN source_pts as s ON p.sid=s.sid'
        sql += " WHERE p.model_line='{:}'".format(name)
        self.execute(sql)
        # Dummy picks for synthetics
        sql = 'DROP VIEW IF EXISTS {:}'.format(vmdummy)
        self.execute(sql)
        sql = 'CREATE VIEW {:}'.format(vmdummy)
        sql += ' AS SELECT p.rid as rid, p.sid as sid,'
        sql += ' e.branch as branch, e.subbranch as subbranch,'
        sql += ' Distance(r.geom, s.geom)/1000. as offset,'
        sql += ' 0.0 as time, 0.0 as error, event, trace_in_file, data_file'
        sql += ' FROM events as e, dummy_picks as p'
        sql += ' INNER JOIN receiver_pts as r ON p.rid=r.rid'
        sql += ' INNER JOIN source_pts as s ON p.sid=s.sid'
        sql += " WHERE p.model_line='{:}'".format(name)
        self.execute(sql)

    def _get_model_vmview(self, vtype, model=None):
        """
        Get a view name for a specific model
        """
        if model is None:
            view = 'vm{:}'.format(vtype)
        else:
            sql = 'SELECT vm{:}_view FROM model_lines WHERE'.format(vtype)
            sql += " name='{:}'".format(model)

            view = self.execute(sql).fetchone()[0]
        
            assert view is not None,\
                    "Failed to find model '{:}' in table 'model_lines'"\
                    .format(model)
        return view

    def _get_vmtomo_input(self, step=1, model=None, dummy=False, **kwargs):

        if dummy:
            vtype = 'dummypicks'
        else:
            vtype = 'picks'
        picksview = self._get_model_vmview(vtype, model=model)
        instview = self._get_model_vmview('inst', model=model)
        shotsview = self._get_model_vmview('shots', model=model)

        # make master join
        masterview = '_vmmaster'
        sql = 'DROP VIEW IF EXISTS {:}'.format(masterview)
        self.execute(sql)
        sql = 'CREATE TEMPORARY VIEW {:}'.format(masterview)
        sql += ' AS SELECT * FROM '
        sql += ' {:} AS p INNER JOIN {:} AS s ON p.sid=s.sid'\
                .format(picksview, shotsview)
        sql += ' INNER JOIN {:} AS r ON p.rid=r.rid'.format(instview)
        if len(kwargs) > 0:
            sql += ' WHERE ' + format_search(kwargs)
        print sql
        self.execute(sql)

        # Traveltimes
        sql = 'SELECT rid, sid, branch, subbranch, offset, time, error'
        sql += ' FROM {:}'.format(masterview)
        sql += ' ORDER BY rid, sid'
        picks = format_row_factory(self.execute(sql), none_value=0.0,
                                   step=step)

        # Receiver locations
        sql = 'SELECT DISTINCT rid, rx, ry, rz FROM {:}'\
                .format(masterview)
        sql += ' ORDER BY rid'
        inst = format_row_factory(self.execute(sql), none_value=0.0, step=1)

        # Source locations
        sql = 'SELECT DISTINCT sid, sx, sy, sz FROM {:}'\
                .format(masterview)
        sql += ' ORDER BY sid'
        shots = format_row_factory(self.execute(sql), none_value=0.0, step=1)

        return inst, shots, picks

    def write_vmtomo(self, instfile='inst.dat', pickfile='picks.dat',
                     shotfile='shots.dat', directory='.', step=1, model=None,
                     dummy=False, **kwargs):
        """
        Write pick data to VM Tomography format input files.

        Parameters
        ----------
        instfile: str
            Name of file to write instrument data to.
        pickfile: str
            Name of file to write pick data to.
        shotfile: str
            Name of file to write shot data to.
        directory: str
            Name of path to prepend to filenames.
        step: int
            Specifies the increment of picks to write out.
        model: str
            Name of a model line in the 'model_lines' table to project project
            source and receiver locations onto.
        dummy: bool
            If True, writes out dummy picks for all source, receiver, event
            tuples. Useful for calculating synthetic traveltimes.
        **kwargs: 
            Optional keyword=value arguments for fields in the
            picks table. Default is to write all picks.
        """
        inst, shots, picks = self._get_vmtomo_input(step=step, model=model,
                                                    dummy=dummy, **kwargs)

        if directory is not None:
            instfile = os.path.join(directory, instfile)
            pickfile= os.path.join(directory, pickfile)
            shotfile = os.path.join(directory, shotfile)

        f = open(instfile, 'w')
        f.write(inst)
        f.close()
        
        f = open(pickfile, 'w')
        f.write(picks)
        f.close()
        
        f = open(shotfile, 'w')
        f.write(shots)
        f.close()

    def write_odt_picks(self, odt_file, data_file, event, odt_line=None,
                        vred=None):

        f = open(odt_file, 'w')
        f.write('#line     x     y     trace     time\n')

        if odt_line is None:
            odt_line == data_file

        if vred is None:
            time_sql = 'time*1000.'
        else:
            time_sql = 'time*1000. - Distance(r.geom, s.geom)/{:}'.format(vred)
        
        sql = 'SELECT X(s.geom), Y(s.geom), trace_in_file, {:} FROM'\
                .format(time_sql)
        sql += ' rays AS p INNER JOIN receiver_pts AS r ON p.rid=r.rid'
        sql += ' INNER JOIN source_pts AS s ON p.sid=s.sid'
        sql += ' INNER JOIN dummy_picks AS g ON (p.rid=g.rid AND p.sid=g.sid)'
        sql += " WHERE event='{:}'".format(event)
        sql += " AND data_file='{:}'".format(data_file)
        sql += ' ORDER BY trace_in_file'

        for row in self.execute(sql):
            f.write('{:} {:} {:} {:} {:}\n'.format(odt_line, *row))

        f.close()
