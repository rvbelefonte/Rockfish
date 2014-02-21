"""
Test suite for the population.Population class
"""
import unittest
import numpy as np
from rockfish.genetic import population

class PopulationTestCase(unittest.TestCase):

    def test___init__(self):
        """
        Should initialize with all the required attributes
        """
        # should create an empty population
        pop = population.Population()
        self.assertEqual(pop.size, 0)
        self.assertEqual(len(pop.individuals), 0) 
        self.assertEqual(len(pop.fitness), 0)

        # should set individuals at init, if passed
        f0 = np.random.rand(100, 5)
        pop = population.Population(individuals=f0)
        self.assertEqual(pop.size, 100)
        self.assertEqual(pop.individuals.shape, f0.shape)
        self.assertEqual(len(pop.fitness), 100)
        self.assertEqual(len(pop._inew), 100)

        # should set fitness at init, if passed
        f0 = np.random.rand(100, 5)
        fit0 = np.arange(0, 100)
        pop = population.Population(individuals=f0, fitness=fit0)
        self.assertEqual(pop.size, 100)
        self.assertEqual(pop.individuals.shape, f0.shape)
        self.assertEqual(len(pop.fitness), 100)
        self.assertEqual(pop.new, 0)

    def test__inew(self):
        """
        Should return indices of individuals flagged as new
        """
        # default should use np.nan as a flag
        f0 = np.random.rand(100, 5)
        pop = population.Population(individuals=f0)
        self.assertEqual(pop.new, 100)
        self.assertEqual(len(np.nonzero(np.isnan(pop.fitness))[0]), 100)

        # should allow for custom flag
        pop = population.Population(individuals=f0, new_flag=-999)
        self.assertEqual(pop.new, 100)

        # should find flagged individuals
        pop = population.Population(individuals=f0)
        pop.fitness = np.ones(pop.size)
        idx = np.random.randint(0, pop.size, size=20)
        pop._fitness[idx] = pop.NEW_FLAG
        self.assertEqual(pop.new, len(np.unique(idx)))


def suite():
    return unittest.makeSuite(PopulationTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

