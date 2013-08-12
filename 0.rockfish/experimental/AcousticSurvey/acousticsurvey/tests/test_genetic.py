"""
Test suite for :mod:`acousticsurvey.genetic`
"""
import unittest
import numpy as np
from acousticsurvey.genetic import Environment
from acousticsurvey.traveltimes import slant_time

class geneticTestCase(unittest.TestCase):
    """
    Test cases for:m od:`obslocate`
    """
    def setUp(self):
        """
        Load benchmark data.
        """
        # Load benchmark data
        f = open('Pw.xyt')
        self.sx = []
        self.sy = []
        for line in f:
            _sx, _sy, _t = [float(v) for v in line.split()]
            self.sx.append(_sx)
            self.sy.append(_sy)
        f.close()
        self.sz = 6*np.ones(len(self.sx))
        # Set a receiver position
        self.rx = np.mean(self.sx)
        self.ry = np.mean(self.sy)
        self.rz = 2000.
        # Set a velocity
        self.v = 1500.
        # Compute synthetic travel times
        self.t = []
        for _sx, _sy, _sz in zip(self.sx, self.sy, self.sz):
            self.t.append(slant_time(_sx, _sy, _sz, 
                                     self.rx, self.ry, self.sz, self.v))

    def test_init(self):
        """
        Should create a new population instance.
        """
        # Should initialize with just source positions and travel
        # times
        env = Environment(self.sx, self.sy, self.sz, self.t)

    def test_evolve(self):
        """
        Should recover position used to produce synthethic data.
        """
        env = Environment(self.sx, self.sy, self.sz, self.t, velocity=1500)
        result = env.evolve(max_generations=100, plot=True)

def suite():
    return unittest.makeSuite(geneticTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

