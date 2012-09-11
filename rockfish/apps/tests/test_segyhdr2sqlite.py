"""
Test suite for rockfish.apps.segyhdr2sqlite
"""
import os
import unittest
import subprocess
from rockfish.core.util import get_example_file
from rockfish.apps import segyhdr2sqlite

class segyhdr2sqliteTestCase(unittest.TestCase):
    """
    Test cases for segyhdr2sqlite command-line utility.
    """
    def setUp(self):
        """
        Set benchmark data.
        """
        pass

    def test_segyhdr2sqlite(self):
        """
        """
        filename = get_example_file('ew0210_o30.segy')
        # should create a new database
        sh = 'python ../segyhdr2sqlite.py test.db %s' %filename
        subprocess.call(sh, shell=True)
        self.assertTrue(os.path.isfile('test.db'))

def suite():
    return unittest.makeSuite(segyhdr2sqliteTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
