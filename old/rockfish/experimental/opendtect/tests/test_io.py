"""
Test cases for the io module.
"""
import os
import unittest
from rockfish.opendtect import io


class ioTestCase(unittest.TestCase):
    """
    Test cases for the io module.
    """
    def test_read_2dh(self):
        """
        Should be able to read 2D horizon data from the binary format.
        """
        filename = 'example.2dh'
        io.read_2dh(filename)


def suite():
    return unittest.makeSuite(ioTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
