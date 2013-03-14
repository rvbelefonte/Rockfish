"""
Test case for the two2three module.
"""
import unittest
import numpy as np
from rockfish.tomography.model import VM, readVM
from rockfish.utils.loaders import get_example_file
from rockfish.tomography.two2three import project_point,\
        project_model_points, project_layer_velocities, two2three

TEST_MODELS = ['benchmark2d.vm']


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

    def test_project_model_points(self):
        """
        Should map 2d model points to points in the 3d model.
        """
        phi = 30.
        vm3d = VM(r1=(100, 200, 0), r2=(500, 300, 30), dx=5, dy=5, dz=1)
        for model in TEST_MODELS:
            vm2d = readVM(get_example_file(model))
            # default should return valid coordinates
            x = project_model_points(vm2d, vm3d, phi)
            self.assertTrue(np.min(x) >= vm2d.r1[0])
            self.assertTrue(np.max(x) <= vm2d.r2[0])
            # indices = True should return valid indices
            ix = project_model_points(vm2d, vm3d, phi)
            self.assertTrue(np.min(ix) >= 0)
            self.assertTrue(np.max(ix) <= vm2d.nx)

    def dev_project_layer_velocities(self):
        """
        Should map 2D model velocities to a 3D model.
        """
        # Create a simple 2D model with sl set to layer IDs
        vm2d = VM(r1=(-2, 0, -2), r2=(50, 0, 30), dx=1, dy=1, dz=1)
        z = 3 + vm2d.x * 0.1
        vm2d.insert_interface([[_z] for _z in z])
        vm2d.insert_interface(10)
        z = 22 + vm2d.x * -0.1
        vm2d.insert_interface([[_z] for _z in z])
        vm2d.sl = vm2d.layers
        # Project into a 3D model
        phi = 30
        vm3d = VM(r1=(10, 1, -2), r2=(20, 20, 30), dx=1, dy=1, dz=1)
        vm3d.insert_interface(5)
        vm3d.insert_interface(10)
        vm3d.insert_interface(20)
        for ilyr in range(vm2d.nr + 1):
            project_layer_velocities(vm2d, vm3d, phi, ilyr)
        # Layers should only include values from the same 2d layers
        for ilyr in range(vm2d.nr + 1):
            idx = np.nonzero(vm3d.layers == ilyr)
            self.assertEqual(vm3d.sl[idx].min(), ilyr)


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
    return unittest.makeSuite(two2threeTestCase, 'dev')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
