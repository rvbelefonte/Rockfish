"""
Test cases for the vm module.
"""
import os
import unittest
import numpy as np
from rockfish.tomography.model import VM, readVM
from rockfish.utils.loaders import get_example_file


class vmTestCase(unittest.TestCase):
    """
    Test cases for the vmtools modules.
    """
    def test_init_empty(self):
        """
        Calling VM without any arguments should return an empty instance.
        """
        vm = VM()
        for attr in ['dx', 'dy', 'dz', 'r1', 'r2', 'sl', 'rf', 'ir', 'ij']:
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
        vmfile = get_example_file('goc_l26.15.00.vm')
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
        # read anymodel with interfaces
        vm = readVM(get_example_file('jump1d.vm'))
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
        vm = VM()
        x = vm.r1[0] + (vm.r2[0] - vm.r1[0]) / 2.
        ix = vm.x2i([x])
        self.assertEqual(x, vm.i2x(ix)[0])

    def test_y2i(self):
        """
        Should convert between y indices and coordinates and back
        """
        vm = VM()
        y = vm.r1[1] + (vm.r2[1] - vm.r1[1]) / 2.
        iy = vm.y2i([y])
        self.assertEqual(y, vm.i2y(iy)[0])

    def test_z2i(self):
        """
        Should convert between z indices and coordinates and back
        """
        vm = VM()
        z = vm.r1[1] + (vm.r2[1] - vm.r1[1]) / 2.
        iz = vm.z2i([z])
        self.assertEqual(z, vm.i2z(iz)[0])

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
        for model in ['cranis3d.vm', 'goc_l26.15.00.vm']:
            vm = readVM(get_example_file(model))
            # should define constant velocities within layer
            for ilyr in range(vm.nr + 1):
                vm.sl = np.nan * np.ones((vm.nx, vm.ny, vm.nz))
                vm.define_stretched_layer_velocities(ilyr, [10])
                self.assertEqual(np.nanmax(vm.sl), 1./10)
                self.assertEqual(np.nanmin(vm.sl), 1./10)

    def test_insert_layer_velocities(self):
        """
        Should insert velocities into a layer.
        """
        for model in ['cranis3d.vm', 'goc_l26.15.00.vm']:
            vm = readVM(get_example_file(model))
            # should define constant velocities within layer
            for ilyr in range(vm.nr + 1):
                vm.sl = np.nan * np.ones((vm.nx, vm.ny, vm.nz))
                sl = 10 * np.ones((vm.nx, vm.ny, vm.nz))
                vm.insert_layer_velocities(ilyr, sl, is_slowness=True)
                self.assertEqual(np.nanmax(vm.sl), 10)
                self.assertEqual(np.nanmin(vm.sl), 10)




def suite():
    return unittest.makeSuite(vmTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
