"""
Test cases for the anisotropy model. 
"""
import os
import unittest
import numpy as np
from rockfish.equations.anisotropy import transverse

class anisotropyTestCase(unittest.TestCase):
    """
    Test cases for the anisotropy module.
    """
    def test_transverse(self):
        """
        Should calculate wavespeed for transvere anisotropy.
        """
        # Should calculate correct values
        theta = [0, 45, 90, 135, 180]
        V0 = [10.5, 8.5, 8.5, 6.5, 10.5]
        V = transverse(theta, 8.5, 1, 1, 1, 1)
        for _v0, _v in zip(V0, V):
            self.assertEqual(_v, _v0)

        # Should return a matrix with shape (len(theta), N0, N1, ..., N4)
        a = np.meshgrid([8.5], [1], [1], [1], [1], indexing='ij')
        V = transverse(theta, *a)
        self.assertEqual(type(V), list)
        self.assertEqual(len(V), len(theta))
        self.assertEqual(a[0].shape, V[0].shape)
        for _v0, _v in zip(V0, np.asarray(V).flatten()):
            self.assertEqual(_v, _v0)


def suite():
    return unittest.makeSuite(anisotropyTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')        
