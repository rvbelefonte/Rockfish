"""
Test cases for the vm module.
"""
import os
import unittest
import numpy as np
import copy
from rockfish.tomography.model import VM, VMGrids, readVM
from rockfish.utils.loaders import get_example_file


BENCHMARK_2D = 'benchmark2d.vm'
TEST_2D_MODELS = ['jump1d.vm']
TEST_3D_MODELS = ['pinchout3d.vm', 'cranis3d.vm']
TEST_MODELS = TEST_2D_MODELS + TEST_3D_MODELS


class VMTestCase(unittest.TestCase):
    """
    Test cases for the vmtools modules.
    """
    def test_init_empty(self):
        """
        Calling VM without any arguments should return an empty instance.
        """
        vm = VM()
        for attr in ['dx', 'dy', 'dz', 'r1', 'r2', 'sl', 'rf',
                     'ir', 'ij']:
            self.assertTrue(hasattr(vm, attr))

    def compare_to_benchmark(self, vm):
        """
        Compare a vm model to the benchmark model.

        Values are as read by read_vm.m
        """
        # Should have same header values as read by vm_read.m
        self.assertEqual(vm.nx, 1041)
        self.assertEqual(vm.ny, 1)
        self.assertEqual(vm.nz, 506)
        self.assertAlmostEqual(vm.r1[2], -0.5, places=2)
        self.assertAlmostEqual(vm.r2[0], 260.00, places=2)
        self.assertAlmostEqual(vm.dx, 0.25, places=2)
        self.assertAlmostEqual(vm.dy, 1.00, places=2)
        self.assertAlmostEqual(vm.dz, 0.1, places=2)
        # Should have same slowness values as read by vm_read.m
        # Grid values should be ordered as [x][y][z]
        self.assertAlmostEqual(vm.sl[0][0][0],  3.0030, places=4)
        self.assertAlmostEqual(vm.sl[-1][0][0], 3.0030, places=4)
        self.assertAlmostEqual(vm.sl[-1][0][0], 3.0030, places=4)
        self.assertAlmostEqual(vm.sl[49][0][19], 0.6667, places=4)
        self.assertAlmostEqual(vm.sl[69][0][199], 0.1223, places=4)
        # Should have same interface values as read by vm_read.m
        # Interface values should be ordered as [iref][x][y]
        self.assertAlmostEqual(vm.rf[0][0][0], 0.0000, places=4)
        self.assertAlmostEqual(vm.rf[0][899][0], -0.1570, places=4)
        self.assertAlmostEqual(vm.rf[1][899][0], -0.0570, places=4)

    def test_read_write_vm(self):
        """
        Reading and writing in the VM format should not change data.
        """
        # read data from the disk file
        vmfile = get_example_file(BENCHMARK_2D)
        vm = readVM(vmfile)
        # check values
        self.compare_to_benchmark(vm)
        # write it to another file
        tmp = 'temp.vm'
        vm.write(tmp)
        # read these data back in
        vm = readVM(tmp)
        # check values
        self.compare_to_benchmark(vm)
        # clean up
        os.remove(tmp)

    def test_boundary_flags(self):
        """
        Should convert boundary flags from fortran to python index conventions
        """
        for model in TEST_MODELS:
            # read anymodel with interfaces
            vm = readVM(get_example_file(model))
            # set all ir and ij flags to -1 (off)
            vm.ir = -1 * np.ones(vm.ir.shape)
            vm.ij = -1 * np.ones(vm.ij.shape)
            # reading and writing should not change flag values
            tempvm = 'temp123.vm'
            vm.write(tempvm)
            vm = readVM(tempvm)
            self.assertEqual(vm.ir.min(), -1)
            self.assertEqual(vm.ir.max(), -1)
            self.assertEqual(vm.ij.min(), -1)
            self.assertEqual(vm.ij.max(), -1)
            # cleanup
            os.remove(tempvm)

    def test_x2i(self):
        """
        Should convert between x indices and coordinates and back
        """
        r1 = (-10, -20, -30)
        r2 = (10, 20, 30)
        vm = VM(r1=r1, r2=r2, dx=1, dy=1, dz=1)
        ix = vm.x2i([vm.r1[0]])[0]
        x = vm.i2x([ix])[0]
        self.assertEqual(ix, 0)
        self.assertEqual(x, vm.r1[0])
        ix = vm.x2i([vm.r2[0]])[0]
        x = vm.i2x([ix])[0]
        self.assertEqual(ix, vm.nx - 1)
        self.assertEqual(x, vm.r2[0])

    def test_y2i(self):
        """
        Should convert between y indices and coordinates and back
        """
        r1 = (-10, -20, -30)
        r2 = (10, 20, 30)
        vm = VM(r1=r1, r2=r2, dx=1, dy=1, dz=1)
        iy = vm.y2i([vm.r1[1]])[0]
        y = vm.i2y([iy])[0]
        self.assertEqual(iy, 0)
        self.assertEqual(y, vm.r1[1])
        iy = vm.y2i([vm.r2[1]])[0]
        y = vm.i2y([iy])[0]
        self.assertEqual(iy, vm.ny - 1)
        self.assertEqual(y, vm.r2[1])

    def test_z2i(self):
        """
        Should convert between z indices and coordinates and back
        """
        r1 = (-10, -20, -30)
        r2 = (10, 20, 30)
        vm = VM(r1=r1, r2=r2, dx=1, dy=1, dz=1)
        iz = vm.z2i([vm.r1[2]])[0]
        z = vm.i2z([iz])[0]
        self.assertEqual(iz, 0)
        self.assertEqual(z, vm.r1[2])
        iz = vm.z2i([vm.r2[2]])[0]
        z = vm.i2z([iz])[0]
        self.assertEqual(iz, vm.nz - 1)
        self.assertEqual(z, vm.r2[2])

    def test_insert_interface(self):
        """
        Should insert an interface and handle setting flags correctly
        """
        # Initialize a new model
        vm = VM(r1=(0, 0, 0), r2=(50, 0, 30), dx=0.5, dy=0.5, dz=0.5)
        # Should add a new, flat interface at 10 km
        z0 = 10.
        vm.insert_interface(z0 * np.ones((vm.nx, vm.ny)))
        self.assertEqual(vm.nr, 1)
        self.assertEqual(vm.rf[0].min(), z0)
        self.assertEqual(vm.rf[0].max(), z0)
        # New interfaces should have jp=0
        self.assertEqual(vm.jp[0].min(), 0)
        self.assertEqual(vm.jp[0].max(), 0)
        # New layers should have ir and ij = index of new interface
        self.assertEqual(vm.ir[0].min(), 0)
        self.assertEqual(vm.ir[0].max(), 0)
        self.assertEqual(vm.ij[0].min(), 0)
        self.assertEqual(vm.ij[0].max(), 0)
        # Adding a new interface should increase ir and ij of deeper layers
        for z0 in [5., 15., 1., 20.]:
            vm.insert_interface(z0 * np.ones((vm.nx, vm.ny)))
            for iref in range(0, vm.nr):
                self.assertEqual(vm.ir[iref].min(), iref)
                self.assertEqual(vm.ir[iref].max(), iref)
                self.assertEqual(vm.ij[iref].min(), iref)
                self.assertEqual(vm.ij[iref].max(), iref)
        # should take a scalar value for a constant depth interface
        vm = VM(r1=(0, 0, 0), r2=(50, 0, 30), dx=0.5, dy=0.5, dz=0.5)
        z0 = 10.
        vm.insert_interface(z0)
        self.assertEqual(vm.nr, 1)
        self.assertEqual(vm.rf[0].min(), z0)
        self.assertEqual(vm.rf[0].max(), z0)

    def test_remove_interface(self):
        """
        Should remove an interface and handle setting flags correctly
        """
        # Initialize a new model
        vm = VM(r1=(0, 0, 0), r2=(50, 0, 30), dx=0.5, dy=0.5, dz=0.5)
        # Insert a set of interaces
        nr = 0
        for z0 in [1., 5., 10., 15., 20.]:
            nr += 1
            vm.insert_interface(z0 * np.ones((vm.nx, vm.ny)))
        # Should remove interface and decrease ir and ij of deeper layers
        for iref in range(0, nr):
            vm.remove_interface(0)
            nr -= 1
            self.assertEqual(vm.nr, nr)
            for _iref in range(0, vm.nr):
                self.assertEqual(vm.ir[_iref].min(), _iref)
                self.assertEqual(vm.ir[_iref].max(), _iref)
                self.assertEqual(vm.ij[_iref].min(), _iref)
                self.assertEqual(vm.ij[_iref].max(), _iref)

    def test_define_stretched_layer_velocities(self):
        """
        Should fit a 1D velocity function to a layer.
        """
        for model in TEST_MODELS:
            vm = readVM(get_example_file(model))
            # should define constant velocities within layer
            for ilyr in range(vm.nr + 1):
                vm.sl = np.nan * np.ones((vm.nx, vm.ny, vm.nz))
                vm.define_stretched_layer_velocities(ilyr, [10])
                self.assertEqual(np.nanmax(vm.sl), 1. / 10)
                self.assertEqual(np.nanmin(vm.sl), 1. / 10)

    def test_insert_layer_velocities(self):
        """
        Should insert velocities into a layer.
        """
        for model in TEST_MODELS:
            vm = readVM(get_example_file(model))
            # should define constant velocities within layer
            for ilyr in range(vm.nr + 1):
                vm.sl = np.nan * np.ones((vm.nx, vm.ny, vm.nz))
                sl = 10 * np.ones((vm.nx, vm.ny, vm.nz))
                vm.insert_layer_velocities(ilyr, sl, is_slowness=True)
                self.assertEqual(np.nanmax(vm.sl), 10)
                self.assertEqual(np.nanmin(vm.sl), 10)

    def test__get_layers(self):
        """
        Should return the layer index of each node on the grid.
        """
        for model in TEST_MODELS:
            vm = readVM(get_example_file(model))
            layers = vm._get_layers()
            # should have an entry for each node
            self.assertEqual(layers.shape, (vm.nx, vm.ny, vm.nz))
            # should have nodes in each layer
            # assuming no complete pinchouts
            self.assertEqual(len(np.unique(layers)), vm.nr + 1)

    def test_get_layer_bounds(self):
        """
        Should return arrays with layer top and bottom bounding surfaces
        """
        # Create a simple 3D model
        r1 = (0, 0, 0)
        r2 = (50, 50, 20)
        vm = VM(r1=r1, r2=r2, dx=2, dy=2, dz=0.2)
        # Should have no layers
        self.assertEqual(vm.nr, 0)
        # Should return model top and bottom
        z0, z1 = vm.get_layer_bounds(0)
        self.assertEqual(z0.shape, (vm.nx, vm.ny))
        self.assertEqual(z1.shape, (vm.nx, vm.ny))
        self.assertEqual(z0.min(), r1[2])
        self.assertEqual(z0.max(), r1[2])
        self.assertEqual(z1.min(), r2[2])
        self.assertEqual(z1.max(), r2[2])
        # Insert an interfce and get bounds again
        _z = 5.
        vm.insert_interface(_z * np.ones((vm.nx, vm.ny)))
        # Top layer should be between r1[2] and _z
        z0, z1 = vm.get_layer_bounds(0)
        self.assertEqual(z0.min(), r1[2])
        self.assertEqual(z0.max(), r1[2])
        self.assertEqual(z1.min(), _z)
        self.assertEqual(z1.max(), _z)
        # Bottom layer should be between _z and r2[2]
        z0, z1 = vm.get_layer_bounds(1)
        self.assertEqual(z0.min(), _z)
        self.assertEqual(z0.max(), _z)
        self.assertEqual(z1.min(), r2[2])
        self.assertEqual(z1.max(), r2[2])
        # Should handle pinchouts
        _z1 = 2 * _z
        iref = vm.insert_interface(_z1 * np.ones((vm.nx, vm.ny)))
        ix = vm.xrange2i(0, 25)
        vm.rf[iref, ix, :] = vm.rf[iref - 1, ix, :]
        z0, z1 = vm.get_layer_bounds(1)
        self.assertEqual(z0.min(), _z)
        self.assertEqual(z0.max(), _z)
        self.assertEqual(z1.min(), _z)
        self.assertEqual(z1.max(), _z1)

    def test_gridpoint2index(self):
        """
        Should convert between 1D and 3D grid indices.
        """
        vm = VM()
        # should return an integer index
        i0 = (10, 0, 3)
        idx = vm.gridpoint2index(*i0)
        self.assertEqual(type(idx), int)
        # should return original 3D indices
        i1 = vm.index2gridpoint(idx)
        self.assertEqual(type(i1), tuple)
        for j in range(3):
            self.assertEqual(i0[j], i1[j])

    def dev_grids(self):
        """
        Should use a separate class to manage grids 
        """
        vm = readVM(get_example_file('1d.vm'))

        # should have the grid class 
        self.assertTrue(hasattr(vm, 'grids'))
        self.assertTrue(isinstance(vm.grids, VMGrids))

        # should still have the 'sl' alias for the slowness grid
        self.assertTrue(hasattr(vm, 'sl'))
        sl0 = copy.copy(vm.sl) # save original slowness grid

        # modifying vm.sl should update vm.grids.slowness
        self.assertTrue(vm.sl is vm.grids.slowness)

        vm.sl = 999.99
        self.assertTrue(vm.grids.slowness == 999.99)

        # and visa versa
        vm.grids.slowness = 888.88
        self.assertTrue(vm.sl == 888.88)

        # grids should also have velocity and twt
        self.assertTrue(hasattr(vm.grids, 'velocity'))
        self.assertTrue(hasattr(vm.grids, 'twt'))

        # these grids should be the same shape as sl
        for n0, n1 in zip(vm.sl.shape, vm.grids.velocity.shape):
            self.assertEqual(n0, n1)
        
        for n0, n1 in zip(vm.sl.shape, vm.grids.twt.shape):
            self.assertEqual(n0, n1)



def suite():
    return unittest.makeSuite(VMTestCase, 'dev')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
