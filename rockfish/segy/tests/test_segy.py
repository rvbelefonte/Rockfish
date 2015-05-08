"""
Test suite for rockfish.segy.segy
"""

import unittest
from rockfish.segy.segy import readSEGY, SEGYFile
from rockfish.utils.loaders import get_example_file

class SEGYFileTestCase(unittest.TestCase):

    def test_readSEGY(self):
        """
        Should return a rockfish.segy.segy.SEGYFile 
        """
        segy = readSEGY(get_example_file('ew0210_o30.segy'))
        self.assertTrue(isinstance(segy, SEGYFile))

    def test_scaled_ensemble_coordinates(self):
        """
        Should scale and unscale ensemble coordinates
        """
        segy = readSEGY(get_example_file('ew0210_o30.segy'))

        tr = segy.traces[0]

        # should set geographic coordinates
        tr.header.coordinate_units = 2
        tr.header.scalar_to_be_applied_to_all_coordinates = -100
        lon, lat = (-110.3001, 35.012)
        tr.header.scaled_ensemble_coordinate_x = lon
        tr.header.scaled_ensemble_coordinate_y = lat
        self.assertEqual(tr.header.scaled_ensemble_coordinate_x, lon)
        self.assertEqual(tr.header.scaled_ensemble_coordinate_y, lat)

        # should be preserve values through i/o
        segy.traces = [tr]
        segy.write('temp_test.segy')
        segy1 = readSEGY('temp_test.segy')
        tr1 = segy1.traces[0]
        self.assertEqual(tr1.header.scaled_ensemble_coordinate_x, lon)
        self.assertEqual(tr1.header.scaled_ensemble_coordinate_y, lat)

        # should set cartesian coordinates
        tr.header.coordinate_units = 1
        tr.header.scalar_to_be_applied_to_all_coordinates = 1
        x, y = (1232312, 2231244512)
        tr.header.scaled_ensemble_coordinate_x = x
        tr.header.scaled_ensemble_coordinate_y = y
        self.assertEqual(tr.header.ensemble_coordinate_x, x)
        self.assertEqual(tr.header.ensemble_coordinate_y, y)





def suite():
    return unittest.makeSuite(SEGYFileTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

