"""
Test suite for the raygeometry module.
"""
import unittest
import numpy as np
from rockfish.tomography.model import VM
from rockfish.tomography.raygeometry import assign_points_to_layers,\
        get_indices_near_piercing, get_piercing_points, distance,\
        get_path_in_layer


class raygeometryTestCase(unittest.TestCase):
    """
    Test cases for the raygeometry module.
    """
    def setUp(self):
        """
        Build test models
        """
        # Create a 3D model with three layers (2 boundaries)
        r1 = (0, 0, 0)
        r2 = (20, 20, 30)
        self.vm = VM(r1=r1, r2=r2)
        self.vm.insert_interface(5)
        self.vm.insert_interface(10)
        # Define a path for the test case
        self.pi = [0, 1, 1, 2, 2, 2, 1, 1, 0]
        self.px = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.py = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.pz = [1, 6, 8, 11, 12, 11, 8, 6, 2]
        self.path = zip(self.px, self.py, self.pz, self.pi)

    def test_distance(self):
        """
        Should calculate cartesian distance
        """
        # should work in 2D
        p0 = (0, 0)
        p1 = (0, 1.)
        self.assertEqual(distance(p0, p1), 1.)
        # should work in 3D
        p0 = (0, 0, 0)
        p1 = (0, 0, 1)
        self.assertEqual(distance(p0, p1), 1.)

    def test_assign_points_to_layers(self):
        """
        Should assign a layer index to each point.
        """

        # Should label each point with its layer index
        pi = assign_points_to_layers(self.vm, self.px, self.py, self.pz)
        for _pi0, _pi in zip(self.pi, pi):
            self.assertEqual(_pi0, _pi)

    def test_get_indices_near_piercing(self):
        """
        Should find indices for points near a piercing points.
        """
        # should get indices if path crosses layer
        iref = 0
        ip = get_indices_near_piercing(self.pi, iref)
        self.assertEqual(len(ip), 2)
        self.assertEqual(ip[0][0], 0)
        self.assertEqual(ip[0][1], 1)
        self.assertEqual(ip[1][0], 8)
        self.assertEqual(ip[1][1], 7)
        # should return empty array if path does not cross interface
        pi = 999 * np.ones(len(self.pi))
        ip = get_indices_near_piercing(pi, iref)
        self.assertEqual(len(ip), 0)
        # should just return points on the downward leg
        ip = get_indices_near_piercing(self.pi, iref, downward=True,
                                       upward=False)
        self.assertEqual(len(ip), 1)
        self.assertEqual(ip[0][0], 0)
        self.assertEqual(ip[0][1], 1)
        # should just return points on the upward leg
        ip = get_indices_near_piercing(self.pi, iref, downward=False,
                                       upward=True)
        self.assertEqual(len(ip), 1)
        self.assertEqual(ip[0][0], 8)
        self.assertEqual(ip[0][1], 7)

    
    def test_get_piercing_points(self):
        """
        Should find coordinates of piercing points.
        """
        iref = 0
        # indices of points near the piercing points
        ip = get_indices_near_piercing(self.pi, iref)
        # should find piercing points if path crosses interface
        pp = get_piercing_points(self.vm, iref, self.px, self.py, self.pz,
                                 ip)
        self.assertEqual(pp[0, 0], 1.)
        self.assertEqual(pp[0, 1], 1.8)
        self.assertEqual(pp[0, 2], 5.)
        self.assertEqual(pp[1, 0], 1.)
        self.assertEqual(pp[1, 1], 8.75)
        self.assertEqual(pp[1, 2], 5.)
        # should return empty array if path does not cross interface
        px = np.ones(len(self.pi))
        py = np.linspace(1, 9, len(self.pi))
        pz = 12 * np.ones(len(self.pi))
        pi = assign_points_to_layers(self.vm, px, py, pz)
        ip = get_indices_near_piercing(pi, iref)
        pp = get_piercing_points(self.vm, 0, px, py, pz, ip)
        self.assertEqual(len(pp), 0)
        # should just return points on the downward leg
        ip = get_indices_near_piercing(self.pi, iref, downward=True,
                                       upward=False)
        pp = get_piercing_points(self.vm, 0, self.px, self.py, self.pz, ip)
        self.assertEqual(pp[0, 0], 1.)
        self.assertEqual(pp[0, 1], 1.8)
        self.assertEqual(pp[0, 2], 5.)
        # should just return points on the upward leg
        ip = get_indices_near_piercing(self.pi, iref, downward=False,
                                       upward=True)
        pp = get_piercing_points(self.vm, 0, self.px, self.py, self.pz, ip)
        self.assertEqual(pp[0, 0], 1.)
        self.assertEqual(pp[0, 1], 8.75)
        self.assertEqual(pp[0, 2], 5.)

        
    def test_path_in_layer(self):
        """
        Should get coordinates for portion of path in layer.
        """
        down_npts = [2, 4, 5]
        up_npts = [2, 4, 0]
        for ilyr in range(3):
            d, u = get_path_in_layer(self.vm, ilyr, self.px, self.py, self.pz)
            self.assertEqual(len(d), down_npts[ilyr])


def suite():
    return unittest.makeSuite(raygeometryTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')


