"""
Test suite for the UKOOA P1/90 format support module.
"""
import os
import unittest
from rockfish.navigation.p190 import P190
from rockfish.utils.loaders import get_example_file

TEST_DATA_DIR = 'data'
P190_FILES = ['mgl0807.p190']


class P190TestCase(unittest.TestCase):
    """
    Tests for the UKOOA P1/90 format support module
    """
    def setUp(self):
        """
        Setup for the test examples
        """
        # files that p190 should be able to read
        self.p190_files = [get_example_file(f) for f in P190_FILES]

    def test_read(self):
        """
        Should be able to read a P1/90 file
        """
        for filename in self.p190_files:
            p1 = P190(filename, 'test_p190.sqlite')
            os.remove('test_p190.sqlite')


def suite():
    return unittest.makeSuite(P190TestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
