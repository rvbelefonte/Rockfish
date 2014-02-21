"""
Test suite for the tools module
"""
import unittest
import numpy as np
from rockfish.genetic import tools

class toolsTestCase(unittest.TestCase):
    
    def test_position(self):
        """
        Should determine the position of a number in sorted series
        """
        f0 = np.asarray([10, -1, -3, 2, 30])
        pos0 = [3, 1, 0, 2, 4]
        pos1 = tools.position(f0)

        for p0, p1 in zip(pos0, pos1):
            self.assertEqual(p0, p1)

        for i in range(10):
            f0 = np.random.rand(5)
            pos = tools.position(f0)

            self.assertEqual(pos[np.argmin(f0)], 0)
            self.assertEqual(pos[np.argmax(f0)], len(f0) - 1)

    def test_linear_rank(self):

        # should handle dimensions correctly
        for sp in np.arange(1, 2, 0.1):
            fitness = np.random.rand(5) 
            rank = tools.linear_rank(fitness, sp=sp)
        
            # should return an array with the same length as fitness
            self.assertEqual(len(fitness), len(rank))
            self.assertEqual(rank.shape, (len(fitness),))

            # should always sum to the length of fitness
            self.assertAlmostEqual(sum(rank), len(fitness), 6)

            # should rank according to values if sp > 1.
            if sp > 1.:
                self.assertEqual(np.argmax(rank), np.argmax(fitness))

    def test_bga_mutate(self):

        # output be same shape as input
        for shape in [(10,), (100, 3), (40, 3, 2)]:
            f0 = np.ones(shape)
            f1 = tools.bga_mutate(f0, r=0.1, k=0.001)
            self.assertEqual(f0.shape, f1.shape)

        # should change some values
        f0 = np.ones(10)
        n = 0
        for i in range(10):
            f1 = tools.bga_mutate(f0, r=0.1, k=0.001)
            for _f0, _f1 in zip(f0, f1):
                if _f0 != _f1:
                    n += 1
        self.assertGreater(n, 0)
        
        # larger r values should produce more variability
        f0 = np.ones(10)
        s1 = []
        s2 = []
        for i in range(1000):
            f1 = tools.bga_mutate(f0, r=0.1, k=0.001)
            f2 = tools.bga_mutate(f0, r=0.5, k=0.001)
            s1.append(np.std(f1))
            s2.append(np.std(f2))

        self.assertGreater(np.mean(s2), np.mean(s1))

        # larger k values should produce smaller changes
        f0 = np.ones(10)
        m1 = []
        m2 = []
        for i in range(1000):
            f1 = tools.bga_mutate(f0, r=1., k=0.001)
            f2 = tools.bga_mutate(f0, r=1., k=10.)

            m1.append(max(np.abs(f1 - f0)))
            m2.append(max(np.abs(f2 - f0)))

        self.assertGreater(np.mean(m1), np.mean(m2))

    def test_clone(self):
        """
        Should copy the population with a bias towards fitter individuals
        """
        # should select towards all ones
        f0 = np.arange(-3, 5)
        for i in range(5):
            fit0 = 1. / np.abs(f0 - 1.)
            rank = tools.linear_rank(fit0, sp=2)
            nchild = np.round(rank)
            f0 = tools.clone(f0, nchild)
        self.assertEqual(np.sum(f0), len(f0))




def suite():
    return unittest.makeSuite(toolsTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

