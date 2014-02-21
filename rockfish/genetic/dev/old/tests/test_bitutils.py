"""
Test suite for the bitutils module
"""
import numpy as np
import unittest
from rockfish.genetic.bitutils import BitSet

class BitSetTestCase(unittest.TestCase):
    """
    Test suite for the BitSet class
    """
    def test___init__(self):
        """
        Should initialize a new BitSet instance
        """
        f0 = np.random.rand(100, 2)
        bs = BitSet(f0)

        self.assertEqual(f0.shape, bs.float.shape)
        self.assertEqual(f0.shape, bs.bin.shape)

        for _f0, _f1 in zip(f0.flatten(), bs.float.flatten()):
            self.assertEqual(_f0, _f1)


    def dev_idx2flat(self):
        """
        Should take multidimensional matrix indices and return indices in
        the flattened array version of the matrix
        """
        f0 = np.random.rand(100, 5)
        bs = BitSet(f0)

        i = bs.idx2flat((2,))
        self.assertEqual(i.shape, (5, ))
        
        i = bs.idx2flat((2,), (50,))
        self.assertEqual(i.shape, (10, ))


def suite():
    return unittest.makeSuite(BitSetTestCase, 'dev')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')



