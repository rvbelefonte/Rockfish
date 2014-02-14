"""
Test suite for the genetic.Toolbox class
"""

import unittest
import numpy as np
import logging
from rockfish.genetic.genetic import Toolbox

logging.basicConfig(level='DEBUG')

class ToolboxTestCase(unittest.TestCase):

    def test_register(self):
        """
        Should be able to register a function
        """
        def func(a, b, c=3):
            return a, b, c

        tools = Toolbox()

        tools.register('my_func', func, 2, c=4)

        dat = tools.my_func(3)

        self.assertEqual(dat[0], 2)
        self.assertEqual(dat[1], 3)
        self.assertEqual(dat[2], 4)

def suite():
    return unittest.makeSuite(ToolboxTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
