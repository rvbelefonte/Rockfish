"""
General database tools.
"""
import sqlite3
import logging

class RockfishDatabaseConnection(sqlite3.Connection):
    """
    Base class for creating a database connection.
    """
    def __init__(self, database, *args, **kwargs):
        sqlite3.Connection.__init__(self, database, *args, **kwargs)
        # enable case-insensative keyword access to data rows
        self.row_factory = sqlite3.Row

    def _insert(self, table, **kwargs):
        """
        Adds an entry to a table.
        
        :param table: Name of table to add data to.
        :type table: ``str``
        :param **kwargs: keyword=value arguments for fields in the ``events`` 
            table.
        """
        sql = 'INSERT INTO %s (%s)' \
              %(table, ', '.join([k for k in kwargs]))
        sql += ' VALUES (%s)' % ', '.join(['?' for k in kwargs])
        data = tuple([kwargs[k] for k in kwargs])
        logging.debug("calling: self.execute('%s', '%s')" %(sql, data))
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
        sql += " WHERE " + ' and '.join(['%s="%s"' %(k, kwargs[k])\
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
        sql += ', '.join(['%s="%s"' %(k, kwargs[k]) for k in kwargs])
        sql += ' WHERE '
        sql += ' and '.join(['%s="%s"' %(k, pvalues[k]) for k in pvalues])
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
            values = ['%s="%s"' %(k, kwargs[k]) for k in kwargs] 
            sql += ' WHERE ' + ' and '.join(values)
        logging.debug('calling: self.execute(%s)' %sql)
        return self.execute(sql).fetchall()[0][0]

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
        sql = 'PRAGMA table_info(%s)' %table
        logging.debug('calling: self.execute(%s)' %sql)
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
        sql += " WHERE " + ' and '.join(['%s="%s"' %(k, kwargs[k])\
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
        _fields=[]
        _primary_fields = []
        for f in fields:
            #Build: name type [NOT NULL] [DEFAULT default_value]
            _fields.append('%s %s' %(f[0], f[1]))
            if f[3] is True:
                # require NOT NULL
                _fields[-1] += ' NOT NULL'
            if f[4] is True:
                # add to list of primary keys
                _primary_fields.append(f[0])
            if f[2] is not None:
                # include default value
                _fields[-1] += ' DEFAULT %s' % f[2]
        sql =  "CREATE TABLE IF NOT EXISTS '" + table + "'"
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