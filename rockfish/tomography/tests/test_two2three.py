"""
Test case for the two2three module.
"""
import unittest
import numpy as np
from rockfish.tomography.model import readVM
from rockfish.utils.loaders import get_example_file
from rockfish.tomography.two2three import project_point, two2three

TEST_MODELS = ['goc_l26.15.00.vm', 'CRAnis.NorthEast.00.00.vm']


class two2threeTestCase(unittest.TestCase):
    """
    Test cases for the two2three module.
    """
    def test_project_point(self):
        """
        Should find a radius and coordinates of the projection
        of a point onto a line.
        """
        theta = np.pi/4
        # points should be equal for theta=45 and x=y
        x = 10
        y = 10
        r, xp, yp = project_point(x, y, theta)
        self.assertAlmostEqual(x, xp, 10)
        self.assertAlmostEqual(y, yp, 10)
        # angle of opposite side should be orthogonal to line
        x = 10
        y = 5
        r, xp, yp = project_point(x, y, theta)
        phi = np.arctan2(yp - y, xp - x)
        self.assertAlmostEqual(theta + np.pi/2, phi, 5)
        # should also work on numpy arrays
        x = np.asarray([5, 10, 15])
        y = np.asarray([1, 1, 1])
        r, xp, yp = project_point(x, y, theta)
        for i in range(0, len(x)):
            _r, _xp, _yp = project_point(x[i], y[i], theta)
            self.assertEqual(r[i], _r)
            self.assertEqual(xp[i], _xp)
            self.assertEqual(yp[i], _yp)

    def test_two2three(self, sol=(0, 0), theta=39):
        """
        Should create a 3D model from a 2D model.
        """
        for test_model in TEST_MODELS:
            vm2d = readVM(get_example_file(test_model))
            # calculate example endpoints
            line_len = np.sqrt((vm2d.r2[0] - vm2d.r1[0]) ** 2 +\
                              (vm2d.r2[1] - vm2d.r1[1]) ** 2)
            eol = (sol[0] + line_len * np.cos(np.deg2rad(theta)),
                   sol[1] + line_len * np.sin(np.deg2rad(theta)))
            # should create 3d model
            vm3d = two2three(vm2d, sol, eol, dx=1, dy=1)
            # check bounds
            self.assertAlmostEqual(vm3d.r1[0], sol[0], 0)
            self.assertAlmostEqual(vm3d.r1[1], sol[1], 0)
            self.assertAlmostEqual(vm3d.r2[0], eol[0], 0)
            self.assertAlmostEqual(vm3d.r2[1], eol[1], 0)
            # spot check some values
            for iref in range(0, vm3d.nr):
                self.assertAlmostEqual(vm3d.rf[iref].min(),
                                       vm2d.rf[iref].min(), 1)
                self.assertAlmostEqual(vm3d.rf[iref].max(),
                                       vm2d.rf[iref].max(), 1)
            
    def test_two2three_nonzero_origin(self):
        """
        Should take a non-zero orgin.
        """
        self.test_two2three(sol=(343, 1085), theta=39)


def suite():
    return unittest.makeSuite(two2threeTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
