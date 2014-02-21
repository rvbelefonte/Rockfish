"""
Test suite for the population module
"""
import unittest
import numpy as np
import logging
from bitstring import BitArray
from rockfish.genetic.bitutils import BitSet
from rockfish.genetic.population import Population


class PopulationTestCase(unittest.TestCase):

    def test___init__(self):
        """
        Should initialize with all required attributes
        """
        # Should handle multi-dimensional arrays
        for shp in [(10,), (10, 5), (23, 2, 3)]:
            f0 = np.random.rand(*shp)
            pop = Population(f0, nbits=64)

            # Indiviudals should be stored as a BitSet
            self.assertTrue(isinstance(pop._ind, BitSet))
            for b in pop._ind._bitarray:
                self.assertTrue(isinstance(b, BitArray))

            # Population.ind should be a float representation of the BitSet
            # with the same shape and size as the intial population matrix
            self.assertEqual(pop.ind.shape, f0.shape)
            self.assertEqual(pop.size, len(f0))
            _f0 = f0.flatten()
            _f1 = pop.ind.flatten()
            for __f0, __f1 in zip(_f0, _f1):
                self.assertEqual(__f0, __f1)
                self.assertTrue(isinstance(__f1, np.float64))

            # should set fitness attribute
            fit0 = np.ones(len(f0))
            pop.fit = np.ones(len(f0))
            for f0, f1 in zip(fit0, pop.fit):
                self.assertEqual(f0, f1)

            # fit must always be an array with len = len(ind)
            with self.assertRaises(ValueError):
                pop.fit = [1, 2]

    def test_fit(self):
        """
        Setting fit should update the _fit attribute and force resorting
        """
        ind0 = np.random.rand(10, 5)
        fit0 = range(10)[::-1] # already sorted

        pop = Population(ind=ind0, fit=fit0)
        for f0, f1 in zip(fit0, pop.fit):
            self.assertEqual(f0, f1)

        # should allow for setting elements directly
        pop.fit[5] = np.nan
        pop.fit[8] = np.nan
        self.assertEqual(len(np.nonzero(np.isnan(pop.fit))[0]), 2)
        self.assertEqual(len(np.nonzero(np.isnan(pop._fit))[0]), 2)

        # should always be sorted
        ind0 = np.random.rand(10)
        fit0 = range(10)
        pop = Population(ind=ind0, fit=fit0)

        self.assertEqual(ind0[0], pop.ind[-1])
        self.assertEqual(ind0[-1], pop.ind[0])

        _ind0 = pop.ind[-1]
        pop.fit[-1] = 9999
        self.assertEqual(pop.ind[0], _ind0)

        ind0 = pop.ind[:]
        pop.fit = range(10)
        self.assertEqual(ind0[0], pop.ind[-1])

    def test_inew(self):
        """
        Should return indices of new individuals
        """
        ind0 = np.random.rand(10, 5)
        fit0 = np.random.rand(10)

        pop = Population(ind=ind0, fit=fit0)

        self.assertEqual(len(pop.inew), 0)

        pop.fit[5] = np.nan
        self.assertEqual(len(pop.inew), 1)
        
        pop.fit[6] = np.nan
        self.assertEqual(len(pop.inew), 2)

    def test_isort(self):
        """
        Should return indices that would sort the fitness array
        """
        ind0 = np.random.rand(10, 5)
        fit0 = range(10)[::-1] 

        pop = Population(ind=ind0, fit=fit0)

        idx = pop.isort
        for i0, i1 in zip(fit0[::-1], idx):
            self.assertEqual(i0, i1)

    def test_sort(self):
        """
        Should sort ind and fit by fitness
        """
        ind0 = np.random.rand(10, 5)
        fit0 = range(10)[::-1] 
        pop = Population(ind=ind0, fit=fit0)

        isort = pop.isort
        pop.sort()

        for i in range(10):
            for f0, f1 in zip(pop.ind[i], ind0[isort[i]]):
                self.assertEqual(f0, f1)

    def test_fit_min(self):
        """
        Should return minimum fitness value
        """
        ind0 = np.random.rand(10, 5)
        fit0 = range(10)[::-1] 
        pop = Population(ind=ind0, fit=fit0)

        self.assertEqual(pop.fit_min, 0)

    def test_fit_max(self):
        """
        Should return minimum fitness value
        """
        ind0 = np.random.rand(10, 5)
        fit0 = range(10)[::-1] 
        pop = Population(ind=ind0, fit=fit0)

        self.assertEqual(pop.fit_max, 9)

    def test_fit_mean(self):
        """
        Should return minimum fitness value
        """
        ind0 = np.random.rand(10, 5)
        fit0 = range(10)[::-1] 
        pop = Population(ind=ind0, fit=fit0)

        self.assertEqual(pop.fit_mean, np.mean(fit0))

    def test_clone(self):
        """
        Should clopy the population with a bias towards fitter individuals
        """
        ind0 = np.random.rand(100, 5)
        fit0 = range(100)
        
        pop = Population(ind=ind0, fit=fit0)

        shape0 = ind0.shape
        size0 = pop.size

        fit_mean0 = pop.fit_mean
        pop.clone()

        self.assertGreater(pop.fit_mean, fit_mean0)

        # should not change shape or size of population
        self.assertEqual(pop.ind.shape, shape0)
        self.assertEqual(pop.size, size0)

    def test_mutate(self):
        """
        Should mutate the population
        """
        ind0 = np.random.rand(100, 5)
        fit0 = range(100)
        
        pop = Population(ind=ind0, fit=fit0)

        nmutate = 0
        for i in range(10):
            pop.mutate()
            nmutate += len(pop.inew)

        self.assertGreater(nmutate, 0)

    def test_cross(self):
        """
        Should cross two numbers
        """
        ind0 = np.random.rand(5, 3)
        fit0 = range(5)
        pop = Population(ind=ind0, fit=fit0)

        pop.cross(px=1.)
        self.assertGreater(len(pop.inew), 1)

    def dev_reproduce(self):
        """
        Should create a new generation
        """
        ind0 = np.random.rand(50, 3)
        fit0 = range(len(ind0))
        pop0 = Population(ind=ind0, fit=fit0)

        pop1 = pop0.reproduce(px=1., pm=1., inplace=False)

        self.assertEqual(pop1.size, pop0.size)
        self.assertGreater(len(pop1.inew), 0)

        # should not produce NaNs
        for i in range(50):
            ind0 = 3. * np.random.rand(10, 3)
            fit0 = np.random.rand(10)

            pop = Population(ind=ind0, fit=fit0)

            pop.reproduce()

            self.assertEqual(len(np.nonzero(np.isnan(pop.ind))[0]), 0)








def suite():
    return unittest.makeSuite(PopulationTestCase, 'dev')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
