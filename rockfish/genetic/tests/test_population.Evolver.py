"""
Test suite for the population.Evolver class
"""
import unittest
import numpy as np
from rockfish.genetic import population


def eval_one_max(pop):

    return 1. / np.sum(np.abs(pop - 1.), axis=1)



class EvolverTestCase(unittest.TestCase):

    def test_eval_one_max(self):
        """
        Make sure the benchmark evaluator is working
        """
        f0 = np.ones((10, 5))
        self.assertTrue(np.isinf(eval_one_max(f0)[0]))

    def test___init__(self):
        """
        Should initialize with all the required attributes
        """
        f0 = 5 * (np.random.rand(10, 5) - 0.5)
        ga = population.Evolver(f0, eval_one_max)
        self.assertTrue(hasattr(ga, 'register'))

        # should have called evalute
        self.assertEqual(ga.generations[-1].new, 0)

        # should have registered a default ranking function
        self.assertEqual(np.round(np.sum(ga.rank())), len(f0))

    def test_clone(self):
        """
        Should create a new generation with a bias towards fitter
        individuals
        """
        f0 = 5 * (np.random.rand(10, 5) - 0.5)
        ga = population.Evolver(f0, eval_one_max)
        ga.clone()

        # should have created a new generation
        self.assertEqual(len(ga.generations), 2)

        # should have copied fitness
        self.assertFalse(ga.generations[-1].new)

    def test_mutate(self):
        """
        Should mutate the current generation
        """
        f0 = 5 * (np.random.rand(10, 5) - 0.5)
        ga = population.Evolver(f0, eval_one_max)

        self.assertFalse(ga.generations[-1].new)

        for i in range(10):
            ga.mutate()

        self.assertTrue(ga.generations[-1].new)

    def test__evolve(self):
        """
        Should advance the population by one generation
        """
        f0 = 3 * np.random.rand(10, 5)
        ga = population.Evolver(f0, eval_one_max)

        new = 0
        ngen = 10000
        for i in range(ngen):
            ga._evolve()
            #print ga.generations[-1].individuals[-1]
            #print ga.generations[-1].fitness[-1]

        self.assertEqual(len(ga.generations), ngen + 1)










def suite():
    return unittest.makeSuite(EvolverTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

