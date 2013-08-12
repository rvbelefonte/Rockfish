"""
Test suite for rockfish.plotting.managers
"""
import os
import unittest
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from rockfish.segy.segy import readSEGY, TRACE_HEADER_KEYS
from rockfish.utils.loaders import get_example_file
from rockfish.picking.database import PickDatabaseConnection
from rockfish.segy.database import SEGYHeaderDatabase
from rockfish.plotting.managers import SEGYPlotManager

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

class SEGYPlotManagerTestCase(unittest.TestCase):
    """
    Test cases for SEGYPlotManager
    """
    def setUp(self):
        """
        Setup benchmark data.
        """
        self.segy = readSEGY(get_example_file('ew0210_o30.segy'),
                             unpack_headers=True)
        self.pickdb = PickDatabaseConnection(':memory:')
        for pick in uniq_picks:
            self.pickdb.update_pick(**pick)
        self.default_params = [
            'ABSCISSA_KEY', 'GAIN', 'CLIP',
            'NORMALIZATION_METHOD', 'OFFSET_GAIN_POWER',
            'WIGGLE_PEN_COLOR', 'WIGGLE_PEN_WIDTH',
            'NEG_FILL_COLOR', 'POS_FILL_COLOR', 'DISTANCE_UNIT',
            'TIME_UNIT', 'SEGY_TIME_UNITS', 'SEGY_DISTANCE_UNITS',
            'SEGY_HEADER_ALIASES']

    def test_init_SEGYPlotManager(self):
        """
        Should create a new instance of the SEGYPlotManager.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotManager(ax, self.segy)
        # should have the default parameters
        for attr in self.default_params:
            self.assertTrue(hasattr(splt, attr))
        # by default, should *not* have header databse
        self.assertFalse(hasattr(splt, 'sdb'))
        # should attach axes
        self.assertTrue(isinstance(splt.ax, matplotlib.axes.Axes))
        # class should be able to update the axes
        splt.ax.plot([0,1],[0,1])
        self.assertEqual(len(splt.ax.lines), 1)
        # updates outside the class should be seen inside the class
        ax.plot([0,1],[0,1])
        self.assertEqual(len(splt.ax.lines), 2)
        self.assertEqual(len(ax.lines), 2)
        # if a pick database is given, should attach pickdb and build lookup db
        splt = SEGYPlotManager(ax, self.segy, pickdb=self.pickdb)
        self.assertTrue(isinstance(splt.pickdb, PickDatabaseConnection))
        self.assertTrue(isinstance(splt.sdb, SEGYHeaderDatabase))
    
    def test_build_header_database(self):
        """
        Should connect to a database for looking up header attributes.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        # connecting to a database in memory should not create a file
        splt = SEGYPlotManager(ax, self.segy, trace_header_database=':memory:')
        self.assertFalse(os.path.isfile(':memory:'))
        # connecting to a filename should create a file if it does not exist
        filename = 'temp.test_build_header_database.sqlite'
        if os.path.isfile(filename):
            os.remove(filename)
        # should not create database if no pickdb is given
        splt = SEGYPlotManager(ax, self.segy, trace_header_database=filename)
        self.assertFalse(os.path.isfile(filename))
        # should create database if pickdb is given
        splt = SEGYPlotManager(ax, self.segy, pickdb=self.pickdb, 
                               trace_header_database=filename)
        self.assertTrue(os.path.isfile(filename))
        # clean up
        os.remove(filename)
        # create plot manager in memory with pickdb
        splt = SEGYPlotManager(ax, self.segy, pickdb=self.pickdb)
        # should be able to get primary fields from the picks trace table
        pick_keys = splt.pickdb._get_primary_fields(splt.pickdb.TRACE_TABLE)
        self.assertTrue(len(pick_keys) > 0)
        # pick primary keys should be in the alias dictionary
        # or be a header attribute
        header = self.segy.traces[0].header
        for k in pick_keys:
            self.assertTrue(k in splt.SEGY_HEADER_ALIASES \
                            or hasattr(header, k))
        # should add header fields for primary keys in the pick database
        sql = 'SELECT * FROM %s' %splt.sdb.TRACE_TABLE
        data = splt.sdb.execute(sql)
        for key in pick_keys:
            _key = splt._get_header_alias(key)
            for i,row in enumerate(data):
                segy_value = splt.get_header_value(
                    self.segy.traces[i].header, key,                                                convert_units=False)
                db_value = row[_key]
                self.assertEqual(segy_value, db_value)

    def test_get_units(self):
        """
        Should return (segy units, plot units) or None.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotManager(ax, self.segy)
        splt.DISTANCE_UNIT = 'distance_unit_marker'
        splt.TIME_UNIT = 'time_unit_marker'
        for key in TRACE_HEADER_KEYS:
            if key in splt.SEGY_TIME_UNITS:
                # should return TIME_UNIT for a time attribute
                self.assertEqual(splt._get_units(key)[1],
                                 'time_unit_marker')
            elif key in splt.SEGY_DISTANCE_UNITS:
                # should return DISTANCE_UNIT for a distance attribute
                self.assertEqual(splt._get_units(key)[1],
                                 'distance_unit_marker')
            else:
                # should return None values are unitless
                self.assertEqual(splt._get_units(key), None)

    def test_convert_units(self):
        """
        Should convert header units to plot units.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotManager(ax, self.segy)
        # should correctly perform unit conversions for distance
        splt.DISTANCE_UNIT = 'km'
        self.assertEqual(splt._convert_units('offset', [1000]), [1])
        # should correctly perform unit conversions for time
        splt.TIME_UNIT = 's'
        self.assertEqual(splt._convert_units('delay', [1000]), [1]) 

    def test_get_time_array(self):
        """
        Should return an array of time values for a single trace.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotManager(ax, self.segy)
        tr = self.segy.traces[0]
        # should have npts values
        npts = splt.get_header_value(tr.header, 'npts')
        t = splt.get_time_array(tr.header)
        self.assertEqual(npts, len(t))

    def test_get_header_value(self):
        """
        Should be able to use aliases to get unit-converted values 
        from headers.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotManager(ax, self.segy)
        # should return exact header values when convert_units=False
        tr = self.segy.traces[0]
        for alias in splt.SEGY_HEADER_ALIASES:
            key = splt.SEGY_HEADER_ALIASES[alias]
            value = splt.get_header_value(tr.header, alias,
                                           convert_units=False)
            _value = tr.header.__getattribute__(key)
            self.assertEqual(value, _value)
        # default should return header values in the plot units
        splt.DISTANCE_UNIT = 'km'
        alias = 'offset'
        key = splt.SEGY_HEADER_ALIASES[alias]
        scaled_value = splt.get_header_value(tr.header, alias)
        header_value = tr.header.__getattribute__(key)
        self.assertEqual(np.round(scaled_value, decimals=3), 
                         header_value/1000.)

    def test_get_abscissa(self):
        """
        Should return a list of abcissa values.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotManager(ax, self.segy, pickdb=self.pickdb)
        # just get abcissa for a subset of the traces
        idx = [0, 100, 103, 104, 500, 550]
        values = []
        for i in idx:
            ensemble = self.segy.traces[i].header.ensemble_number
            trace = \
                self.segy.traces[i].header.trace_number_within_the_ensemble
            values.append((ensemble, trace))
        # should return a list of values for plot x-axis
        x = splt._get_abscissa(['ensemble', 'trace'], values)
        _key = splt._get_header_alias(splt.ABSCISSA_KEY)
        for j,i in enumerate(idx):
            tr = self.segy.traces[i]
            self.assertEqual(tr.header.__getattribute__(_key),
                             x[j])

    def test_manage_layers(self):
        """
        Should handle moving plot items around.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotManager(ax, self.segy)
        # should echo parameters if item is not in dicts
        self.assertTrue(splt._manage_layers(foobar=True)['foobar'])
        self.assertFalse(splt._manage_layers(foobar=False)['foobar'])
        # for active item and True, should do nothing
        splt.ACTIVE_LINES['foobar'] = ax.plot([0,1], [0,1])
        self.assertTrue('foobar' in splt.ACTIVE_LINES)
        self.assertFalse('foobar' in splt.INACTIVE_LINES)
        self.assertFalse(splt._manage_layers(foobar=True)['foobar'])
        self.assertTrue('foobar' in splt.ACTIVE_LINES)
        self.assertFalse('foobar' in splt.INACTIVE_LINES)
        # for active item and False, should move to inactive and return False
        self.assertFalse(splt._manage_layers(foobar=False)['foobar'])
        self.assertFalse('foobar' in splt.ACTIVE_LINES)
        self.assertTrue('foobar' in splt.INACTIVE_LINES)
        # for force_new=True, should remove from active and inactive and return
        # True
        # item is currently in inactive list
        need2plot = splt._manage_layers(force_new=True, foobar=True)
        self.assertTrue(need2plot['foobar'])
        self.assertFalse('foobar' in splt.ACTIVE_LINES)
        self.assertFalse('foobar' in splt.INACTIVE_LINES)
        # item is now in active list
        splt.ACTIVE_LINES['foobar'] = ax.plot([0,1], [0,1])
        need2plot = splt._manage_layers(force_new=True, foobar=True)
        self.assertTrue(need2plot['foobar'])
        self.assertFalse('foobar' in splt.ACTIVE_LINES)
        self.assertFalse('foobar' in splt.INACTIVE_LINES)


def suite():
    return unittest.makeSuite(SEGYPlotManagerTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
