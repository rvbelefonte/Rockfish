"""
Test suite for the utils module.
"""
import os
import unittest
from rockfish.tomography.utils import update_model_id

class utilsTestCase(unittest.TestCase):
    """
    Test cases for the utils module.
    """
    def test_update_model_id(self):
        """
        Should increment a <step>.<iteration> formated model id.
        """
        # should handle id without paths or extensions
        self.assertEqual('0.01', update_model_id('0.00'))
        self.assertEqual('00.01', update_model_id('00.00'))
        self.assertEqual('00.001', update_model_id('00.000'))
        # should handle ids with paths and but no extensions
        path = os.path.join('path', 'to', 'mod')
        self.assertEqual(os.path.join(path, '0.1'),
                         update_model_id(os.path.join(path, '0.0')))
        # should handle ids with no paths and but with extensions
        self.assertEqual('0.01.vm', update_model_id('0.00.vm'))
        # should handle ids with paths and extensions
        path = os.path.join('path', 'to', 'mod')
        self.assertEqual(os.path.join(path, '0.1.vm'),
                         update_model_id(os.path.join(path, '0.0.vm')))


def suite():
    return unittest.makeSuite(utilsTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
