"""
Test suite for the rockfish.plotting.util
"""
import unittest
from rockfish.plotting.util import MPL_COLORS, get_mpl_color


class utilTestCase(unittest.TestCase):
    """
    Test cases for the util module
    """
    def test_get_mpl_color(self):
        """
        Should return a color name.
        """
        # should return color at given index when n is < len(colors)
        for n in range(0, len(MPL_COLORS)):
            self.assertEqual(MPL_COLORS[n], get_mpl_color(n))
        # should cycle colors by default
        _n = 3
        n = len(MPL_COLORS) + _n
        self.assertEqual(MPL_COLORS[_n], get_mpl_color(n))
        # cycle=False should give last color in the list
        _n = 3
        n = len(MPL_COLORS) + _n
        self.assertEqual(MPL_COLORS[-1], get_mpl_color(n, cycle=False))


def suite():
    return unittest.makeSuite(utilTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
