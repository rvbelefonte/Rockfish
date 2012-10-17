"""
Test suite for the rayfan module.
"""
import unittest
import numpy as np
import logging
from rockfish.vmtomo.rayfan import Rayfan
from rockfish.core.util import get_example_file

logging.basicConfig(level=logging.DEBUG)

class rayfanTestCase(unittest.TestCase):
    """
    Test cases for the rayfan module.
    """
    def test_empty_rayfan_init(self):
        """
        Calling Rayfan() should create a new rayfan instance.
        """
        # create empty Rayfan
        rfn = Rayfan()
        # should have all the required arguments
        for attr in ['start_point_id', 'static_correction',
                     'end_point_ids', 'event_ids', 'event_subids',
                     'travel_times', 'pick_times', 'pick_errors',
                     'raypaths']:
            self.assertTrue(hasattr(rfn, attr))

    def test_read_rayfan_init(self):
        """
        Calling Rayfan(file) should read data from a file.
        """
        # Example rayfan file
        rayfile = get_example_file('goc_l26.14.00.ray')
        # Attempting to read from a non-file-like object should raise a
        # TypeError
        with self.assertRaises(TypeError):
            Rayfan(rayfile)
        # Open the file
        file = open(rayfile, 'rb')
        # Should read 1st rayfan from the file
        rfn = Rayfan(file)

def suite():
    return unittest.makeSuite(rayfanTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
