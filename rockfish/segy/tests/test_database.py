"""
Test suite for the segy.database module.
"""

import unittest
from rockfish.segy.segy import readSEGY, TRACE_HEADER_KEYS
from rockfish.core.util import get_example_file
from rockfish.segy.database import SEGYHeaderDatabase, TRACE_TABLE

class SEGYHeaderDatabaseTestCase(unittest.TestCase):
    """
    Test cases for the header database.
    """
    def setUp(self):
        """
        Set benchmark data.
        """
        self.segy = readSEGY(get_example_file('ew0210_o30.segy'))
        
        self.segy_scaled = readSEGY(get_example_file('ew0210_o30.segy'),
                                    scale_headers=True)
        

    def test_init_SEGYHeaderDatabase(self):
        """
        Should connect to a tempory database and populate table with header
        attributes.
        """
        # should load all of the standard header attributes
        sdb = SEGYHeaderDatabase(self.segy, *TRACE_HEADER_KEYS)
        for attr in TRACE_HEADER_KEYS:
            sql = 'SELECT %s FROM %s' %(attr, TRACE_TABLE)
            db_values = [row[0] for row in sdb.execute(sql)]
            hdr_values = [tr.header.__getattribute__(attr) \
                          for tr in self.segy.traces]
            self.assertEqual(db_values, hdr_values)
        # should work with the scaled header properties
        scaled_keys = ['scaled_source_coordinate_x']
        sdb = SEGYHeaderDatabase(self.segy_scaled, *scaled_keys)
        for attr in scaled_keys:
            sql = 'SELECT %s FROM %s' %(attr, TRACE_TABLE)
            db_values = [row[0] for row in sdb.execute(sql)]
            hdr_values = [tr.header.__getattribute__(attr) \
                          for tr in self.segy_scaled.traces]
            self.assertEqual(db_values, hdr_values)


def suite():
    return unittest.makeSuite(SEGYHeaderDatabaseTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

