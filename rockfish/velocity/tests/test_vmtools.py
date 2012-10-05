"""
Test cases for vmtools.
"""
import unittest
import numpy as np
from rockfish.velocity.vmtools import VM
from rockfish.core.util import get_example_file

class vmtoolsTestCase(unittest.TestCase):
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

    def test_read_write_vm(self):
        """
        Should be able to read/write a model in the VM Tomography binary format.
        """
        vmfile = get_example_file('goc_l26.15.00.vm')
        # Should read data from the disk file
        vm = VM(vmfile)
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


def suite():
    return unittest.makeSuite(vmtoolsTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
