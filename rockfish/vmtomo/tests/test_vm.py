"""
Test cases for the vm module.
"""
import os
import unittest
import numpy as np
from rockfish.vmtomo.vm import VM, readVM
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
        for attr in ['dx','dy','dz','r1','r2','sl','rf','ir','ij']:
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

def suite():
    return unittest.makeSuite(vmTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
