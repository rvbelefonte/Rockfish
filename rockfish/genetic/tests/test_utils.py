"""
Test suite for the utils module
"""

import unittest
import numpy as np
from rockfish.genetic.utils import float2bin, bin2float, crossover, mutate

class utilsTestCase(unittest.TestCase):

    def test_float2bin(self):
        """
        Should convert a float to binary and back
        """
        # should take single values and return len=1 array 
        f0 = 9.12345
        b = float2bin(f0, length=32)
        self.assertTrue(isinstance(b[0], str))
        self.assertEqual(len(b), 1)
        self.assertEqual(len(b[0]), 32)

        # should take a single string instance
        f1 = bin2float(b)
        self.assertEqual(len(f1), 1)
        self.assertAlmostEqual(f0, f1[0], 6)

        # should work on arrays
        f0 = np.random.rand(100)
        b = float2bin(f0)
        self.assertEqual(len(b), 100)

        for _b in b:
            self.assertTrue(isinstance(_b, str))
            self.assertEqual(len(_b), 32)

        f1 = bin2float(b)

        for _f0, _f1 in zip(f0, f1):
            self.assertAlmostEqual(_f0, _f1, 6)

    def test_crossover(self):
        """
        Should perform binary crossover with two numbers
        """
        # TODO not sure how to test this: assertNotEqual will be False when
        # the random bit in crossover is 0.  For now, this test just makes
        # sure the sizes are correct

        # should work on scalar individuals
        f1_0, f2_0 = 500 * np.random.rand(2)
        f1_1, f2_1 = crossover(f1_0, f2_0)
        self.assertFalse(hasattr(f1_1, '__iter__'))
        self.assertFalse(hasattr(f2_1, '__iter__'))

        # should work on arrays individuals
        f1_0, f2_0 = 500 * np.random.rand(2, 5)
        f1_1, f2_1 = crossover(f1_0, f2_0)
        self.assertEqual(len(f1_1), 5)
        self.assertEqual(len(f2_1), 5)

    def test_mutate(self):
        """
        Should perform binary mutation
        """
        f0 = np.random.rand(100)

        f1 = mutate(f0)

        self.assertEqual(len(f0), len(f1))

        for _f0, _f1 in zip(f0, f1):
            self.assertNotEqual(_f0, _f1)


def suite():
    return unittest.makeSuite(utilsTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

