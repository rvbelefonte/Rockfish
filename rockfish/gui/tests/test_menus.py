"""
Test suite for rockfish.gui.menus
"""

import unittest
import matplotlib.pyplot as plt
import matplotlib
import wx
from rockfish.segy.segy import readSEGY
from rockfish.utils.loaders import get_example_file
from rockfish.picking.database import PickDatabaseConnection
from rockfish.gui.menus import PlotSegyViewMenu, PlotSegyPlottingMenu, \
    PlotSegyPickingMenu, PlotSegyFileMenu

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

class MenusTestCase(unittest.TestCase):
    """
    Master suite for testing the menu classes.
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

    # XXX no tests!

def suite():
    return unittest.makeSuite(MenusTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

