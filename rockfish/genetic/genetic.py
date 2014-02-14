import numpy as np
from functools import partial 
from utils import bin2float, float2bin, crossover, mutate


class Toolbox(object):

    def register(self, alias, method, *args, **kargs):
        """
        Register a *method* in the toolbox under the name *alias*. 
        
        You may provide default arguments that will be passed automatically
        when calling the registered method. Fixed arguments can then be 
        overriden at function call time.
        
        Parameters
        ----------
        alias: str
            The name the operator will take in the toolbox. If the
            alias already exist it will overwrite the the operator
            already present.
        method: callable
            The function to which refer the alias.
        *args, **kwargs: 
            One or more argument (and keyword argument) to pass
            automatically to the registered function when called, optional.
        
        The following code block is an example of how the toolbox is used. ::

            >>> def func(a, b, c=3):
            ...     print a, b, c
            ... 
            >>> tools = Toolbox()
            >>> tools.register("myFunc", func, 2, c=4)
            >>> tools.myFunc(3)
            2 3 4
        
        The registered function will be given the attributes :attr:`__name__`
        set to the alias and :attr:`__doc__` set to the original function's
        documentation. The :attr:`__dict__` attribute will also be updated
        with the original function's instance dictionnary, if any.
        """
        pfunc = partial(method, *args, **kargs)
        pfunc.__name__ = alias
        pfunc.__doc__ = method.__doc__
        
        try:
            # Some methods don't have any dictionary, in these cases simply 
            # don't copy it.
            pfunc.__dict__.update(method.__dict__.copy())
        except AttributeError:
            pass
        
        setattr(self, alias, pfunc)


class PopulationError(Exception):
    """
    Base class for Population errors
    """
    pass

class PopulationFittnessNotSetError(PopulationError):
    """
    Raised if trying to access fitnesstness when it is not set
    """
    pass


class Population(Toolbox):

    def __init__(self, individuals=[], fitness=None,
            crossover_probability=0.5, mutation_probability=0.5):

        self.CROSSOVER_PROBABILITY = crossover_probability
        self.MUTATION_PROBABILITY = mutation_probability
        
        self._fitness = None

        self.individuals = individuals
        self.fitness = fitness 

    def _get_npop(self):
        return len(self.individuals)

    npop = property(fget=_get_npop)

    def _get_individuals(self):
        return self._individuals

    def _set_individuals(self, value):

        self._fitness = None
        self._individuals = np.atleast_1d(value)

    individuals = property(fget=_get_individuals, fset=_set_individuals)

    def _get_fitness(self):
        if self._fitness is None:
            raise PopulationFittnessNotSetError(\
                'Fitness values are not set.  This was likely caused by'\
                + ' updating individuals without redefining fitness.')

        return self._fitness
    
    def _set_fitness(self, value):
        if value is None:
            self._fitness = None
            return
        
        self._fitness = np.atleast_1d(value)

        assert len(value) == self.npop,\
            'fitness must have length = len(individuals) = {:}'\
            .format(self.npop)

        # sort by fitness
        isrt = np.argsort(self._fitness)[::-1]
        self._fitness = self._fitness[isrt] 
        self._individuals = self._individuals[isrt]

    fitness = property(fget=_get_fitness, fset=_set_fitness)

    def clone(self):
        """
        Creates a new generation from the current generation, with a bias
        towards individuals with a higher fitness.
        """
        # determine number of children from each individual 
        cumfit = np.cumsum(self.fitness)
        rd = np.sort(np.random.rand(self.npop) * np.sum(self.fitness))
        nchild = np.zeros(self.npop, dtype=np.int)
        nchild[0] = np.sum(rd < cumfit[0])
        for i in range(1, self.npop):
             nchild[i] = np.sum((rd < cumfit[i]) * (rd > cumfit[i - 1]))

        assert np.sum(nchild) == self.npop,\
                'Population size changed during reproduction'

        # copy out children
        ind1 = np.zeros(self.individuals.shape)
        fit1 = np.zeros(self.individuals.shape)
        j = 0
        for i, d in enumerate(zip(self.individuals, self.fitness)):
            _ind0, _fit0 = d
            for _j in range(nchild[i]):
                ind1[j] = _ind0
                fit1[j] = _fit0
                j += 1

        self.individuals = ind1
        self.fitness = fit1


    def crossover(self, **kwargs):
        
        p = kwargs.pop('p', self.CROSSOVER_PROBABILITY)
        
        npop = self.npop
        n = np.sum(np.random.rand(npop) < p)

        new = []
        for i in range(n):
            j = np.random.randint(0, npop, size=2)

            self.individuals[j[0]], self.individuals[j[1]] =\
                    crossover(self.individuals[j[0]],
                            self.individuals[j[1]])

            self.fitness[j[0]] = -1.0
            self.fitness[j[1]] = -1.0


    def mutate(self, **kwargs):

        p = kwargs.pop('p', self.MUTATION_PROBABILITY)

        n = np.sum(np.random.rand(self.npop) < p)
        im = np.random.randint(0, self.npop, size=n)

        self.individuals[im] = mutate(self.individuals[im])
        self.fitness[im] = -1.0

    def _get_inew(self):
        
        return np.nonzero(self.fitness == -1)[0]

    inew = property(fget=_get_inew)
