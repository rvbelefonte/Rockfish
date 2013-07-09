"""
Test suite for the database module
"""
import os
import inspect
from pyspatialite.dbapi2 import Connection as SpatialiteConnection
import unittest
from rockfish.database.database import RockfishDatabaseConnection


class DatabaseTestCase(unittest.TestCase):
    """
    Test cases for the database module
    """
    def test_init_RockfishDatabaseConnection(self):
        """
        Connect should initiate a working sqlite3 connection and cursor.
        """
        # should connect to a database in memory
        db = RockfishDatabaseConnection(':memory:')
        # no file should be created
        self.assertFalse(os.path.isfile(':memory:'))
        # should inherit from sqlite3.Connection
        for member in inspect.getmembers(SpatialiteConnection):
            self.assertTrue(hasattr(db, member[0]))
        # should create a connection to a new file on the disk
        filename = 'temp.sqlite'
        if os.path.isfile(filename):
            os.remove(filename)
        db = RockfishDatabaseConnection('temp.sqlite')
        self.assertTrue(os.path.isfile(filename))
        # should connect to an existing file on the disk
        db = RockfishDatabaseConnection(filename)
        # clean up
        os.remove(filename)

    def test__add_field_if_not_exists(self):
        """
        Should add a field only if it does not already exist.
        """
        db = RockfishDatabaseConnection(':memory:')
        field_name = 'field1'
        fields = [(field_name, 'REAL', None, False, False)]
        db._create_table_if_not_exists('table1', fields)
        # should have the field
        current_fields = db._get_fields('table1')
        self.assertEqual(len(current_fields), 1)
        # try to add the field again
        db._add_field_if_not_exists('table1', field_name)


def suite():
    return unittest.makeSuite(DatabaseTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
