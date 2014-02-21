"""
Test suite for the evolution module
"""
import unittest
import numpy as np
from rockfish.genetic.evolution import Evolver, Population


def eval_one_max(ind):
    ind = np.atleast_1d(ind)
    n = len(ind[0])

    e = []
    for _ind in ind:
        # XXX trying kludge to fix invalid value errors
        d = np.asarray([float(str(i)) for i in _ind])

        print '0: ', d
        print '1: ', d - 1.
        print '2: ', np.abs(d - 1.)
        print '3: ', np.sum(np.abs(d - 1.))

        e.append(n - np.sum(np.abs(d - 1.)))

    return e

class EvolverTestCase(unittest.TestCase):

    def dev_eval_one_max(self):
        """
        Check that the test evaluator is working
        """
        f0 = np.asarray([[1, 1, 1, 1, 1],
                         [0, 1, 1, 1, 1],
                         [0, 1, 0, 1, 1],
                         [0, 1, 0, 1, 1]])

        self.assertEqual(max(eval_one_max(f0)), 5.0)

        # should not produce NaNs
        for i in range(20):
            ind0 = 3. * np.random.rand(10, 3)
            fit0 = eval_one_max(ind0)

            pop = Population(ind=ind0, fit=fit0)
            pop.reproduce()

            fit = eval_one_max(pop.ind)

            print f0
            print fit

            self.assertEqual(len(np.nonzero(np.isnan(fit))[0]), 0)




    def test___init__(self):
        """
        Should initialize a new evolver instance
        """
        f0 = np.asarray([[1, 1, 1, 1, 1],
                         [0, 1, 1, 1, 1],
                         [0, 1, 0, 1, 1],
                         [0, 1, 0, 1, 1]])

        ga = Evolver(f0, eval_one_max)

        # should have evaluated fitness
        self.assertEqual(len(ga.pop.inew), 0)
        best_fit, best_ind = ga.best_fit
        self.assertEqual(best_fit, 5)

        print ga.__str__(extended=True)

    def XXX__evolve(self):
        """
        Should evolve population by one generation
        """
        f0 = 3. * np.random.rand(10, 3)
        ga = Evolver(f0, eval_one_max)

        print ga.__str__(extended=True)
        ga._evolve()
        print ga.__str__(extended=True)
        
        # should have evaluated fitness
        self.assertEqual(len(ga.pop.inew), 0)
        








def suite():
    return unittest.makeSuite(EvolverTestCase, 'dev')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

