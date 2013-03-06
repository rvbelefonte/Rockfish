"""
Test suite for the forward module.
"""
import os
import unittest
import numpy as np
import logging
from rockfish.picking.database import PickDatabaseConnection
from rockfish.tomography.forward import raytrace
from rockfish.tomography.rayfan import readRayfanGroup
from rockfish.tomography.model import readVM
from rockfish.utils.loaders import get_example_file


class forwardTestCase(unittest.TestCase):
    """
    Test cases for the rayfan module.
    """
    def test_raytrace_branch_id(self):
        """
        Raytracing should honor branch ids
        """
        #vmfile = get_example_file('jump1d.vm')
        vmfile = get_example_file('inactive_layers.vm')

        # Create pick database
        pickdbfile = 'temp.sqlite'
        pickdb = PickDatabaseConnection(pickdbfile)
        pickdb.update_pick(event='P1', ensemble=100, trace=1,
                        vm_branch=1, vm_subid=0,
                        time=5.0, source_x=10, source_y=0.0, source_z=0.006,
                        receiver_x=40, receiver_y=0.0, receiver_z=4.9)
        pickdb.update_pick(event='P2', ensemble=100, trace=1,
                        vm_branch=2, vm_subid=0, time=5.0)
        pickdb.update_pick(event='P3', ensemble=100, trace=1,
                        vm_branch=3, vm_subid=0, time=5.0)
        pickdb.commit()

        # Raytrace
        vm = readVM(vmfile)
        rayfile = 'temp.ray'
        for branch in range(1, 4):
            if os.path.isfile(rayfile):
                os.remove(rayfile)
            pick_keys = {'vm_branch' : branch}
            raytrace(vmfile, pickdb, rayfile, **pick_keys)
            # Should have created a rayfile
            self.assertTrue(os.path.isfile(rayfile))
            # Load rayfans
            rays = readRayfanGroup(rayfile)
            # Should have traced just one ray
            self.assertEqual(len(rays.rayfans), 1)
            rfn = rays.rayfans[0]
            self.assertEqual(len(rfn.paths), 1)
            # Rays should turn in specified layer
            zmax = max([p[2] for p in rfn.paths[0]])
            self.assertGreaterEqual(zmax, vm.rf[branch - 1][0][0])

        # cleanup
        for filename in [rayfile, pickdbfile]:
            if os.path.isfile(filename):
                os.remove(filename)


def suite():
    return unittest.makeSuite(forwardTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
