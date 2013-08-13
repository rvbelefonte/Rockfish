"""
Test suite for the workers module
"""
import os, shutil, unittest
from rockfish import TraveltimeDatabaseConnection 
from rockfish.raytrace.mpi import workers
from rockfish.models import VM

class workersTestCase(unittest.TestCase):

    def SetUp(self):
        """
        Setup the test bench
        """
        pass

    def test_Raytracer_dbtype(self):
        """
        Should raise TypeError if db is wrong type 
        """
        db = None
        self.assertRaises(TypeError, workers.RaytraceWorker, db)
       
        db = TraveltimeDatabaseConnection(':memory:')
        rt = workers.RaytraceWorker(db, None)
        self.assertIsInstance(rt, workers.RaytraceWorker)

    def test_Raytrace_setup(self):
        """
        Should write input files for a single worker
        """
        odir = 'temp.out'
        if os.path.isdir(odir):
            shutil.rmtree(odir)
        db = TraveltimeDatabaseConnection(':memory:')
        rt = workers.RaytraceWorker(db, None, output_dir=odir)
        rt.setup()

        # should make the output directory
        self.assertTrue(os.path.isdir(odir))

        # should have created input files
        for fname in [rt.REC_FILE, rt.SRC_FILE, rt.PICK_FILE]:
            self.assertTrue(os.path.isfile(fname))

        # cleanup
        shutil.rmtree(odir)

    def test_Raytrace_run(self):
        """
        Should raytrace a model
        """
        # setup traveltime database
        db = TraveltimeDatabaseConnection(':memory:')
        db.insert_pick(event='Pg', branch=1, subbranch=0,
                       rid=10, sid=9001,
                       sx=20000, sy=0, sz=-6,
                       rx=80000, ry=0, rz=-5000,
                       time=99, error=0.05)

        # setup example vm model
        vmfile = 'temp.vm'
        vm = VM()
        vm.insert_interface(5)
        vm.define_constant_layer_velocity(0, 1.5)
        vm.define_constant_layer_gradient(1, 0.5)
        vm.write(vmfile)
        
        # setup raytracer
        odir = 'temp.out'
        options = {'verbose': True}
        rt = workers.RaytraceWorker(db, vmfile, output_dir=odir,
                                    options=options)
        rt.setup()

        # should run the raytracer
        rt.run()

        # cleanup
        shutil.rmtree(odir)
        
       

def suite():
    return unittest.makeSuite(workersTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
