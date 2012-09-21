"""
Test suite for the UKOOA P1/90 format support module.
"""
import logging
import unittest
from rockfish.navigation.p190 import P190

logging.basicConfig(level=logging.WARN)

TEST_DATA_DIR = 'data'
P190_FILES = ['mgl0807.p190']

class P190TestCase(unittest.TestCase):
    """
    Tests for the UKOOA P1/90 format support module.
    """
    def setUp(self):
        # files that ukooa.py should be able to read
        self.p190_files = ['{:}/{:}'.format(TEST_DATA_DIR, f) for f in
                           P190_FILES]

    def test_read(self):
        """
        Should be able to read a P1/90 file.
        """
        for filename in self.p190_files:
            p1 = P190(filename,'test_p190.sqlite')

def suite():
    return unittest.makeSuite(P190TestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

