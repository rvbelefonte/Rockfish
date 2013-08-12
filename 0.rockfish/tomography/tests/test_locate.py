"""
Test case for the locate module 
"""
import os
import unittest
import numpy as np
from rockfish.tomography.model import readVM
from rockfish.utils.loaders import get_example_file
from rockfish.picking.database import PickDatabaseConnection
from rockfish.tomography.forward import raytrace
from rockfish.tomography.rayfan import rayfan2db
from rockfish.tomography.locate import locate_on_surface


TEST_MODELS = ['CRAnis.NorthEast.00.00.vm']


class locateTestCase(unittest.TestCase):
    """
    Test cases for the locate module.
    """
    def test_locate_on_surface(self):
        """
        Should locate a receiver on a surface.
        """
        inst_id = 100
        dx = 1
        iref = 0
        for _vmfile in TEST_MODELS:
            vmfile = get_example_file(_vmfile)
            vm = readVM(vmfile)
            # calculate synthetic times
            pickdb = PickDatabaseConnection(':memory:')
            x0 = np.mean(vm.x)
            y0 = np.mean(vm.y)
            picks = []
            xsearch = vm.xrange2i(max(vm.r1[0], x0 - dx),
                                  min(vm.r2[0], x0 + dx))
            for i, ix in enumerate(xsearch):
                x = vm.x[ix]
                iy = vm.x2i([y0])[0]
                z0 = vm.rf[iref][ix][iy]
                pickdb.add_pick(event='Pw', ensemble=inst_id,
                                trace=i, time=1e30,
                                source_x=x, source_y=y0, source_z=0.006,
                                receiver_x=x0, receiver_y=y0, receiver_z=z0,
                                vm_branch=1, vm_subid=0)
            rayfile = 'temp.ray'
            raytrace(vmfile, pickdb, rayfile)
            raydb = rayfan2db(rayfile, 'temp.syn.sqlite', synthetic=True)
            os.remove(rayfile)
            # run locate
            x, y, z, rms = locate_on_surface(vmfile, raydb, 0, x0=x0,
                                        y0=y0, dx=dx, dy=dx)
            # compare result
            self.assertAlmostEqual(x, x0, 0)
            self.assertAlmostEqual(y, y0, 0)


def suite():
    return unittest.makeSuite(locateTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
