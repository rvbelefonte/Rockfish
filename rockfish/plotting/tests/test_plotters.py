"""
Test suite for rockfish.plotting.plotters
"""
import os
import unittest
import inspect
import copy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from rockfish.segy.segy import readSEGY, TRACE_HEADER_KEYS
from rockfish.utils.loaders import get_example_file
from rockfish.picking.database import PickDatabaseConnection
from rockfish.segy.database import SEGYHeaderDatabase
from rockfish.plotting.plotters import SEGYPlotManager, \
        SEGYPlotter, SEGYPickPlotter

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

class SEGYPlotterTestCase(unittest.TestCase):
    """
    Test cases for SEGYPlotter and SEGYPickPlotter
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

    def test_init_SEGYPlotter(self):
        """
        Should create a new instance of the SEGYPlotter.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotter(ax, self.segy)
        # should inherit from SEGYPlotManager
        for member in inspect.getmembers(SEGYPlotManager):
            self.assertTrue(hasattr(splt, member[0]))
        # should *not* build header lookup table
        self.assertFalse(hasattr(splt, 'sdb'))
        # should attach axes
        self.assertTrue(isinstance(splt.ax, matplotlib.axes.Axes))

    def test_plot_negative_wiggle_fills(self):
        """
        Should add negative wiggle fills to the axes.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotter(ax, self.segy)
        # should add a single artist to the active patch dict.
        splt.plot_wiggles(negative_fills=True)
        self.assertEqual(len(splt.ACTIVE_PATCHES['negative_fills']),1)
        # same artist should be in the axes list
        self.assertTrue(splt.ACTIVE_PATCHES['negative_fills'][0] in \
                        splt.ax.patches)
        # should be able to directly remove it
        splt.ax.patches.remove(splt.ACTIVE_PATCHES['negative_fills'][0])
        self.assertEqual(len(splt.ax.patches), 0)
        # and re-add it
        splt.ax.patches.append(splt.ACTIVE_PATCHES['negative_fills'][0])
        self.assertEqual(len(splt.ax.patches), 1)
        # should move artist to the inactive patch dict.
        splt.plot_wiggles(negative_fills=False)
        self.assertEqual(len(splt.INACTIVE_PATCHES['negative_fills']),1)
        self.assertEqual(len(splt.ax.patches), 0)
        # calling again should change nothing
        splt.plot_wiggles(negative_fills=False)
        self.assertEqual(len(splt.INACTIVE_PATCHES['negative_fills']),1)
        self.assertEqual(len(splt.ax.patches), 0)
        # should move artist back to active patch dict.
        splt.plot_wiggles(negative_fills=True)
        self.assertEqual(len(splt.ACTIVE_PATCHES['negative_fills']),1)
        self.assertEqual(len(splt.ax.patches), 1)
        # new plot items should be accessible through the orig. axes
        self.assertEqual(len(splt.ax.patches),
                         len(ax.patches))

    def test_plot_positive_wiggle_fills(self):
        """
        Should add positive wiggle fills to the axes.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotter(ax, self.segy)
        # should add a single artist to the active patch dict.
        splt.plot_wiggles(positive_fills=True)
        self.assertEqual(len(splt.ACTIVE_PATCHES['positive_fills']),1)
        # same artist should be in the axes list
        self.assertTrue(splt.ACTIVE_PATCHES['positive_fills'][0] in \
                        splt.ax.patches)
        # should be able to directly remove it
        splt.ax.patches.remove(splt.ACTIVE_PATCHES['positive_fills'][0])
        self.assertEqual(len(splt.ax.patches), 0)
        # and re-add it
        splt.ax.patches.append(splt.ACTIVE_PATCHES['positive_fills'][0])
        self.assertEqual(len(splt.ax.patches), 1)
        # should move artist to the inactive patch dict.
        splt.plot_wiggles(positive_fills=False)
        self.assertEqual(len(splt.INACTIVE_PATCHES['positive_fills']),1)
        self.assertEqual(len(splt.ax.patches), 0)
        # calling again should change nothing
        splt.plot_wiggles(positive_fills=False)
        self.assertEqual(len(splt.INACTIVE_PATCHES['positive_fills']),1)
        self.assertEqual(len(splt.ax.patches), 0)
        # should move artist back to active patch dict.
        splt.plot_wiggles(positive_fills=True)
        self.assertEqual(len(splt.ACTIVE_PATCHES['positive_fills']),1)
        self.assertEqual(len(splt.ax.patches), 1)
        # new plot items should be accessible through the orig. axes
        self.assertEqual(len(splt.ax.patches),
                         len(ax.patches))

    def test_plot_wiggle_traces(self):
        """
        Should add wiggle traces to the axes.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotter(ax, self.segy)
        # should add a single artist to the active line dict.
        splt.plot_wiggles(wiggle_traces=True)
        self.assertEqual(len(splt.ACTIVE_LINES['wiggle_traces']),1)
        # same artist should be in the axes list
        self.assertTrue(splt.ACTIVE_LINES['wiggle_traces'][0] in \
                        splt.ax.lines)
        # should be able to directly remove it
        splt.ax.lines.remove(splt.ACTIVE_LINES['wiggle_traces'][0])
        self.assertEqual(len(splt.ax.lines), 0)
        # and re-add it
        splt.ax.lines.append(splt.ACTIVE_LINES['wiggle_traces'][0])
        self.assertEqual(len(splt.ax.lines), 1)
        # should move artist to the inactive line dict.
        splt.plot_wiggles(wiggle_traces=False)
        self.assertEqual(len(splt.INACTIVE_LINES['wiggle_traces']),1)
        self.assertEqual(len(splt.ax.lines), 0)
        # calling again should change nothing
        splt.plot_wiggles(wiggle_traces=False)
        self.assertEqual(len(splt.INACTIVE_LINES['wiggle_traces']),1)
        self.assertEqual(len(splt.ax.lines), 0)
        # should move artist back to active line dict and re-add to axes
        splt.plot_wiggles(wiggle_traces=True)
        self.assertEqual(len(splt.ACTIVE_LINES['wiggle_traces']),1)
        self.assertEqual(len(splt.ax.lines), 1)
        # new plot items should be accessible through the orig. axes
        self.assertEqual(len(splt.ax.lines),
                         len(ax.lines))

    def test_link_axes(self):
        """
        Plotting should update items in the linked axes.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotter(ax, self.segy)
        # should add one artist to our axes
        splt.plot_wiggles(wiggle_traces=True)
        self.assertEqual(len(splt.ACTIVE_LINES['wiggle_traces']), 1)
        self.assertTrue('wiggle_traces' not in splt.INACTIVE_LINES)
        self.assertEqual(len(ax.lines), 1)
        # should remove one artist to our axes
        splt.plot_wiggles(wiggle_traces=False)
        self.assertTrue('wiggle_traces' not in splt.ACTIVE_LINES)
        self.assertEqual(len(splt.INACTIVE_LINES['wiggle_traces']), 1)
        self.assertEqual(len(ax.lines), 0)

    def test_init_SEGYPickPlotter(self):
        """
        Should create a new instance of the SEGYPickPlotter.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPickPlotter(ax, self.segy, pickdb=self.pickdb)
        # should inherit from SEGYPlotter
        for member in inspect.getmembers(SEGYPlotter):
            self.assertTrue(hasattr(splt, member[0]))
        # should build header lookup table
        self.assertTrue(isinstance(splt.sdb, SEGYHeaderDatabase))
        # should attach axes
        self.assertTrue(isinstance(splt.ax, matplotlib.axes.Axes))
        
    def test_plot_picks(self):
        """
        Should add picks to an axes and the layer managers.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        pickdb = PickDatabaseConnection(':memory:')
        for pick in uniq_picks:
            pickdb.update_pick(**pick)
        splt = SEGYPickPlotter(ax, self.segy, pickdb)
        # should add a single artist to the line dict. for each event
        splt.plot_picks()
        for event in self.pickdb.events:
            self.assertTrue(len(splt.ACTIVE_LINES[event]), 1)
        # should be able to add new picks and have them be accessible by the
        # SEGYPickPlotter
        new_event = '--tracer--'
        new_pick = copy.copy(uniq_picks[0])
        new_pick['event'] = new_event
        pickdb.update_pick(**new_pick)
        splt.plot_picks()
        self.assertTrue(new_event in splt.ACTIVE_LINES)


def suite():
    return unittest.makeSuite(SEGYPlotterTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

