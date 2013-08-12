"""
Test cases for the parameters module.
"""
import os
import unittest
import numpy as np
from rockfish.experimental.inverse.parameters import meshgrid_from_ranges


class parametersTestCase(unittest.TestCase):
    """
    Test cases for the parameters modules.
    """
    def test_meshgrid_from_ranges(self):
        """
        Should build a matrix of all unique parameter combinations
        """
        # Should build a matrix for 3 parameter ranges
        n0 = 2
        n1 = 4
        n2 = 6
        aranges = [(1, 3, n0),
                   (10, 15, n1),
                   (20, 15, n2)]
        a0 = np.zeros((n1, n0, n2))
        a1 = np.zeros((n1, n0, n2))
        a2 = np.zeros((n1, n0, n2))
        for i, _a0 in enumerate(np.linspace(*aranges[0])):
            for j, _a1 in enumerate(np.linspace(*aranges[1])):
                for k, _a2 in enumerate(np.linspace(*aranges[2])):
                    a0[j, i, k] = _a0
                    a1[j, i, k] = _a1
                    a2[j, i, k] = _a2
        b0, b1, b2 = meshgrid_from_ranges(aranges, method=np.linspace)
        for i in range(n0):
            for j in range(n1):
                for k in range(n2):
                    self.assertEqual(a0[j, i, k], b0[j, i, k])
                    self.assertEqual(a1[j, i, k], b1[j, i, k])
                    self.assertEqual(a2[j, i, k], b2[j, i, k])


def suite():
    return unittest.makeSuite(parametersTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
