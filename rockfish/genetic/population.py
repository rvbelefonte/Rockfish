"""
Module for working with evolving populations
"""
import numpy as np
import copy
import logging
import tools


class Population(object):
    """
    Class for managing a single population
    """
    def __init__(self, individuals=[], fitness=None, new_flag=np.nan):

        self.NEW_FLAG = new_flag

        self.individuals = individuals
        self.fitness = fitness


    def _get_size(self):
        return len(self._individuals)

    size = property(fget=_get_size)

    def _get_individuals(self):
        return self._individuals[self._isort]

    def _set_individuals(self, values):
        self._individuals = np.asarray(values)
    
    individuals = property(fget=_get_individuals, fset=_set_individuals)

    def _get_fitness(self):
        return self._fitness[self._isort]

    def _set_fitness(self, values):
        if values is None:
            self._fitness = self.NEW_FLAG * np.ones(self.size)
        else:
            values = np.atleast_1d(values)
            assert values.shape == (self.size, ),\
                    'fitness must be a {:} by 1 array'.format(self.size)

            self._fitness = values

    fitness = property(fget=_get_fitness, fset=_set_fitness)

    def _get_max_fitness(self):

        fit = self.fitness
        idx = np.isfinite(fit)

        return np.max(fit[idx])

    max_fitness = property(_get_max_fitness)

    def _get_inew(self):
        """
        Returns the indices of individuals flagged as new
        """
        if self.NEW_FLAG is np.nan:
            return np.nonzero(np.isnan(self.fitness))[0]
        else:
            return np.nonzero(self.fitness == self.NEW_FLAG)[0]

    _inew = property(fget=_get_inew)

    def _get_new(self):
        """
        Returns the number of new individuals
        """
        return len(self._inew)
    
    new = property(fget=_get_new)

    def _get_isort(self):
        """
        Returns the indices that would sort the population by fitness 
        """
        return np.argsort(self._fitness)

    _isort = property(fget=_get_isort)


class Evolver(tools.Toolbox):
    """
    Class for evolving a population 
    """

    def __init__(self, individuals, evaluate, *args, **kwargs):

        self.NEW_FLAG = kwargs.pop('new_flag', np.nan)
        self.SP = kwargs.pop('sp', 2)
        self.R = kwargs.pop('r', 0.1)
        self.K = kwargs.pop('k', 0.001)
        self.R_REDUCE = kwargs.pop('r_reduce', 0.1)
        self.GROWTH_FACTOR = kwargs.pop('growth_factor', 1.)

        self.generations = [Population(individuals=individuals,
            fitness=kwargs.pop('fitness', None), new_flag=self.NEW_FLAG)]

        self.NPOP = kwargs.pop('npop', len(individuals))
        self.register('_evaluate', evaluate, *args, **kwargs)
        self.evaluate()

        # register the default tools
        self.register('_rank', tools.linear_rank, sp=self.SP)
        self.register('_mutate', tools.bga_mutate, r=self.R, k=self.K)

    def _get_ibest_fit(self):
        #XXX FIXME this doesn't count properly when there are NaNs
        return np.argmax([g.fitness[-1] for g in self.generations\
                if not np.isnan(g.fitness[-1])])

    ibest_fit = property(fget=_get_ibest_fit)

    def _get_best_fit(self):
        return np.max([g.fitness[-1] for g in self.generations\
                if not np.isnan(g.fitness[-1])])

    best_fit = property(fget=_get_best_fit)

    def _get_best_individual(self):

        return self.generations[self.ibest_fit].individuals[-1]

    best_individual = property(fget=_get_best_individual)

    def evaluate(self):
        inew = self.generations[-1]._inew
        self.generations[-1]._fitness[inew] =\
                self._evaluate(self.generations[-1]._individuals[inew])

    def rank(self):
        return self._rank(self.generations[-1].fitness)

    def mutate(self):

        f1 = self._mutate(self.generations[-1]._individuals, r=self.R,
                k=self.K)

        inew = np.nonzero(np.sum(self.generations[-1]._individuals - f1,
            axis=1))

        self.generations[-1]._individuals = f1
        self.generations[-1]._fitness[inew] = self.NEW_FLAG

    def clone(self, **kwargs):
        growth_factor = kwargs.pop('growth_factor', self.GROWTH_FACTOR)
        nchild = np.round(self.rank() * growth_factor)

        f1 = tools.clone(self.generations[-1].individuals, nchild)
        #fit1 = tools.clone(self.generations[-1].fitness, nchild)


        self.generations.append(Population(individuals=f1,
            new_flag=self.NEW_FLAG))


        self.generations[-1].fitness =\
                tools.clone(self.generations[-1].fitness, nchild)

    def _evolve(self):

        if (len(self.generations) > 1) and self.R_REDUCE:
            dfit = (self.generations[-1].max_fitness\
                    - self.generations[-2].max_fitness)\
                    / self.generations[-2].max_fitness
                    
            logging.debug('dfit = {:}'.format(dfit))
            if dfit < 1.e-6:
                self.R *= self.R_REDUCE

        logging.debug('best_fit = {:}'.format(self.best_fit))
        self.clone()
        self.mutate()
        self.evaluate()

        npop = len(self.generations[-1].individuals)
        idx = range(-min(self.NPOP, npop), 0)
        self.generations[-1].individuals = \
                self.generations[-1].individuals[idx]
        self.generations[-1].fitness = \
                self.generations[-1].fitness[idx]
        
        # prevent degeneration
        best_fit = self.best_fit
        self.generations[-1].individuals[0] = self.best_individual
        self.generations[-1].fitness[0] = best_fit

        self._best_fit0 = copy.copy(self.best_fit)


    def evolve(self, ngen=1):

        for i in range(ngen):
            self._evolve()


        

        
