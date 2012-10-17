"""
Test cases for the vm module.
"""
import os
import unittest
import numpy as np
from rockfish.vmtomo.vm import VM
from rockfish.core.util import get_example_file

class vmTestCase(unittest.TestCase):
    """
    Test cases for the vmtools modules.
    """
    def test_init_empty(self):
        """
        Calling VM without any arguments should return an empty instance.
        """
        vm = VM()
        for attr in ['dx','dy','dz','nx','ny','nz','r1','r2','sl','rf','ir',
                     'ij']:
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
        self.assertAlmostEqual(vm.r1, (0.00,0.00,-0.5), places=2)
        self.assertAlmostEqual(vm.r2, (260.00,0.00,50.00), places=2)
        self.assertAlmostEqual(vm.dx, 0.25, places=2)
        self.assertAlmostEqual(vm.dy, 1.00, places=2)
        self.assertAlmostEqual(vm.dz, 0.1, places=2)
        # Should have same slowness values as read by vm_read.m
        # Grid values should be ordered as [x][y][z]
        self.assertAlmostEqual(vm.sl[0][0][0],  3.0030, places=4)
        self.assertAlmostEqual(vm.sl[-1][0][0], 3.0030, places=4)
        self.assertAlmostEqual(vm.sl[-1][0][0], 3.0030, places=4)
        self.assertAlmostEqual(vm.sl[49][0][19],0.6667, places=4)
        self.assertAlmostEqual(vm.sl[69][0][199],0.1223, places=4)
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
        vm = VM(vmfile)
        # check values
        self.compare_to_benchmark(vm)
        # write it to another file
        tmp = 'temp.vm'
        vm.write(tmp)
        # read these data back in
        vm = VM(tmp)
        # check values
        self.compare_to_benchmark(vm)
        # clean up
        os.remove(tmp)

    def test_pack_unpack_arrays(self):
        """
        Packing and unpacking arrays should not change data.
        """
        vmfile = get_example_file('goc_l26.15.00.vm')
        # read model and leave arrays packed
        vm1 = VM(vmfile, unpack_arrays=False)
        # read the same model and unpack arrays
        vm2 = VM(vmfile)
        # pack the arrays back up
        vm2._pack_arrays()
        # should be the same size
        self.assertEqual(len(vm1.sl), len(vm2.sl))
        self.assertEqual(len(vm1.rf), len(vm2.rf))
        self.assertEqual(len(vm1.ir), len(vm2.ir))
        self.assertEqual(len(vm1.ij), len(vm2.ij))
        # should have the same values
        for i,sl1 in enumerate(vm1.sl):
            self.assertEqual(sl1, vm2.sl[i])
        for i,_ in enumerate(vm1.rf):
            self.assertEqual(vm1.rf[i], vm2.rf[i])
            self.assertEqual(vm1.jp[i], vm2.jp[i])
            self.assertEqual(vm1.ir[i], vm2.ir[i])
            self.assertEqual(vm1.ij[i], vm2.ij[i])

def suite():
    return unittest.makeSuite(vmTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
