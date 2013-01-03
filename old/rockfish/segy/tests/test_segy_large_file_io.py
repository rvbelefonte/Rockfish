"""
Test suite for rockfish.segy.segy
"""

import unittest
import os
import numpy as np
from rockfish.segy.segy import readSEGY, SEGYFile, SEGYTrace
from rockfish.core.util import get_example_file

class SEGYFileLargeSizeIOTestCase(unittest.TestCase):

    def setUp(self):
        self.scratch_dir = 'scratch'
        if not os.path.isdir(self.scratch_dir):
            os.mkdir(self.scratch_dir)


    def readwrite_segy(self, size_gb):
        """
        Writing and then reading should not change data. 
        """
        size_bytes = size_gb * 1073741824 
        npts = 8192
        ntraces = (size_bytes - 3600)/(240 + 4 * npts)
        data = np.float32(np.random.rand(npts))
        # create a SEGYFile object and populate it with data
        segy = SEGYFile()
        # set format to 4-byte IEEE 
        segy.binary_file_header.data_sample_format_code = 5
        segy.binary_file_header.number_of_data_traces_per_ensemble = 1
        for i in range(0, ntraces):
            tr = SEGYTrace()
            tr.data = data
            segy.traces.append(tr)
        # write the new SEGYFile
        test_filename = self.scratch_dir + '/test_segy_large_file_io.segy'
        if os.path.isfile(test_filename):
            os.remove(test_filename)
        segy.write(test_filename, data_encoding=5)
        # read the data back in and compare
        new_segy = readSEGY(test_filename)
        for tr in new_segy.traces:
            self.assertEqual(list(tr.data), list(data))
        # clean up
        #os.remove(test_filename)

    def test_readwrite_segy_1gb(self):
        """
        Should be able to read and write 1 Gb files.
        """
        self.readwrite_segy(1)

    def test_readwrite_segy_2gb(self):
        """
        Should be able to read and write 2 Gb files.
        """
        self.readwrite_segy(2)

    def test_readwrite_segy_4gb(self):
        """
        Should be able to read and write 4 Gb files.
        """
        self.readwrite_segy(4)



def suite():
    return unittest.makeSuite(SEGYFileLargeSizeIOTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

