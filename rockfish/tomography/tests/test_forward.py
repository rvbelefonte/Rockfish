"""
Test suite for the forward module.
"""
import os
import shutil
import unittest
import numpy as np
import logging
import time
from rockfish.picking.database import PickDatabaseConnection
from rockfish.tomography.forward import raytrace, parallel_raytrace
from rockfish.tomography.rayfan import readRayfanGroup
from rockfish.tomography.model import readVM
from rockfish.utils.loaders import get_example_file

logging.basicConfig(level=logging.DEBUG)

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
        if os.path.isfile(pickdbfile):
            os.remove(pickdbfile)
        pickdb = PickDatabaseConnection(pickdbfile)
        pickdb.update_pick(event='P1', ensemble=100, trace=1,
                           branch=1, subbranch=0,
                           time=5.0, source_x=10, source_y=0.0, source_z=0.006,
                           receiver_x=40, receiver_y=0.0, receiver_z=4.9)
        pickdb.update_pick(event='P2', ensemble=100, trace=1,
                           branch=2, subbranch=0, time=5.0)
        pickdb.update_pick(event='P3', ensemble=100, trace=1,
                           branch=3, subbranch=0, time=5.0)
        pickdb.commit()

        # Raytrace
        vm = readVM(vmfile)
        rayfile = 'temp.ray'
        for branch in range(1, 4):
            if os.path.isfile(rayfile):
                os.remove(rayfile)
            pick_keys = {'branch' : branch}
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

    def test_parallel_raytrace(self):
        """
        Should run raytracing in parallel
        """
        # Create pick database
        pickdbfile = 'temp.sqlite'
        if os.path.isfile(pickdbfile):
            os.remove(pickdbfile)
        pickdb = PickDatabaseConnection(pickdbfile)

        for i, event in enumerate( ['P1', 'P2', 'P3']):
            branch = i + 1
            for ens in range(3):
                pickdb.update_pick(event=event, ensemble=ens, trace=1,
                                   branch=branch, subbranch=0,
                                   time=5.0, source_x=10, source_y=0.0,
                                   source_z=0.006, receiver_x=40,
                                   receiver_y=0.0, receiver_z=4.9)
        pickdb.commit()

        # set velocity model
        vmfile = get_example_file('inactive_layers.vm')

        # raytrace
        for nproc in [1, 2, 8]:
            input_dir = 'test.input'
            output_dir = 'test.output'
            t_start = time.clock()
            parallel_raytrace(vmfile, pickdb, branches=[1, 2, 3],
                              input_dir=input_dir, output_dir=output_dir,
                              nproc=nproc, ensemble_field='ensemble')
            t_elapsed = time.clock() - t_start

        shutil.rmtree(input_dir)
        shutil.rmtree(output_dir)
        os.remove(pickdbfile)


def suite():
    return unittest.makeSuite(forwardTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
