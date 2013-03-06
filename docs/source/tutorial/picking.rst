
.. _pickdatabase-tutorial:

Travel time databases
*********************

Rockfish has support for managing travel-time picks. In Rockfish, picks are
stored in a `SQLite <http://www.sqlite.org>` database with a set of
standardized tables and fields. The following tutorial describes how to
setup up this database, and get pick data in and out of the database.

Creating a Pick Database
========================

To create a new database on the disk, or reconnect to an existing database:

>>> from rockfish.picking.database import PickDatabaseConnection
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
predicted         real       Modeled travel time.   None 
residual          real       Difference between     None
                             picked and predicted
                             travel times.
time_reduced      real       Reduced pick time in   None
                             seconds.
error             real       Pick error in seconds. ``0.0``
timestamp         timestamp  Time pick was entered  ``CURRENT_TIMESTAMP``
                             or updated.
method            text       Method used to make    ``'unknown'``
                             the pick.
data_file         text       Data file the pick was None
                             made on.
ray_btm_x         real       x-coordinate for the   None
                             raypath's bottoming
                             point
ray_btm_y         real       y-coordinate for the   None
                             raypath's bottoming
                             point
ray_btm_z         real       z-coordinate for the   None
                             raypath's bottoming
                             point
================= =========  ====================== =====================

Other custom fields may be added to tables in the database, but names should 
be different from those in the tables above.  To add a custom field to a
new database, initiate the database with, for example:

>>> other_fields = [#(name, sql_type, default_value, is_not_null, is_primary)
>>>                  ('myfield1', 'TEXT', 'default_value1', False, False),
>>>                  ('myfield2', 'TEXT', 'default_value2', False, False)]
>>> pickdb = PickDatabaseConnection(':memory:', extra_pick_fields=other_fields)

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
trace_in_file     integer    Trace sequence number  None
                             within the SEGY file
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
