"""
Test cases for the geometry module
"""
import unittest
import numpy as np
import matplotlib.pyplot as plt
from rockfish.tomography.model import VM
from rockfish.tomography.geometry.raypaths import assign_points_to_layers,\
        split_downup, get_points_in_layer, find_line_intersection,\
        _trim_path_ends_to_layer, insert_intersections,\
        split_path_at_interface_intersections, resample_path

PLOT = False

class geometryTestCase(unittest.TestCase):
    """
    Test cases for the geometry module
    """

    def setUp(self):
        """
        Build a test VM model
        """
        self.vm = VM(r1=(0, 0, 0), r2=(100, 100, 50), dx=5, dy=5, dz=5)

        self.vm.define_constant_layer_velocity(0, 1.5)
        self.vm.insert_interface(3)
        self.vm.insert_interface(10)

        # dipping layer
        dzdx = 0.1
        dzdy = 0.1
        rf = 25 * np.ones((self.vm.nx, self.vm.ny))
        for ix in range(self.vm.nx):
            for iy in range(self.vm.ny):
                rf[ix, iy] += dzdx * (ix * self.vm.dx)
                rf[ix, iy] += dzdy * (iy * self.vm.dy)
        #XXX self.vm.insert_interface(rf)

        self.vm.insert_interface(30)

        ray0 = [#x, y, z, ilyr, direction
                [2, 2, 1, 0, 1],
                [22, 22, 25, 2, 1],
                [23, 23, 28, 2, 1],
                [40, 40, 44, 3, 1],
                [41, 41, 46, 3, 0],
                [62, 62, 19, 2, -1],
                [80, 80, 5, 1, -1]]

        ray1 = [#x, y, z, ilyr, direction
                [5, 5, 2, 0, 1],
                [60, 60, 45, 3, 1]]
        
        ray2 = [#x, y, z, ilyr, direction
                [5, 5, 45, 3, -1],
                [60, 60, 2, 0, -1]]

        # rays
        self.raypaths = np.asarray([ray0, ray1, ray2])

        self.vm.write('test.vm')

    def plot_init(self):
        """
        setup should make a test model
        """
        if not PLOT:
            return

        fig = plt.figure()
        ax = fig.add_subplot(111)

        y0 = 50
        vm = self.vm.slice_along_xy_line(
            self.vm.x, y0 * np.ones(self.vm.nx))
        vm.plot_layers(ax=ax)

        for path in self.raypaths:
            _path = np.asarray(path)
            ax.plot(_path[:, 0], _path[:, 2], '.-c')

        plt.title('test_init: Test model at y = {:}'.format(y0))

        plt.show()

    def test_assign_points_to_layers(self):
        """
        Should determine what layers a series of points are in
        """
        pi = []
        for path in self.raypaths:
            _path = np.asarray(path)
            _pi = assign_points_to_layers(self.vm, _path[:, 0], _path[:, 1],
                                          _path[:, 2])
            pi.append(_pi)

            for i0, i1 in zip(_path[:, 3], _pi):
                self.assertEqual(i0, i1)

        if PLOT:
            fig = plt.figure()
            ax = fig.add_subplot(111)

            y0 = 50
            vm = self.vm.slice_along_xy_line(
                self.vm.x, y0 * np.ones(self.vm.nx))
            vm.plot(ax=ax, show_grid=True)

            for i in range(len(pi)):
                path = np.asarray(self.raypaths[i])

                ax.plot(path[:, 0], path[:, 2], '-c')
                ax.scatter(path[:, 0], path[:, 2], c=pi[i],
                           s=50)

            plt.title('test_assign_points_to_layers: nodes colored by layer')
            plt.show()

    def test_get_points_in_layer(self):
        """
        Should return points within a layer
        """
        for path in self.raypaths:
            for ilyr in range(self.vm.nr):
                _path = np.asarray(path)
                px, py, pz = _path[:, 0], _path[:, 1], _path[:, 2]
            
                d, u = split_downup(px, py, pz)
                for p in [d, u]:
                    px, py, pz = p[:, 0], p[:, 1], p[:, 2]


                    pi = assign_points_to_layers(self.vm, px, py, pz)
                    pi0 = np.nonzero(pi == ilyr)[0]

                    # should only return points that fall within a layer
                    px1, py1, pz1, pi1 = get_points_in_layer(
                        self.vm, ilyr, px, py, pz, overlap=False)

                    self.assertEqual(len(pi0), len(px1))
                    self.assertEqual(len(pi0), len(py1))
                    self.assertEqual(len(pi0), len(pz1))
                    self.assertEqual(len(pi0), len(pi1))
                    
                    # should include neighboring points
                    px2, py2, pz2, pi2 = get_points_in_layer(
                        self.vm, ilyr, px, py, pz, overlap=True)
                    self.assertGreaterEqual(len(px2), len(px1))
                    self.assertGreaterEqual(len(py2), len(py1))
                    self.assertGreaterEqual(len(pz2), len(pz1))
                    self.assertGreaterEqual(len(pi2), len(pi1))

                    # should be empty or have more than 1 point
                    self.assertNotEqual(len(px2), 1)
                    self.assertNotEqual(len(py2), 1)
                    self.assertNotEqual(len(pz2), 1)
                    self.assertNotEqual(len(pi2), 1)

                    if PLOT:
                        fig = plt.figure()
                        ax = fig.add_subplot(111)
                        self.vm.plot(ax=ax)

                        #ax.scatter(px, pz, c=pi, marker='.', s=30, zorder=0)
                        ax.plot(px, pz, '.-k', lw=5, zorder=1)
                        ax.plot(px1, pz1, '.-m', lw=4, zorder=2)
                        ax.plot(px2, pz2, '.-c', lw=1, zorder=3)

                        plt.title('test_get_points_in_layer: ilyr={:}'\
                                  .format(ilyr))

                        plt.show()

    def test_split_downup(self):
        """
        Should split path into down-going and up-coming segments
        """
        down = []
        up = []
        for path in self.raypaths:
            _path = np.asarray(path)
            px, py, pz = _path[:, 0], _path[:, 1], _path[:, 2]

            d, u = split_downup(px, py, pz)
            down.append(d)
            up.append(u)

            ibot = np.nonzero(_path[:, 4] == 0)
            idown = np.append(np.nonzero(_path[:, 4] == 1), ibot)
            iup = np.append(ibot, np.nonzero(_path[:, 4] == -1))

            self.assertEqual(len(d), len(idown))
            self.assertEqual(len(u), len(iup))

        if PLOT:
            fig = plt.figure()
            ax = fig.add_subplot(111)

            self.vm.plot(ax=ax, ir=False, ij=False, rf=False) 

            for i in range(len(self.raypaths)):
                path = np.asarray(self.raypaths[i])

                ax.plot(path[:, 0], path[:, 2], '-k', lw=5)

                ax.plot(down[i][:, 0], down[i][:, 2], '-r')
                ax.plot(up[i][:, 0], up[i][:, 2], '-g')

            plt.title('test_split_downup: up and down paths') 
            plt.show()

    def test_find_line_intersection(self):
        """
        Should find where a point crosses an interface
        """
        p0 = [1, 2, 1]
        p1 = [82, 40, 40]
        for iref in [0, 1, 2]:

            x, y, z = find_line_intersection(self.vm, iref, p0, p1)

            ix = self.vm.x2i(x)
            iy = self.vm.y2i(y)
            z0 = self.vm.rf[iref][ix, iy]

            self.assertAlmostEqual(z, z0, 1)

            if PLOT:
                fig = plt.figure()
                ax = fig.add_subplot(111)

                self.vm.plot(ax=ax, show_grid=True)

                ax.plot([p0[0], p1[0]], [p0[2], p1[2]], '.-c')
                ax.plot(x, z, '.w')

                plt.title('test_find_line_intersection: iref={:}'\
                          .format(iref))

                plt.show()

    def test__trim_path_to_layer(self):
        """
        Should trim a pre-processed path to single layer
        """
        # path that crosses layer 2
        ray0 = [[1, 1, 1],
                [40, 1, 20],
                [80, 1, 40]]
        
        # path that terminates in layer 2
        ray1 = [[1, 1, 1],
                [40, 1, 20],
                [80, 1, 22]]

        # path that starts in layer 2
        ray2 = [[1, 1, 19],
                [40, 1, 20],
                [80, 1, 40]]

        # path that starts and ends in layer 2
        ray3 = [[1, 1, 19],
                [40, 1, 20],
                [80, 1, 22]]

        for ray in [ray0, ray1, ray2, ray3]:

            px = [r[0] for r in ray]
            py = [r[1] for r in ray]
            pz = [r[2] for r in ray]

            if PLOT:
                fig = plt.figure()
                ax = fig.add_subplot(111)
                self.vm.plot(ax=ax, show_grid=True)
                ax.plot(px, pz, '.-g')

            _trim_path_ends_to_layer(self.vm, px, py, pz)

            pi = assign_points_to_layers(self.vm, px, py, pz)
            for i in pi:
                self.assertEqual(i, 2)

            if PLOT:
                ax.plot(px, pz, '.-m')
                plt.show()

    def test_insert_intersections(self):
        """
        Should add layer intersections
        """
        for path in self.raypaths[0:1]:
            _path = np.asarray(path)
            px, py, pz = _path[:, 0], _path[:, 1], _path[:, 2]

            for duplicate in [True, False]:
                if PLOT:
                    fig = plt.figure()
                    ax = fig.add_subplot(111)
                    plt.title('duplicate = {}'.format(duplicate))
                    self.vm.plot(ax=ax, show_grid=True)
                    ax.plot(px, pz, '.-g', markersize=10, lw=3)

                px, py, pz, pi = insert_intersections(self.vm, px, py, pz,
                                                      duplicate=duplicate)

                if PLOT:
                    ax.plot(px, pz, '.-m')
                    plt.show()
                
                self.assertEqual(len(px), len(pi))
                self.assertEqual(len(py), len(pi))
                self.assertEqual(len(pz), len(pi))

    def test_split_path_at_interface_intersections(self):
        """
        Should split a path into layer segments 
        """
        sym = ['.-r', '.-c', '.-m', '.-w']
        for path in self.raypaths:
            _path = np.asarray(path)
            px, py, pz = _path[:, 0], _path[:, 1], _path[:, 2]

            _px, _, _pz, _ = insert_intersections(self.vm, px, py, pz)
            if PLOT:
                fig = plt.figure()
                ax = fig.add_subplot(111)
                self.vm.plot(ax=ax, show_grid=True)
                ax.plot(px, pz, '.-g', markersize=20, lw=5)
                ax.plot(_px, _pz, '.-k', markersize=10, lw=3)

            segments = split_path_at_interface_intersections(
                self.vm, px, py, pz)

            if PLOT:
                for i, segments in enumerate(segments):
                    for p in segments:
                        if len(p) == 0:
                            continue

                        ax.plot(p[:, 0], p[:, 2], sym[i])
                
                plt.show()

            self.assertEqual(len(segments), self.vm.nr + 1)

    def test_resample_path(self):
        """
        Should interpolate path
        """
        if PLOT:
            fig = plt.figure()
            ax = fig.add_subplot(111)

        for path in self.raypaths:
            _path = np.asarray(path)
            px, py, pz = _path[:, 0], _path[:, 1], _path[:, 2]

            pxi, pyi, pzi = resample_path(px, py, pz, dx=1)

            if PLOT:
                self.vm.plot(ax=ax, show_grid=True)
                ax.plot(px, pz, '.-g', markersize=20, lw=5)
                ax.plot(pxi, pzi, '.-k', markersize=10, lw=3)

        if PLOT:
            plt.show()



def suite():
    return unittest.makeSuite(geometryTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
