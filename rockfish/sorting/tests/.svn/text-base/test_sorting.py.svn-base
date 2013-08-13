"""
The rockfish.sorting test suite.
"""

import unittest
from rockfish.segy.segy import SEGYFile, SEGYTrace
from rockfish.sorting.trace_sorting import SEGYSorting

class SEGYSortingTestCase(unittest.TestCase):
    """
    Test cases for the sorting module. 
    """
    def setUp(self):
        """
        Create a SEGYFile object to sort.
        """
        self.sgy = SEGYFile()
        self.attr1 = 'ensemble_number'
        self.attr2 = 'trace_number_within_the_ensemble'
        self.val1 = [2,1,2,1,1,2]
        self.val2 = [5,4,3,2,1,0]
        for i,k1 in enumerate(self.val1):
            k2 = self.val2[i]
            self.sgy.traces.append(SEGYTrace())
            self.sgy.traces[i].header.__setattr__(self.attr1,k1) 
            self.sgy.traces[i].header.__setattr__(self.attr2,k2)

    def test_decorate_undecorate(self):
        """
        Decorate should be reversed by undecorate. 
        """
        # Decorated traces should have attribute values prepended.
        self.sgy._decorate_traces(self.attr1, self.attr2)
        for i,tr in enumerate(self.sgy.traces):
            self.assertEqual([self.val1[i], self.val2[i], i, tr[-1]], 
                             self.sgy.traces[i])
        # Undecorating decorated traces should return the original traces
        self.sgy._undecorate_traces()
        for i,tr in enumerate(self.sgy.traces):
            self.assertTrue(isinstance(tr,SEGYTrace))
        
    def test_sort_traces(self):
        """
        sort_traces should sort traces in place.
        """
        # sort the traces
        self.sgy.sort_traces(self.attr1, self.attr2)
        # traces should now be sorted
        # check 1st key
        self.assertEqual([tr.header.__getattribute__(self.attr1) \
                          for tr in self.sgy.traces],sorted(self.val1))
        # check all keys
        values = []
        for i,row in enumerate(zip(self.val1,self.val2)):
            values.append([v for v in row])
            values[i].extend([i])
        correct = [row[:-1] for row in sorted(values)]
        print correct
        result = [[tr.header.__getattribute__(self.attr1),
                   tr.header.__getattribute__(self.attr2)]\
                  for tr in self.sgy.traces]
        self.assertEqual(result,correct)

        
        




def suite():
    return unittest.makeSuite(SEGYSortingTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
