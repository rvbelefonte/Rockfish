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

traces
------

Table of source and receiver locations for each trace.

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
import sqlite3

DEFAULT_EPSG = 4326

EPSG_SETUP_SQL = os.path.join(os.path.dirname(__file__), 'epsg-sqlite.sql')
DEFAULT_SETUP_SQL = os.path.join(os.path.dirname(__file__), 'default_setup.sql')

# XXX dev
logging.basicConfig(level='INFO')

class IntegrityError(sqlite3.IntegrityError):
    """
    Raised when database lacks required tables or data.
    """
    pass

class DatabaseConnection(sqlite3.Connection):
    """
    Base class for interacting with databases
    """
    def __init__(self, *args, **kwargs): 
        database = kwargs.pop('database', ':memory:')
        if database == ':memory:':
            logging.warn('Creating new database in memory.')
        elif os.path.isfile(database):
            logging.info('Connecting to existing database: {:}'.format(database))
        else:
            logging.info('Creating new database: {:}'.format(database))
        sqlite3.Connection.__init__(self, database, *args, **kwargs)

    def executefile(self, sqlfile):
        """
        Read a sqlite script and execute it.
        """
        with open(sqlfile, 'r') as f:
            sql = f.read()
        self.executescript(sql)

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



class TraveltimeDatabaseConnection(DatabaseConnection):
    """
    Class for managing a database of traveltimes.
    """
    def __init__(self, *args, **kwargs): 

        self.EPSG = kwargs.pop('epsg', DEFAULT_EPSG)
        DatabaseConnection.__init__(self, *args, **kwargs)

        self.setup()
        self.verify()

    def setup(self):
        """
        Sets up default tables, views, and triggers for a new database.
        """
        if 'epsg' not in self.TABLES:
            logging.info("Setting up new projection table 'epsg'.")
            self.executefile(EPSG_SETUP_SQL)
        else:
            logging.info("Using existing projection table 'epsg' table.")

        self.executefile(DEFAULT_SETUP_SQL)

    def verify(self):
        """
        Check that database has all of the required tables and data
        """
        self._verify_epsg()

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





    # XXX Function prototypes
    def insert(self, **kwargs):
        """
        Inserts a new traveltime
        """
        pass
    
    def update(self, **kwargs): 
        """
        Updates an existing traveltime, or adds a new one.
        """
        pass

    def remove(self, **kwargs):
        """
        Removes an existing traveltime.
        """
        pass

    def create_2d_line(self, sol, eol=None, epsg=DEFAULT_EPSG, filter=None):
        """
        Creates a new 2D line to project traces onto.
        """
        pass
