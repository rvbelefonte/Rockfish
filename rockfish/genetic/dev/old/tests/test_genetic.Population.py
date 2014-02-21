"""
Test suite for the genetic.Population class
"""

import unittest
import numpy as np
import logging
from rockfish.genetic.genetic import Population,\
        PopulationFittnessNotSetError, PopulationFittnessDimensionError

#logging.basicConfig(level='DEBUG')

class PopulationTestCase(unittest.TestCase):

    def test_init(self):
        """
        Should initialize with the correct attributes 
        """
        # should create an empty instance
        pop = Population()

        self.assertTrue(hasattr(pop, 'CROSSOVER_PROBABILITY'))
        self.assertTrue(hasattr(pop, 'MUTATION_PROBABILITY'))
        self.assertTrue(hasattr(pop, 'individuals'))
        self.assertTrue(hasattr(pop, 'fitness'))
        self.assertTrue(hasattr(pop, 'inew'))

        self.assertEqual(len(pop.individuals), 0)

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

        # npop should always be the length of individuals
        ind0 = np.random.rand(100, 5)
        pop = Population(individuals=ind0)
        self.assertEqual(ind0.shape[0], pop.npop)
        self.assertEqual(ind0.shape[0], len(pop.individuals))
        self.assertEqual(len(ind0), len(pop.individuals))

    def test_fitness(self):
        """
        Fitness must always be the same length as individuals
        """
        pop = Population(individuals=[1, 2, 3, 4, 5])

        # should raise error when trying to set fitness with length not
        # equal to the length of indivuals
        with self.assertRaises(PopulationFittnessDimensionError):
            pop.fitness = [1, 2, 3]

        # should allow setting fitness to an iterable with the same length
        # as individuals
        self.fitness = np.zeros(pop.npop)
        self.assertEqual(len(self.fitness), pop.npop)

        # setting fitness should force a sort of individuals and fitness
        ind0 = np.random.rand(100, 5)
        fit0 = np.arange(100)
        pop = Population(individuals=ind0, fitness=fit0)
        for v0, v1 in zip(ind0[0], pop.individuals[-1]):
            self.assertEqual(v0, v1)

        self.assertEqual(fit0.max(), pop.fitness[0])


        # ... but should not change the shape of individuals
        self.assertEqual(ind0.shape, pop.individuals.shape)
        self.assertEqual(pop.fitness.shape, (100,))

        # should not allow fitness to be greater than 1d
        with self.assertRaises(PopulationFittnessDimensionError):
            pop.fitness = np.zeros((pop.npop, 10))


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

        self.assertGreater(np.max(sumfit), np.sum(fit0))

        # should not change shape of 1d array
        ind0 = np.random.rand(50)
        pop = Population(individuals=ind0, fitness=range(50))
        pop.clone()
        self.assertEqual(pop.individuals.shape, ind0.shape) 

        # should not change shape of multi-d array
        ind0 = np.random.rand(50, 5)
        pop = Population(individuals=ind0, fitness=range(50))
        pop.clone()
        self.assertEqual(pop.individuals.shape, ind0.shape)

        # should not produce NaNs
        ind0 = np.round(np.random.rand(100))
        pop = Population(individuals=ind0)
        for p in range(100):
            pop.clone()
            self.assertEqual(len(np.nonzero(np.isnan(pop.individuals))[0]), 0)


    def test_crossover(self):
        """
        Should perform binary crossover on a subset of the population
        """
        ind0 = np.random.rand(4) 
        fit0 = np.arange(len(ind0))
        pop = Population(individuals=ind0, fitness=fit0)

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
        pop = Population(individuals=ind0, fitness=range(50))

        pop.crossover(p=1.)
        self.assertGreater(len(pop.inew), 0)

        # should not change shape of individuals
        self.assertEqual(pop.individuals.shape, ind0.shape)

        # FIXME?? fails on np.log10(0) in power calc. in float2bin()
        ## should not produce NaNs
        ind0 = np.round(np.random.rand(100))
        pop = Population(individuals=ind0)
        for p in [0.1, 0.5, 1.]:
            pop.crossover(p=p)
            self.assertEqual(len(np.nonzero(np.isnan(pop.individuals))[0]), 0)

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
        pop = Population(individuals=ind0, fitness=range(50))

        pop.mutate(p=1.)
        self.assertGreater(len(pop.inew), 0)

        # should not change shape of individuals
        self.assertEqual(pop.individuals.shape, ind0.shape)

        ## should not produce NaNs
        #ind0 = np.round(np.random.rand(100))
        #pop = Population(individuals=ind0)
        #for p in [0.1, 0.5, 1.]:
        #    pop.mutate(p=p)
        #    self.assertEqual(len(np.nonzero(np.isnan(pop.individuals))[0]), 0)



def suite():
    return unittest.makeSuite(PopulationTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
