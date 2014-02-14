"""
Test suite for the genetic.Evolver class
"""

import unittest
import numpy as np
import logging
from rockfish.genetic.genetic import Evolver, Population

#logging.basicConfig(level='DEBUG')

# Test evaluate functions
def eval_one_max(individuals):
    return 1. / np.sum(np.abs(individuals - 1), axis=1)

def eval_args_kwargs(*args, **kwargs):
    fit = np.sum(args[-1], axis=1)
    for a in args[:-1]:
        fit *= a

    for k in kwargs:
        fit *= kwargs[k]

    return fit


class EvolverTestCase(unittest.TestCase):

    def test_evaluate(self):
        """
        Should register a working evaluate function 
        """
        pop0 = []
        for i in range(100):
            pop0.append(np.round(np.random.rand(5)))


        ga = Evolver(pop0, eval_one_max)

        self.assertTrue(hasattr(ga, 'generations'))
        self.assertTrue(isinstance(ga.generations[0], Population))

        self.assertTrue(ga.generations[0].individuals is ga.individuals)
       
        self.assertTrue(ga.generations[0].CROSSOVER_PROBABILITY\
                is ga.CROSSOVER_PROBABILITY)
        self.assertTrue(ga.generations[0].MUTATION_PROBABILITY\
                is ga.MUTATION_PROBABILITY)

        
        # should register the passed function 'evaluate' as a helper
        self.assertTrue(hasattr(ga, '_evaluate'))

        # should have a main evaluate function that updates fitness
        self.assertTrue(hasattr(ga, 'evaluate'))

        # calling evaluate should update fitness
        ga.evaluate()
        self.assertTrue(ga.generations[0].fitness is ga.fitness)

        # evaluate should also take fixed parameters
        # here, individuals should always be the 1st argument
        pop0 = np.ones((100, 5))

        ga = Evolver(pop0, eval_args_kwargs)
        self.assertEqual(ga.fitness.max(), 5)
        
        ga = Evolver(pop0, eval_args_kwargs, 2)
        self.assertEqual(ga.fitness.max(), 10)
        
        ga = Evolver(pop0, eval_args_kwargs, 2, 3)
        self.assertEqual(ga.fitness.max(), 30)

        ga = Evolver(pop0, eval_args_kwargs, 2, foo=10)
        self.assertEqual(ga.fitness.max(), 100)

    def test__evolve(self):
        """
        Should evolve the population by one generation
        """
        pop0 = []
        for i in range(10):
            pop0.append(np.random.rand(5))

        ga = Evolver(pop0, eval_one_max, crossover_probability=0.,
                mutation_probability=0.)
        fit0 = ga.fitness.mean()

        ga._evolve()
        self.assertEqual(len(ga.generations), 2)

        fit1 = ga.fitness.mean()
        self.assertGreaterEqual(fit1, fit0)

    def dev_evolve(self):
        """
        Should evolve the population by a given number of generations
        """
        pop0 = []
        for i in range(20):
            pop0.append(np.random.rand(5))

        ga = Evolver(pop0, eval_one_max, crossover_probability=0.5,
                mutation_probability=0.5, degeneration=False)

        ga.evolve(ngen=100, verbose=2)




        




def suite():
    return unittest.makeSuite(EvolverTestCase, 'dev')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
