"""
Test suite for the masters module 
"""
import os, shutil, unittest
from rockfish import TraveltimeDatabaseConnection 
from rockfish.raytrace.mpi import workers, masters
from rockfish.models import VM

class mastersTestCase(unittest.TestCase):

    def SetUp(self):
        """
        Setup the test bench
        """
        pass

    def test_RaytraceMaster_dbtype(self):
        """
        Should raise TypeError if db is wrong type 
        """
        db = None
        self.assertRaises(TypeError, masters.RaytraceMaster, db, None)
       
        db = TraveltimeDatabaseConnection(':memory:')
        rt = masters.RaytraceMaster(db, None)
        self.assertIsInstance(rt, masters.RaytraceMaster)

    def test_RaytraceMaster_distribute(self):
        """
        Should setup raytrace workers
        """
        # setup traveltime database
        db = TraveltimeDatabaseConnection(':memory:')
        db.insert_pick(event='Pg', branch=1, subbranch=0,
                       rid=10, sid=9001,
                       sx=20000, sy=0, sz=-6,
                       rx=80000, ry=0, rz=-5000,
                       time=99, error=0.05)
        db.insert_pick(event='Pn', branch=1, subbranch=0,
                       rid=10, sid=9001,
                       sx=20000, sy=0, sz=-6,
                       rx=80000, ry=0, rz=-5000,
                       time=99, error=0.05)

        odir = 'test.out'
        if os.path.isdir(odir):
            shutil.rmtree(odir)

        rt = masters.RaytraceMaster(db, None, pick_keys={'sid': 9001},
                                    output_dir=odir)
                                    
        rt.distribute()
        

       

def suite():
    return unittest.makeSuite(mastersTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
