"""
Test suite for the acoustic survey module.
"""
import unittest
import numpy as np
from rockfish.navigation.acoustic_survey import slant_time, locate_on_surface

class AcousticSurveyTestCase(unittest.TestCase):
    """
    Tests for the acoustic survey module.
    """
    def test_slant_time(self):
        """
        Should calculate travel time as a straight-line distance.
        """
        # should handle a single source, receiver set
        sx = 0
        sy = 0
        sz = 0
        rx = 10
        ry = 5
        rz = 3
        v = 1.5
        t = slant_time(sx, sy, sz, rx, ry, rz, v)
        self.assertEqual(t, 7.71722460186015)
        # should handle multiple sources and a single receiver
        sx = np.asarray([0, 1])
        t = slant_time(sx, sy, sz, rx, ry, rz, v)
        self.assertEqual(len(t), 2)
        self.assertEqual(t[0], 7.71722460186015)
        self.assertEqual(t[1], 7.149203529842406)
        # should hangle multiple sources and multiple recievers
        rx = np.asarray([10, 15])
        t = slant_time(sx, sy, sz, rx, ry, rz, v)
        self.assertEqual(len(t), 2)

    def test_locate_on_surface(self):
        """
        Should find the position of a receiver.
        """
        # Test surface
        x = np.linspace(0, 5, 6)
        y = np.linspace(0, 5, 6)
        zz =  3. + 2. * np.random.rand(len(x), len(y))
        # Synthetic traveltimes
        sx = np.asarray([0, 1, 2, 3, 4, 5])
        sy = np.asarray([5, 4, 3, 2, 1, 0])
        sz = np.asarray([0.5, 0.5, 0.2, 0.1, 0.2, 0.4])
        rx0 = x[3] 
        ry0 = y[3]
        rz0 = zz[3, 3]
        v = 1.50
        twt = 2. * slant_time(sx, sy, sz, rx0, ry0, rz0, v)
        # Run the locator
        rx, ry, rz, rms = locate_on_surface(sx, sy, sz, twt, x, y, zz, v=v)
        self.assertEqual(rx0, rx)
        self.assertEqual(ry0, ry)
        self.assertEqual(rz0, rz)
        self.assertEqual(rms, 0.0)


    
def suite():
    return unittest.makeSuite(AcousticSurveyTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
