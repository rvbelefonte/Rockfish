"""
Database support for picking of events in seismic data.

Creating a Pick Database
========================

To create a new database on the disk, or reconnect to an existing database:

>>> from rockfish.dev.picking2.picksegy import PickDatabaseConnection
>>> pickdb = PickDatabaseConnection('/path/to/database.sqlite') # doctest: +SKIP

This initiates a :class:`sqlite3.Connection` with an active connection and
cursor in the database file.  If the `Default Tables`_ do not already exist
in the database, they are created.

.. warning:: Existing database tables are not altered.  If an existing table
    does not have the required fields, methods such as
    :meth:`PickDatabaseConnection.Connection.add_pick` may raise exceptions.

A database can also be created in memory if the database only needs to exist
temporarily:

>>> pickdb = PickDatabaseConnection(':memory:')

Default Tables
==============

By default, a new database includes the following tables:

========== ===========  ===================================================
Table      Name         Description
========== ===========  ===================================================
`Picks`_   ``picks``    Main data table for storing pick times and errors.
`Events`_  ``events``   Stores information about unique events.
`Traces`_  ``traces``   Stores information about unique data traces.
========== ===========  ===================================================

Picks
-----

Picks are stored in the table ``picks``. New picks must have values provided 
for the following fields:

=================  ========= ===============================================
Field Name         SQL Type  Description 
=================  ========= ===============================================
event*             text      Name of event.
ensemble*          integer   Ensemble number (i.e., shot no., CMP no.)
trace*             integer   Trace number in ensemble (i.e., channel no.)
time               real      Pick time in seconds. Should be absolute,
                             and any reduction, delay time, etc. should have
                             been removed.
=================  ========= ===============================================

*These fields are used as primary keys in the database table and are thus
required.

Other non-required fields are: 

================= =========  ====================== =====================
Field Name        SQL Type   Description            Default Value
================= =========  ====================== =====================
time_reduced      real       Reduced pick time in   None
                             seconds.
error             real       Pick error in seconds. ``0.0``
timestamp         timestamp  Time pick was entered  ``CURRENT_TIMESTAMP``
                             or updated.
method            text       Method used to make    ``'unknown'``
                             the pick.
data_file         text       Data file the pick was None
                             made on.
================= =========  ====================== =====================

Other custom fields may be added to the database, but names should be 
different from those in the tables above.  To add a custom field, 
initiate the database with, for example:

>>> other_fields = [#(fieldname, sql_type, default or None, is primary)
>>>                  ('myfield1', 'TEXT', 'default_value1', False),
>>>                  ('myfield2', 'TEXT', 'default_value2', False)]
>>> pickdb = PickDatabaseConnection(':memory:',extra_pick_fields=other_fields)

Events
------

The :class:`PickDatabaseConnection` also maintains a table called
``events`` for storing information about each unique pick event name. This 
table includes the following required fields:

================= ========= ===============================================
Field Name        SQL Type  Description 
================= ========= ===============================================
event*             text     Name of event.
================= ========= ===============================================

*This field is a primary key and can be used to join the ``events`` table 
with the ``picks`` table.

By default, the ``events`` table also includes the following non-required
fields:

================= =========  ====================== =====================
Field Name        SQL Type   Description            Default Value
================= =========  ====================== =====================
plot_symbol       text       :mod:`matplotlib` plot '.r'
                             symbol string.
================= =========  ====================== =====================

Traces
------

The :class:`PickDatabaseConnection` also maintains a table called
``traces`` for storing information about each unique trace that picks were
made on.  This table includes the following required fields:

================  ========= ================================================
Field Name        SQL Type  Description 
================  ========= ================================================
ensemble*         integer   Ensemble number (i.e., shot no., CMP no.)
trace*            integer   Trace number in ensemble (i.e., channel no.)
source_x          real      Easting (e.g., longitude) of the source.
source_x          real      Northing (e.g., latitude) of the source.
source_z          real      Depth of source below sealevel.
receiver_x        real      Easting (e.g., longitude) of the receiver group.
receiver_y        real      Northing (e.g., latitude) of the receiver group.
receiver_z        real      Depth of receiver below sealevel.
================  ========= ================================================

*These fields are primary keys and can be used to join the ``traces`` table 
with the ``picks`` table.

By default, the ``traces`` table also includes the following non-required
fields:

================= =========  ====================== =====================
Field Name        SQL Type   Description            Default Value
================= =========  ====================== =====================
offset            real       Distance from the      None
                             center of the source 
                             to the center of the
                             receiver group.
faz               real       Forward azimuth (from  None
                             the source to the 
                             receiver).
line              text       2D line name for pick  None
site              text       Instrument site name   None
================= =========  ====================== =====================


"""
import logging
import matplotlib.pyplot as plt
from rockfish.database.database import RockfishDatabaseConnection
from rockfish.database.utils import format_row_factory, format_search

# Default tables and fields
PICK_TABLE = 'picks'
PICK_FIELDS = [
          #(name, sql_type, default_value, is_not_null, is_primary)
          ('event', 'TEXT', None, True, True),
          ('ensemble', 'INTEGER', None, True, True),
          ('trace', 'INTEGER', None, True, True),
          ('time', 'REAL', None, True, False),
          ('time_reduced', 'REAL', None, True, False),
          ('error', 'REAL', 0.0, True, False),
          ('timestamp', 'TIMESTAMP', 'CURRENT_TIMESTAMP', True, False),
          ('method', 'TEXT', 'unknown', False, False),
          ('data_file', 'TEXT', 'unknown', False, False)]

EVENT_TABLE = 'events'
EVENT_FIELDS = [
          #(name, sql_type, default_value, is_not_null, is_primary)
          ('event', 'TEXT', None, True, True),
          ('vm_branch', 'INTEGER', None, False, False),
          ('vm_subid', 'INTEGER', None, 0, False),
          ('plot_symbol', 'TEXT', '".r"', True, False)]

TRACE_TABLE = 'traces'
TRACE_FIELDS = [
          #(name, sql_type, default_value, is_not_null, is_primary)
          ('ensemble', 'INTEGER', None, True, True),
          ('trace', 'INTEGER', None, True, True),
          ('source_x', 'REAL', None, True, False),
          ('source_y', 'REAL', None, True, False),
          ('source_z', 'REAL', None, True, False),
          ('receiver_x', 'REAL', None, True, False),
          ('receiver_y', 'REAL', None, True, False),
          ('receiver_z', 'REAL', None, True, False),
          ('offset', 'REAL', None, False, False),
          ('faz', 'REAL', None, False, False),
          ('line', 'TEXT', None, False, False),
          ('site', 'TEXT', None, False, False)]

# Default view table names
MASTER_VIEW = 'main.all_picks'

# Views for creating VM Tomography input files
VMTOMO_PICK_VIEW = 'main.vmtomo_picks'
VMTOMO_PICK_FIELDS = ['ensemble', # instrument number
                      'trace',    # shot number
                      'vm_branch',# branch
                      'vm_subid', # sub ID
                      'offset',   # range
                      'time',     # time
                      'error']    # pick_error
VMTOMO_SHOT_VIEW = 'main.vmtomo_shots'
VMTOMO_SHOT_FIELDS = ['trace', # shot number
                      'source_x', # x-pos
                      'source_y', # y-pos
                      'source_z'] # z-pos
VMTOMO_INSTRUMENT_VIEW = 'main.vmtomo_instruments'
VMTOMO_INSTRUMENT_FIELDS = ['ensemble', # instrument number
                            'receiver_x', # x-pos
                            'receiver_y', # y-pos
                            'receiver_z'] # z-pos

class PickDatabaseConnectionError(Exception):
    """
    Base PickDatabaseConnection error.
    """
    pass


class PickDatabaseConnection(RockfishDatabaseConnection):
    """
    Class for working with a database of SEG-Y travel-time picks.

    Connects to a SQLite database in memory (default) or on the disk.  This
    class inherits from :class:`sqlite3.Connection`.
    """
    def __init__(self, database, *args, **kwargs):
        RockfishDatabaseConnection.__init__(self, database, *args, **kwargs)
        # build tables 
        self.PICK_TABLE = PICK_TABLE
        self.PICK_FIELDS = PICK_FIELDS
        self.create_pick_table(extra_fields=None)
        self.EVENT_TABLE = EVENT_TABLE
        self.EVENT_FIELDS = EVENT_FIELDS
        self.create_event_table(extra_fields=None)
        self.TRACE_TABLE = TRACE_TABLE
        self.TRACE_FIELDS = TRACE_FIELDS
        self.create_trace_table(extra_fields=None)
        # create views
        self.MASTER_VIEW = MASTER_VIEW
        self.VMTOMO_PICK_VIEW = VMTOMO_PICK_VIEW
        self.VMTOMO_PICK_FIELDS = VMTOMO_PICK_FIELDS
        self.VMTOMO_SHOT_VIEW = VMTOMO_SHOT_VIEW
        self.VMTOMO_SHOT_FIELDS = VMTOMO_SHOT_FIELDS
        self.VMTOMO_INSTRUMENT_VIEW = VMTOMO_INSTRUMENT_VIEW
        self.VMTOMO_INSTRUMENT_FIELDS = VMTOMO_INSTRUMENT_FIELDS
        self.create_views()
        
    def create_pick_table(self, extra_fields=None):
        """
        Creates the pick table if it does not already exist.

        :param extra_fields: Additional fields to include in the pick table.
            Should be a list of (name, sql type, default value, is primary) 
            tuples.
        :type extra_fields: ``[(``str``, ``str``, ``str`` or ``None``,
            ``Bool``)]``
        """
        if extra_fields is not None:
            # update the pick field list with extra fields
            self.PICK_FIELDS.extend(extra_fields)
        self._create_table_if_not_exists(self.PICK_TABLE,self.PICK_FIELDS)

    def create_event_table(self, extra_fields=None):
        """
        Creates the event event table if it does not already exist.

        :param extra_fields: Additional fields to include in the pick table.
            Should be a list of (name, sql type, default value, is primary) 
            tuples.
        :type extra_fields: ``[(``str``, ``str``, ``str`` or ``None``,
            ``Bool``)]``
        """
        if extra_fields is not None:
            # update the pick field list with extra fields
            self.EVENT_FIELDS.extend(extra_fields)
        self._create_table_if_not_exists(self.EVENT_TABLE,self.EVENT_FIELDS)

    def create_trace_table(self, extra_fields=None):
        """
        Creates the event event table if it does not already exist.

        :param extra_fields: Additional fields to include in the pick table.
            Should be a list of (name, sql type, default value, is primary) 
            tuples.
        :type extra_fields: ``[(``str``, ``str``, ``str`` or ``None``,
            ``Bool``)]``
        """
        if extra_fields is not None:
            self.TRACE_FIELDS.extend(extra_fields)
        self._create_table_if_not_exists(self.TRACE_TABLE,self.TRACE_FIELDS)

    def create_views(self):
        """
        Creates views for common database queries.
        """
        self._create_view(self.MASTER_VIEW, fields=None)
        self._create_view(self.VMTOMO_PICK_VIEW, fields=VMTOMO_PICK_FIELDS)
        self._create_view(self.VMTOMO_SHOT_VIEW, fields=VMTOMO_SHOT_FIELDS,
                          distinct=True)
        self._create_view(self.VMTOMO_INSTRUMENT_VIEW,
                          fields=VMTOMO_INSTRUMENT_FIELDS, distinct=True)

    def _create_view(self, name, fields=None, distinct=False):
        """ 
        Creates a view of a master natural join.
        """
        sql = 'CREATE VIEW IF NOT EXISTS %s AS SELECT ' % name
        if distinct is True:
            sql += ' DISTINCT '
        if fields is not None:
            sql += ', '.join(fields)
        else:
            sql += '*'
        sql += ' FROM %s' %self.PICK_TABLE
        sql += ' NATURAL JOIN %s' %self.TRACE_TABLE
        sql += ' NATURAL JOIN %s' %self.EVENT_TABLE
        logging.debug("calling: self.execute('%s')" %sql)
        self.execute(sql)

    def count_picks_by_event(self, event):
        """
        Return the number of picks for an event.

        :param event: Event to count.
        :type event: ``str``
        """
        return self._count_distinct(self.PICK_TABLE, event=event)

    def add_pick(self, **kwargs):
        """
        Add a new pick to the database.

        This function does three things:
            (1) Adds pick data to the ``picks`` table.
            (2) Makes sure that a row exists in the ``events`` table for
                ``event`` (1st primary key).
            (3) Makes sure than a row exists in the ``traces`` table for
                ``ensemble``, ``trace`` (2nd and 3rd primary
                keys).

        :param **kwargs: keyword=value arguments for fields in the ``picks``
            table.
        """
        # add pick data to the pick table
        pick = {}
        pick_fields = self._get_fields(self.PICK_TABLE)
        for k in kwargs:
            if k in pick_fields:
                pick[k] = kwargs[k]
        self._insert(self.PICK_TABLE, **pick)
        # create entries in metadata tables if they don't already exist
        for table in [self.EVENT_TABLE, self.TRACE_TABLE]:
            values = self._select_field_values(table,**kwargs)
            logging.debug('Adding ' + str(values) + " to table '%s'" % table)
            self._insertupdate(table, **values)
            
    def remove_pick(self, **kwargs):
        """
        Removes a pick from the database.

        .. note:: :meth:`remove_pick` leaves rows in the ``events`` and
            ``traces`` tables, even if the current pick was the only pick for a
            unique event and/or trace.

        :param **kwargs: keyword=value arguments for fields to match when
            choosing rows to remove.
        """
        values = self._select_field_values(self.PICK_TABLE, **kwargs)
        self._delete(self.PICK_TABLE, **values)

    def update_pick(self, **kwargs):
        """
        Update a pick in the database, or add if it does not already exist.
        
        :param **kwargs: keyword=value arguments for fields in the ``picks`` 
            table.
        """
        # update all tables
        for table in [self.PICK_TABLE, self.EVENT_TABLE, self.TRACE_TABLE]:
            values = self._select_field_values(table,**kwargs)
            logging.debug('Adding ' + str(values) + " to table '%s'" % table)
            self._insertupdate(table, **values)

    def write_vmtomo(self, instfile='inst.dat', pickfile='picks.dat', 
                     shotfile='shots.dat', directory='.', **kwargs):
        """
        Write pick data to VM Tomography format input files.

        :param instfile: Optional. Name of file to write instrument data to.
            Default is ``inst.dat``.
        :param pickfile: Optional. Name of file to write pick data to.
            Default is ``picks.dat``.
        :param shotfile: Optional. Name of file to write shot data to.
            Default is ``shots.dat``.
        :param directory: Optional. Name of path to append to filenames. 
            Default is to write files in the current working directory.
        :param **kwargs: Optional keyword=value arguments for fields in the
            picks table. Default is to write all picks.
        """
        f = open(directory + '/' + pickfile, 'w')
        f.write(self.get_vmtomo_picks(**kwargs))
        f.close()
        f = open(directory + '/' + instfile, 'w')
        f.write(self.vmtomo_inst)
        f.close()
        f = open(directory + '/' + shotfile, 'w')
        f.write(self.vmtomo_shots)
        f.close()

    def plot_geometry(self, dim=[0,1], receivers=True, sources=True, ax=None,
                      outfile=None):
        """
        Plot source and receiver positions on a 2D plot.

        :param dim: Coordinate dimensions to plot paths into. Default is z vs. x
            (``dim=[0,2]``).
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param receivers: Determines whether or not to plot symbols at
            the receiver locations. Default is ``True``.
        :param sources: Determines whether or not to plot symbols at
            the source locations. Default is ``False``.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        if sources:
            for src in self.get_source_positions():
                ax.plot(src[dim[0]], src[dim[1]], '*r')
        if receivers:
            for rec in self.get_receiver_positions():
                ax.plot(rec[dim[0]], rec[dim[1]], 'vy')
        if outfile:
            fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            plt.draw()

    def get_source_positions(self, **kwargs):
        """
        Get source positions from the database.
        
        :param **kwargs: Optional keyword=value arguments for fields in the
            traces table. Default is to write all picks.
        """
        sql = 'SELECT source_x, source_y, source_z FROM '
        sql += TRACE_TABLE 
        if len(kwargs) > 0:
            sql += " WHERE " + format_search(kwargs)
        return [(v[0], v[1], v[2]) for v in self.execute(sql).fetchall()]
        
    def get_receiver_positions(self, **kwargs):
        """
        Get receiver positions from the database.
        
        :param **kwargs: Optional keyword=value arguments for fields in the
            traces table. Default is to write all picks.
        """
        sql = 'SELECT receiver_x, receiver_y, receiver_z FROM '
        sql += TRACE_TABLE 
        if len(kwargs) > 0:
            sql += " WHERE " + format_search(kwargs)
        return [(v[0], v[1], v[2]) for v in self.execute(sql).fetchall()]

    def get_vmtomo_instrument_position(self, instrument):
        """
        Get x,y,z postion of an instrument from the VM Tomography instrument
        view.

        :param instrument: The number of the instrument to get the position for.
        :returns: x,y,z
        """
        sql = 'SELECT receiver_x, receiver_y, receiver_z FROM '\
                + VMTOMO_INSTRUMENT_VIEW
        sql += ' WHERE ensemble={:}'.format(instrument)
        logging.debug("calling: self.execute('%s').fetchone()" %sql)
        return self.execute(sql).fetchone()

    def get_picks(self, **kwargs):
        """
        Get rows with matching field values from master table.

        :param **kwargs: keyword=value arguments for fields in the master table.
        :returns: list of :class:`sqlite3.Row` row objects
        """
        sql = 'SELECT * FROM %s' % self.MASTER_VIEW
        if len(kwargs) > 0:
            sql += " WHERE " + format_search(kwargs)
        logging.debug("calling: self.execute('%s')" %sql)
        return self.execute(sql).fetchall()

    def _get_events(self):
        """
        Returns a list of unique event names in the database.
        """
        sql = 'SELECT event FROM %s' %self.EVENT_TABLE
        logging.debug("calling: self.execute('%s')" %sql)
        return [f[0] for f in self.execute(sql).fetchall()]

    def get_ensembles(self, **kwargs):
        """
        Returns a list of unique ensembles in the database.
        
        :param **kwargs: keyword=value arguments used to select instruments
            to output.
        """
        sql = 'SELECT DISTINCT ensemble FROM %s' %self.MASTER_VIEW
        if len(kwargs) > 0:
            sql += " WHERE " + format_search(kwargs)
        logging.debug("calling: self.execute('%s')" %sql)
        return [f[0] for f in self.execute(sql).fetchall()]

    def get_vmtomo_picks(self, **kwargs):
        """
        Returns a formated string of picks for input to VM Tomography.
        
        :param **kwargs: keyword=value arguments used to select picks to output
        """
        sql = 'SELECT * FROM {:}'.format(VMTOMO_PICK_VIEW)
        if len(kwargs) > 0:
            sql += " WHERE " + format_search(kwargs)
        return format_row_factory(self.execute(sql), none_value=0.0)

    def get_vmtomo_shots(self, **kwargs):
        """
        Returns a formated string of shots for input to VM Tomography.
        
        :param **kwargs: keyword=value arguments used to select shots to output
        """
        sql = 'SELECT * FROM {:}'.format(VMTOMO_SHOT_VIEW)
        if len(kwargs) > 0:
            sql += " WHERE " + format_search(kwargs)
        return format_row_factory(self.execute(sql), none_value=0.0)

    def get_vmtomo_inst(self, **kwargs):
        """
        Returns a formated string of instruments for input to VM Tomography.
        
        :param **kwargs: keyword=value arguments used to select instruments
            to output.
        """
        sql = 'SELECT * FROM {:}'.format(VMTOMO_INSTRUMENT_VIEW)
        if len(kwargs) > 0:
            sql += " WHERE " + format_search(kwargs)
        return format_row_factory(self.execute(sql), none_value=0.0)

    events = property(_get_events)
    ensembles = property(get_ensembles)
    picks = property(get_picks)
    vmtomo_picks = property(get_vmtomo_picks)
    vmtomo_shots = property(get_vmtomo_shots)
    vmtomo_inst = property(get_vmtomo_inst)
