"""
Test suite for the utils module
"""

import unittest
import numpy as np
from rockfish.genetic.utils import float2bin, bin2float, crossover,\
        mutate

class utilsTestCase(unittest.TestCase):


    def test_float2bin(self):
        """
        Should convert a float to binary and back
        """
        # should take single values and return len=1 array 
        for f0 in [9000.12345, 0.012345]:
            b0, pow0 = float2bin(f0, length=32)
            self.assertTrue(isinstance(b0[0], str))
            self.assertEqual(len(b0), 1)
            self.assertEqual(len(pow0), 1)
            self.assertEqual(len(b0[0]), 32)

        # should take a single string instance
        f1 = bin2float(b0, pow0)
        self.assertEqual(len(f1), 1)
        self.assertAlmostEqual(f0, f1[0], 3)

    def test_float2bin_array(self):
        """
        Should convert arrays to binary and back
        """
        f0 = np.asarray([999.1234, 9.1234, 0.01234, -99.123, 1.e-33])
        b, s = float2bin(f0)

        self.assertEqual(len(b), len(f0))
        self.assertEqual(len(s), len(f0))

        for _b in b:
            self.assertTrue(isinstance(_b, str))

        f1 = bin2float(b, s)

        for _f0, _f1 in zip(f0, f1):
            self.assertAlmostEqual(_f0, _f1, 4)


    def test_crossover(self):
        """
        Should perform binary crossover with two numbers
        """
        # TODO not sure how to test this: assertNotEqual will be False when
        # the random bit in crossover is 0.  For now, this test just makes
        # sure the sizes are correct

        # should work on scalars
        f1_0, f2_0 = 500. * np.random.rand(2)
        f1_1, f2_1 = crossover(f1_0, f2_0)
        self.assertFalse(hasattr(f1_1, '__iter__'))
        self.assertFalse(hasattr(f2_1, '__iter__'))

        # should work on arrays
        f1_0, f2_0 = 500 * np.random.rand(2, 5)
        f1_1, f2_1 = crossover(f1_0, f2_0)
        self.assertEqual(len(f1_1), 5)
        self.assertEqual(len(f2_1), 5)

    def test_mutate(self):
        """
        Should perform binary mutation
        """
        # should not change shape of 1d array
        f0 = np.random.rand(100)
        f1 = mutate(f0)
        self.assertEqual(f0.shape, f1.shape)

        # should mutate all values
        for _f0, _f1 in zip(f0, f1):
            self.assertNotEqual(_f0, _f1)

        # should take multi-dimensional arrays
        f0 = np.random.rand(10, 3)
        f1 = mutate(f0)
        self.assertEqual(f0.shape, f1.shape)
        for i in range(10):
            for j in range(3):
                    self.assertNotEqual(f0[i, j], f1[i, j])

        # FIXME?? fails on np.log10(0) in power calc. in float2bin()
        ## should not produce NaNs
        f0 = np.round(np.random.rand(1000))
        f1 = mutate(f0)
        self.assertEqual(len(np.nonzero(np.isnan(f1))[0]), 0)

    def test_reshape(self):
        """
        Reshaping arrays should be reversable
        """
        f0 = np.random.rand(10, 3)
        shape = f0.shape

        f1 = f0.flatten()
        f1 = f1.reshape(shape)

        self.assertEqual(f0.shape, f1.shape)
        for i in range(10):
            for j in range(3):
                    self.assertEqual(f0[i, j], f1[i, j])


def suite():
    return unittest.makeSuite(utilsTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

