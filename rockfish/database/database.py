"""
General database tools
"""
import sqlite3
from sqlite3 import OperationalError
import logging
import warnings
from rockfish.utils.messaging import Colors as TermColors
from rockfish.utils.user_input import query_yes_no


class RockfishDatabaseConnection(sqlite3.Connection):
    """
    Base class for creating a database connection.
    """
    def __init__(self, database, *args, **kwargs):
        sqlite3.Connection.__init__(self, database, *args, **kwargs)
        # enable case-insensative keyword access to data rows
        self.row_factory = sqlite3.Row

    def _add_field_if_not_exists(self, table, name, sql_type='TEXT'):
        """
        Add a field to an existing table if it does not already exist.

        :param table: Name of table to add field to.
        :param name: Field name.
        :param sql_type: SQLite data type for the new field. Default is TEXT.
        """
        if name not in self._get_fields(table):
            sql = 'ALTER TABLE {:}'.format(table)
            sql += ' ADD COLUMN {:} {:}'.format(name, sql_type)
            self.execute(sql)

    def _insert(self, table, **kwargs):
        """
        Adds an entry to a table.

        Will be decreciated soon. Use insert() instead.
        """
        msg = '_insert() will be removed in the future, use insert() instead.'
        PendingDeprecationWarning(msg)
        return self.insert(self, table, **kwargs)

    def insert(self, table, **kwargs):
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
            self.insert(table, **kwargs)

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

    def _get_tables(self):
        """
        Returns a list of tables in the database.
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        return [d[0] for d in self.execute(sql)]
    tables = property(_get_tables)

    def _get_views(self):
        """
        Returns a list of views in the database.
        """
        sql = "SELECT name FROM sqlite_master WHERE type='view'"
        return [d[0] for d in self.execute(sql)]
    views = property(_get_views)

    def drop(self, name, startswith=False, endswith=False, includes=False, 
             like=False, confirm=True):
        """
        Drop tables and/or views matching a name.
        """
        sql = "SELECT name, type FROM sqlite_master"
        sql += " WHERE type='table' OR type='view'"
        for name_, type_ in self.execute(sql).fetchall():
            drop = False
            if name_ == name:
                drop = True
            elif (startswith or like) and (str(name_).startswith(name)):
                drop = True
            elif (endswith or like) and (str(name_).endswith(name)):
                drop = True
            elif (includes or like) and (name in name_):
                drop = True
            if drop and confirm:
                print TermColors.WARNING,
                drop = query_yes_no('Drop {:} {:}?'.format(type_, name_),
                                    default='no')
                print TermColors.ENDC
            if drop:
                sql = 'DROP {:} {:}'.format(type_, name_)
                self.execute(sql)

    def print_pragma(self, table):
        """
        Print the result of pragma on a table.

        :param table: Name of table to get PRAGMA for.
        """
        for row in self._get_pragma(table):
            print row

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

    def _count_distinct(self, table, **kwargs):
        """
        Return a count of matching rows.

        :param table: Name of the table to query.
        :type table: ``str``
        :param **kwargs: keyword=value arguments for fields to count.
        """

        sql = "SELECT DISTINCT COUNT(*) FROM %s" % table
        sql += " WHERE " + ' and '.join(['{:}="{:}"'.format(k, kwargs[k])\
                                         for k in kwargs])
        return self.execute(sql).fetchall()[0][0]

    def _create_table_if_not_exists(self, table, fields):
        """
        Shortcut function for creating new tables.

        :param table: Name of the table to create.
        :type table: ``str``
        :param fields: Fields to include in the new table.
            Should be a list of (name, sql type, default value, is not null,
            is primary) tuples.
        :type fields: ``[(``str``, ``str``, ``str`` or ``None``,
            ``bool``, ``bool``)]``
        """
        _fields = []
        _primary_fields = []
        for f in fields:
            #Build: name type [NOT NULL] [DEFAULT default_value]
            _fields.append('{:} {:}'.format(f[0], f[1]))
            if f[3] is True:
                # require NOT NULL
                _fields[-1] += ' NOT NULL'
            if f[4] is True:
                # add to list of primary keys
                _primary_fields.append(f[0])
            if f[2] is not None:
                # include default value
                _fields[-1] += ' DEFAULT %s' % f[2]
        sql = "CREATE TABLE IF NOT EXISTS '" + table + "'"
        sql += ' ('
        sql += ', '.join(_fields)
        if len(_primary_fields) > 0:
            sql += ', PRIMARY KEY (' + ', '.join(_primary_fields) + ') '
        sql += ');'
        logging.debug("calling: execute('%s')" % sql)
        self.execute(sql)

    def _select_primary_field_values(self, table, **kwargs):
        """
        Returns a dictionary of values for primary fields that are in a table.

        :param table: Name of table to get field values for.
        :type table: ``str``
        :param **kwargs: keyword=value arguments to select values from.
        """
        fields = self._get_primary_fields(table)
        values = {}
        for k in kwargs:
            if k in fields:
                values[k] = kwargs[k]
        return values

    def _select_field_values(self, table, **kwargs):
        """
        Returns a dictionary of values for fields that are in a table.

        :param table: Name of table to get field values for.
        :type table: ``str``
        :param **kwargs: keyword=value arguments to select values from.
        """
        fields = self._get_fields(table)
        values = {}
        for k in kwargs:
            if k in fields:
                values[k] = kwargs[k]
        return values
