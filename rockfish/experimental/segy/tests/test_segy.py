"""
Test suite for rockfish.segy.segy
"""

import unittest
from rockfish.experimental.segy.segy import readSEGY, SEGYFile
from rockfish.utils.loaders import get_example_file

class SEGYFileTestCase(unittest.TestCase):

    def test_readSEGY(self):
        """
        Should return a rockfish.segy.segy.SEGYFile 
        """
        segy = readSEGY(get_example_file('ew0210_o30.segy'))
        self.assertTrue(isinstance(segy, SEGYFile))


def suite():
    return unittest.makeSuite(SEGYFileTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

