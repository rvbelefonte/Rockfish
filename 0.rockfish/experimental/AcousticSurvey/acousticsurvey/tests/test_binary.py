"""
Test suite for :mod:`acousticsurvey.binary`.
"""
import unittest
from acousticsurvey.binary import float2bin, bin2float, mutate, \
    crossover

class binaryTestCase(unittest.TestCase):
    """
    Test cases for :mod:`acousticsurvey.binary`.
    """
    def test_float2bin_and_bin2float(self):
        """
        Functions should reverse each other.
        """
        val0 = 123.323
        bv, pow10, _ = float2bin(val0)
        val1 = bin2float(bv, pow10)
        self.assertAlmostEqual(val0, val1, 3)
        # should also handle negative numbers
        val0 = -123.323
        bv, pow10, sign = float2bin(val0)
        val1 = bin2float(bv, pow10, sign)
        self.assertAlmostEqual(val0, val1, 3)


    def test_mutate(self):
        """
        Should change a single value.
        """
        val0 = 123.323
        val1 = mutate(val0)
        self.assertNotEqual(val0, val1)

    def test_crossover(self):
        """
        Should mix two values.
        """
        # Crossing two indentical values should produce the same value
        val0 = 123.323
        val1 = crossover(val0, val0)
        self.assertAlmostEqual(val0, val1, 3)
        # Crossing two different values should produce a new value
        val1 = 992.123
        val2 = crossover(val0, val1)
        self.assertNotEqual(val0, val2)

def suite():
    return unittest.makeSuite(binaryTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
