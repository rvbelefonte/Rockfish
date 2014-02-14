"""
Test suite for the genetic.Population class
"""

import unittest
import numpy as np
from rockfish.genetic.genetic import Population, PopulationFittnessNotSetError

class PopulationTestCase(unittest.TestCase):

    def test_init(self):
        """
        Should initialize with the correct attributes 
        """
        # should create an empty instance
        pop = Population()

        self.assertTrue(hasattr(pop, 'register'))

        self.assertTrue(hasattr(pop, 'CROSSOVER_PROBABILITY'))
        self.assertTrue(hasattr(pop, 'MUTATION_PROBABILITY'))
        self.assertTrue(hasattr(pop, 'individuals'))
        self.assertFalse(hasattr(pop, 'fitness'))

        self.assertEqual(len(pop.individuals), 0)

    def test_register(self):
        """
        Should be able to register a function
        """
        def func(a, b, c=3):
            return a, b, c

        pop = Population()

        pop.register('my_func', func, 2, c=4)

        dat = pop.my_func(3)

        self.assertEqual(dat[0], 2)
        self.assertEqual(dat[1], 3)
        self.assertEqual(dat[2], 4)


    def test_individuals(self):
        """
        Updating individuals should force an update of fitness
        """
        pop = Population(individuals=[1, 2, 3], fitness=[0, 0, 0])

        self.assertEqual(pop.npop, 3)

        # resetting individuals should force an update of fit
        pop.individuals = [0, 1, 2]
        with self.assertRaises(PopulationFittnessNotSetError):
            f = pop.fitness

    def test_fitness(self):
        """
        Fitness must always be the same size as individuals
        """
        pop = Population(individuals=[1, 2, 3, 4, 5])

        # should raise error when trying to set fitness with length not
        # equal to the length of indivuals
        with self.assertRaises(AssertionError):
            pop.fitness = [1, 2, 3]

        # should allow setting fitness to an iterable with the same length
        # as individuals
        self.fitness = np.zeros(pop.npop)
        self.assertEqual(len(self.fitness), pop.npop)

    def test_clone(self):
        """
        Should create a new generation by copying the fittest indivuals in
        the current generation
        """
        fit0 = [1, 2, 3, 4]
        pop = Population(individuals=fit0, fitness=fit0)

        sumfit = []
        for i in range(100):
            pop.clone()
            sumfit.append(np.sum(pop.fitness))

        self.assertGreater(np.mean(sumfit), np.sum(fit0))

    def test_crossover(self):
        """
        Should perform binary crossover on a subset of the population
        """
        ind0 = [1, 2, 3, 4]
        pop = Population(individuals=ind0, fitness=ind0)

        # should change some values
        pop.crossover(p=1.)
        count = 0
        for f0, f1 in zip(ind0, pop.individuals):
            if f0 != f1:
                count += 1

        self.assertGreater(count, 0)
        
        # should set fitness for changed individuals to nan
        self.assertGreater(len(pop.inew), 0)
        
        # should handle > 1d
        ind0 = np.random.rand(50, 10)
        pop = Population(individuals=ind0, fitness=ind0)

        pop.crossover(p=1.)
        self.assertGreater(len(pop.inew), 0)

        
        # should not change shape of individuals
        self.assertEqual(pop.individuals.shape, ind0.shape)

    def test_mutate(self):
        """
        Should perform mutation on a subset of the population
        """
        ind0 = np.asarray([1., 2., 3., 4.])
        pop = Population(individuals=ind0, fitness=ind0)

        # should change some values
        pop.mutate(p=1.)
        count = 0
        for f0, f1 in zip(ind0, pop.individuals):
            if f0 != f1:
                count += 1
        self.assertGreater(count, 0)

        # should set fitness for changed individuals to nan
        self.assertGreater(len(pop.inew), 0)

        # should handle > 1d
        ind0 = np.random.rand(50, 10)
        pop = Population(individuals=ind0, fitness=ind0)

        pop.mutate(p=1.)
        self.assertGreater(len(pop.inew), 0)

        # should not change shape of individuals
        self.assertEqual(pop.individuals.shape, ind0.shape)


def suite():
    return unittest.makeSuite(PopulationTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
