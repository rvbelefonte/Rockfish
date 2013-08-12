"""
Test of ObsPy's ability to read MSEED files
"""
import unittest
import os
from obspy.core import read
from rockfish.utils.loaders import get_example_file

class readTestCase(unittest.TestCase):

    def setUp(self):
        """
        Setup the test bench
        """
        self.demodb = get_example_file('demo') 

    def test_read(self):
        """
        Should return an obspy stream object
        """
        fname = os.path.join(os.path.dirname(self.demodb), 
                             'wf/knetc/1992/138/210426/19921382155.15.CHM.BHZ')

        fname = '/Volumes/raid0/Projects/Mariana/data/raw/broadband/sio_data_files/B01S/B01S.HH1.2013.035.00.59.58.msd'

        st = read(fname)


def suite():
    return unittest.makeSuite(readTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

