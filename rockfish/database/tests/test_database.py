"""
Test suite for the database module
"""
import os
import inspect
import sqlite3
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
        pickdb = RockfishDatabaseConnection(':memory:')
        # no file should be created
        self.assertFalse(os.path.isfile(':memory:'))
        # should inherit from sqlite3.Connection
        for member in inspect.getmembers(sqlite3.Connection):
            self.assertTrue(hasattr(pickdb, member[0]))
        # should create a connection to a new file on the disk
        filename = 'temp.sqlite'
        if os.path.isfile(filename):
            os.remove(filename)
        pickdb = RockfishDatabaseConnection('temp.sqlite')
        self.assertTrue(os.path.isfile(filename))
        # should connect to an existing file on the disk
        pickdb = RockfishDatabaseConnection(filename)
        # clean up
        os.remove(filename)


def suite():
    return unittest.makeSuite(DatabaseTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
