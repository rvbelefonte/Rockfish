"""
Test cases for the antelope.core module
"""
import unittest
from rockfish.utils.loaders import get_example_file
from rockfish.antelope.core import readANTELOPE
from obspy.core import UTCDateTime

class coreTestCase(unittest.TestCase):

    def setUp(self):
        """
        Setup the test bench
        """
        self.demodb = get_example_file('demo') 

    def test_readANTELOPE(self):
        """
        Should return an obspy stream object
        """
        st = readANTELOPE(self.demodb, station='USP', channel='BHZ',
                          starttime=UTCDateTime(1992, 5, 17, 21, 55, 16),
                          endtime=UTCDateTime(1992, 5, 17, 21, 56, 0))
        print st

def suite():
    return unittest.makeSuite(coreTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
