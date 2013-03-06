"""
Test cases for the vm2gmt module.
"""
import os
import unittest
import numpy as np
from scipy.io import netcdf_file as netcdf
from rockfish.tomography import readVM
from rockfish.tomography.vm2gmt import surface2netcdf
from rockfish.utils.loaders import get_example_file


class vm2gmtTestCase(unittest.TestCase):
    """
    Test suite for the vm2gmt module.
    """
    def test_surface2netcdf(self):
        """
        Should write a surface to a netcdf file.
        """
        vm = readVM(get_example_file('cranis3d.vm'))
        surface2netcdf(vm, 0, 'test.grd')
        grd = netcdf('test.grd', 'r')
        z = grd.variables['z'][:]
        self.assertEqual((vm.ny, vm.nx), z.shape)
        self.assertAlmostEqual(vm.rf[0][0][0] * 1000., z[0][0], 4)
        #os.remove('test.grd')

def suite():
    return unittest.makeSuite(vm2gmtTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
