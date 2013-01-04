"""
Test suite for the loaders module
"""
import os
import unittest
import doctest
from rockfish.utils import loaders


class LoadersTestCase(unittest.TestCase):
    """
    Test cases for the loaders module
    """
    def get_test_data_dirs(self):
        """
        get_test_data_dirs() should return a list of data directories
        """
        dirnames = loaders.get_test_data_dirs()
        self.assertTrue(isinstance(dirnames, list))

    def test_get_example_file(self):
        """
        get_example_file() should return the path of an example file
        """
        import rockfish
        # should return a filename
        filename = 'mgl0807.p190'
        path0 = os.path.join(rockfish.__path__[0], 'navigation',
                             'tests', 'data', filename)
        self.assertEqual(path0, loaders.get_example_file(filename))
        # should raise an ioerror if file does not exist
        filename = 'does_not.exist'
        with self.assertRaises(IOError):
            loaders.get_example_file(filename)


def suite():
    tests = unittest.makeSuite(LoadersTestCase, 'test')
    tests.addTests(doctest.DocTestSuite(loaders))  # include doctests
    return tests

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
