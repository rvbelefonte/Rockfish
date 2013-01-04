"""
Test suite for the version module.
"""

import unittest
import doctest
from rockfish.utils import version


class VersionTestCase(unittest.TestCase):
    """
    Test cases for the version module.
    """
    def test_get_git_revision(self):
        """
        get_git_revision() should return an integer value as text string
        """
        rev = version.get_git_revision()
        self.assertGreater(int(rev), 0)

    def test_get_version(self):
        """
        get_version() should produce a PEP386-compliant version number
        """
        self.assertEqual(version.get_version((0, 5, 0, 'alpha', 48)),
                         '0.5a48')
        self.assertEqual(version.get_version((1, 2, 1, 'beta', 0)),
                         '1.2.1b0')
        self.assertEqual(version.get_version((1, 2, 1, 'final', 0)),
                         '1.2.1')


def suite():
    tests = unittest.makeSuite(VersionTestCase, 'test')
    tests.addTests(doctest.DocTestSuite(version))  # include doctests
    return tests

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
