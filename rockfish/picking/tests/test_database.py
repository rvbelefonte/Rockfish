"""
Test suite for rockfish.picking
"""

import unittest
import matplotlib.pyplot as plt
import numpy as np
import os
import sqlite3
import inspect
import logging

from rockfish.picking.database import PickDatabaseConnection,\
    PickDatabaseConnectionError, PICK_FIELDS, EVENT_FIELDS, TRACE_FIELDS

# XXX force debug
logging.basicConfig(level=logging.DEBUG,
    format='%(filename)s:%(funcName)s:%(levelname)s:%(message)s')


# Benchmark data
uniq_picks = []
events =    ['Pg', 'Pg', 'Pg', 'Pn']
ensembles = [100, 100, 100, 100]
traces =    [1, 2, 3, 1]
for i in range(0, len(events)):
    uniq_picks.append({
        'event':events[i],
        'ensemble':ensembles[i],
        'trace':traces[i],
        'time':12.3456789,
        'source_x':-123.456,
        'source_y':-12.345,
        'source_z':0.006,
        'receiver_x':-654.321,
        'receiver_y':54.321,
        'receiver_z':1234.5678})


class PickingTestCase(unittest.TestCase):
    """
    Test cases for the picking classes and modules.
    """
    def setUp(self):
        """
        Set benchmark data.
        """
        pass

    def test_init_PickDatabaseConnection(self):
        """
        Connect should initiate a working sqlite3 connection and cursor.
        """
        # should connect to a database in memory
        pickdb = PickDatabaseConnection(':memory:')
        # no file should be created
        self.assertFalse(os.path.isfile(':memory:'))
        # should inherit from sqlite3.Connection
        for member in inspect.getmembers(sqlite3.Connection):
            self.assertTrue(hasattr(pickdb, member[0]))
        # should create a connection to a new file on the disk
        filename = 'temp.sqlite'
        if os.path.isfile(filename):
            os.remove(filename)
        pickdb = PickDatabaseConnection('temp.sqlite')
        self.assertTrue(os.path.isfile(filename))
        # should connect to an existing file on the disk
        pickdb = PickDatabaseConnection(filename)
        # clean up
        os.remove(filename)

    def test_add_remove_picks(self):
        """
        Should add a pick to the picks table.
        """
        pickdb = PickDatabaseConnection(':memory:')
        # should add all picks to the database
        for pick in uniq_picks:
            pickdb.add_pick(**pick)
        pickdb.commit()
        ndb = len(pickdb.execute('SELECT * FROM picks').fetchall())
        self.assertEqual(ndb, len(uniq_picks))
        # attempting to add pick without primary fields should raise an error
        with self.assertRaises(sqlite3.IntegrityError):
            pickdb.add_pick(event='Foobar',time=9.834)
        # attempting to add duplicate picks should raise error
        for pick in uniq_picks:
            with self.assertRaises(sqlite3.IntegrityError):
                pickdb.add_pick(**pick)
        # directly removing pick and then re-adding should work
        for pick in uniq_picks:
            pickdb.remove_pick(**pick)
            pickdb.add_pick(**pick)
        pickdb.commit()
        ndb = len(pickdb.execute('SELECT * FROM picks').fetchall())
        self.assertEqual(ndb, len(uniq_picks))
        # invalid collumn names should raise OperationalError 
        with self.assertRaises(sqlite3.OperationalError):
            pickdb.remove_pick(not_a_field=999)
        with self.assertRaises(sqlite3.OperationalError):
            pickdb.add_pick(not_a_field=999)
        # remove the last pick that we added
        pickdb.remove_pick(**pick)
        # attempting to remove a non-existant pick should do nothing
        pickdb.remove_pick(**pick)
        # updating picks should add picks if they don't exist and update picks
        # if they do exist 
        for pick in uniq_picks:
            pickdb.update_pick(**pick)
        pickdb.commit()
        ndb = len(pickdb.execute('SELECT * FROM picks').fetchall())
        self.assertEqual(ndb, len(uniq_picks))
        # should not be able to add pick without required fields
        with self.assertRaises(sqlite3.IntegrityError):
            pickdb.add_pick(event='Pg',ensemble=1, trace=1)
        # should not be able to corrupt the database with add_pick
        # TODO try to do things like DROP TABLE by setting pick attributes

    def test_counts(self):
        """
        Count functions should return number of distinct rows in tables.
        """
        pickdb = PickDatabaseConnection(':memory:')
        # add a single pick
        event = 'TestCount'
        pick = uniq_picks[0]
        pick['event'] = event
        pickdb.add_pick(**pick)
        pickdb.commit()
        # should have a single pick for this event in picks table 
        n = pickdb.count_picks_by_event(event)
        self.assertEqual(n, 1)
        # should also have a single entry in the event table
        n = pickdb._count_distinct(pickdb.EVENT_TABLE, event=event)
        self.assertEqual(n, 1)
        # now, another pick for the same event
        pick['ensemble'] += 1  # ensure unique
        pickdb.add_pick(**pick)
        pickdb.commit()
        # should have two picks for this event in the picks table
        n = pickdb.count_picks_by_event(event)
        self.assertEqual(n, 2)
        # should still just have one entry in the event table for this event
        n = pickdb._count_distinct(pickdb.EVENT_TABLE, event=event)
        self.assertEqual(n, 1)

    def test_get_picks(self):
        """
        Should return data rows. 
        """
        # create a new database in memory
        pickdb = PickDatabaseConnection(':memory:')
        # add picks, and get our own times
        times0 = []
        for pick in uniq_picks:
            pickdb.add_pick(**pick)
            times0.append(pick['time'])
        pickdb.commit()
        # should return a list of sqlite3.Row objects
        for row in pickdb.get_picks(event=pick['event']):
            self.assertTrue(isinstance(row, sqlite3.Row))
        # should return the same data 
        times1 = []
        for pick in uniq_picks:
            row = pickdb.get_picks(**pick)[0]
            times1.append(row['time'])
        self.assertEqual(sorted(times0), sorted(times1))
        # should return all data
        self.assertEqual(len(uniq_picks),
                         len(pickdb.get_picks()))
        # should return empty list if no matches
        self.assertEqual(len(pickdb.get_picks(event='golly_gee')),0)
        # should also return empty list if no data
        pickdb = PickDatabaseConnection(':memory:')
        self.assertEqual(len(pickdb.get_picks()),0)

    def test_get_events(self):
        """
        Should return a list of event names in the database.
        """
        pickdb = PickDatabaseConnection(':memory:')
        # add picks and get our own list of event names
        events = []
        for i,pick in enumerate(uniq_picks):
            pickdb.add_pick(**pick)
            if pick['event'] not in events:
                events.append(pick['event'])
        # private function should return a list of events
        self.assertEqual(sorted(pickdb._get_events()),
                         sorted(events))
        # public 'events' attribute should be a property with
        # setfunction=_get_events
        self.assertEqual(pickdb.events,
                         pickdb._get_events())
        # should return empty list for empty database
        pickdb = PickDatabaseConnection(':memory:')
        self.assertEqual(pickdb.events, [])



def suite():
    return unittest.makeSuite(PickingTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
