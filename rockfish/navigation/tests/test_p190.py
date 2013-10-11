"""
Test suite for the UKOOA P1/90 format support module.
"""
import os
import unittest
from rockfish.navigation.p190 import P190
from rockfish.utils.loaders import get_example_file

TEST_DATA_DIR = 'data'
P190_FILES = [#(filename, nsources, nchannels),
              ('mgl0807.p190', 2, 636)]

line_count = lambda filename: len(open(filename, 'r').readlines())

class P190TestCase(unittest.TestCase):
    """
    Tests for the UKOOA P1/90 format support module
    """
    def setUp(self):
        """
        Setup for the test examples
        """
        pass

    def test_read(self):
        """
        Should be able to read a P1/90 file
        """
        dbfile = 'test_p190.sqlite'
        for fname, nsrc, nchan in P190_FILES: 
            _fname = get_example_file(fname)
            p1 = P190(_fname, database=dbfile)
            self.assertTrue(os.path.isfile(dbfile))
            self.assertEqual(len(p1.source_points), nsrc)
            self.assertEqual(len(p1.receiver_groups), nchan)
            os.remove(dbfile)

    def test__write_csv(self):
        """
        Should be able to write data to CSV files
        """
        dbfile = 'test_p190.sqlite'
        for fname, nsrc, nchan in P190_FILES: 
            # read p190 file
            _fname = get_example_file(fname)
            p1 = P190(_fname)

            # should write three files
            fnames = p1.write('test_csv', output_format='csv')
            tables = [p1.HEADER_TABLE, p1.COORDINATE_TABLE, p1.RECEIVER_TABLE] 
            for _table in tables:
                self.assertTrue(os.path.isfile(fnames[_table]))
    
            # should have a line for each source, receiver pair
            nrec = line_count(fnames['receiver_groups'])
            self.assertEqual(nrec - 1, nsrc * nchan)

            # cleanup
            for _table in tables:
                os.remove(fnames[_table])

    def test__write_p190(self):
        """
        Should be able to write data to the P190 format
        """
        dbfile = 'test_p190.sqlite'
        for fname, nsrc, nchan in P190_FILES: 
            # read p190 file
            _fname = get_example_file(fname)
            p1 = P190(_fname)

            # should write one p190 file
            ofile = 'test.p190'
            p1.write(ofile, output_format='p190')
            self.assertTrue(os.path.isfile(ofile))

            # read new p190
            p1_new = P190(ofile)

            # should have the same data
            self.assertEqual(len(p1.receiver_groups),
                             len(p1_new.receiver_groups))
            self.assertEqual(len(p1.source_points),
                             len(p1_new.source_points))

            
            # cleanup
            os.remove(ofile)


def suite():
    return unittest.makeSuite(P190TestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
