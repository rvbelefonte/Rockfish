"""
Module for working with evolving populations
"""
import numpy as np
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

        self.generations = [Population(individuals=individuals,
            fitness=kwargs.pop('fitness', None), new_flag=self.NEW_FLAG)]

        self.register('_evaluate', evaluate, *args, **kwargs)
        self.evaluate()

        # register the default tools
        self.register('_rank', tools.linear_rank, sp=2)
        self.register('_mutate', tools.bga_mutate, r=0.1, k=0.001)

    def _get_ibest_fit(self):
        return np.argmax([g.fitness[-1] for g in self.generations\
                if not np.isnan(g.fitness[-1])])

    ibest_fit = property(fget=_get_ibest_fit)

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
        f1 = self._mutate(self.generations[-1]._individuals)

        inew = np.nonzero(np.sum(self.generations[-1]._individuals - f1,
            axis=1))

        self.generations[-1]._individuals = f1
        self.generations[-1]._fitness[inew] = self.NEW_FLAG

    def clone(self, growth_factor=1.):
        nchild = np.round(self.rank() * growth_factor)
        f1 = tools.clone(self.generations[-1].individuals, nchild)
        fit1 = tools.clone(self.generations[-1].fitness, nchild)

        self.generations.append(Population(individuals=f1, fitness=fit1,
            new_flag=self.NEW_FLAG))

        self.generations[-1].fitness =\
                tools.clone(self.generations[-1].fitness, nchild)

    def _evolve(self):

        self.clone()
        self.mutate()
        self.evaluate()


    def evolve(self, ngen=1):

        for i in range(ngen):
            self._evolve()


        

        
