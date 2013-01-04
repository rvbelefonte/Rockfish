"""
Test suite for the rayfan module.
"""
import unittest
import numpy as np
import logging
from rockfish.tomography.rayfan import Rayfan
from rockfish.utils.loaders import get_example_file

logging.basicConfig(level=logging.DEBUG)


class rayfanTestCase(unittest.TestCase):
    """
    Test cases for the rayfan module.
    """
    def test_rayfan_init(self):
        """
        Calling Rayfan(file) should read data from a file.
        """
        # Example rayfan file
        rayfile = get_example_file('goc_l26.14.00.ray')
        # Open the file
        file = open(rayfile, 'rb')
        # Should read 1st rayfan from the file
        rfn = Rayfan(file)


def suite():
    return unittest.makeSuite(rayfanTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
