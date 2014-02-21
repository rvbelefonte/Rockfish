import numpy as np
import logging
import copy
from functools import partial
from bitutils import BitSet


# XXX decpreciating
from bitutils import BitList


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
    Raised if trying to access fitness when it is not set
    """
    pass

class PopulationFittnessDimensionError(PopulationError):
    """
    Raised if trying to set fitness to a size other than npop x 1 
    """
    pass


class Population(object):

    def __init__(self, individuals=[], fitness=None,
            crossover_probability=0.5, mutation_probability=0.5,
            nbits=64):

        self.CROSSOVER_PROBABILITY = crossover_probability
        self.MUTATION_PROBABILITY = mutation_probability
        self.NBITS = nbits
        
        self._fitness = None

        self.individuals = individuals
        self.fitness = fitness

    def _get_npop(self):
        return len(self.individuals)

    npop = property(fget=_get_npop)

    def _get_individuals(self):
        return self._individuals.float

    def _set_individuals(self, value):

        self._fitness = None
        self._individuals = BitSet(value, nbits=self.NBITS) 

    individuals = property(fget=_get_individuals, fset=_set_individuals)

    def _get_fitness(self):
        if self._fitness is None:
            raise PopulationFittnessNotSetError(\
                'Fitness values are not set.  This was likely caused by'\
                + ' updating individuals without redefining fitness.')

        return self._fitness
    
    def _set_fitness(self, value):
        if value is None:
            self._fitness = -1 * np.ones(self.npop)
            return

        value = np.atleast_1d(value)

        if (value.shape != (self.npop,)) and (value.shape != (self.npop, 1)):
            msg = 'fitness must have shape = ({:},1) or ({:},),'\
                    .format(self.npop, self.npop)\
                    + ' but shape = {:}'.format(value.shape)
            raise PopulationFittnessDimensionError(msg)

        self._fitness = value
        
        # sort by fitness
        self.sort()
        
    fitness = property(fget=_get_fitness, fset=_set_fitness)

    def sort(self):
        """
        Sorts individuals and fitness by fitness
        """
        isrt = np.argsort(self._fitness)[::-1]
        self._fitness = self._fitness[isrt] 
        self._individuals = self._individuals[isrt]

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

        logging.debug('nchild = {:}'.format(nchild))

        # XXX does this matter??
        # just update the best indivudals and let the riff raff linger on
        # at the poor-fitness end of the indivudals array
        #assert np.sum(nchild) == self.npop,\
        #        'Population size changed from during reproduction: '\
        #        + '\nnparent={:}, sum(nchild)={:}'.format(self.npop,
        #                np.sum(nchild))

        # copy out children
        # TODO do we need the copy here??
        ind1 = copy.deepcopy(self.individuals)
        fit1 = copy.deepcopy(self.fitness)
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
        ind_shape = self.individuals[0].shape

        new = []
        for i in range(n):
            j = np.random.randint(0, npop, size=2)

            ind0 = self.individuals[j[0]].flatten()
            ind1 = self.individuals[j[1]].flatten()

            for i in range(len(ind0)):

                bits = BitList([ind0[i], ind1[i]])
                bits.crossover()

                ind0[i], ind1[i] = bits.float

            ind0.reshape(ind_shape)
            ind1.reshape(ind_shape)

            self.fitness[j[0]] = -1.0
            self.fitness[j[1]] = -1.0


    def mutate(self, **kwargs):

        p = kwargs.pop('p', self.MUTATION_PROBABILITY)
        logging.debug('mutation p = {:}'.format(p))

        n = np.sum(np.random.rand(self.npop) < p)

        logging.debug('... mutating {:}/{:} indivudals ...'\
                .format(n, self.npop))

        im = np.random.randint(0, self.npop, size=n)

        logging.debug('... selection: im.shape = {:}'.format(im.shape))


        f = self.individuals[im]
        shape0 = f.shape
        f = f.flatten()

        bits = BitList(f)
        bits.invert_rand_significant()

        self.individuals[im] = np.asarray(bits.float).reshape(shape0)

        self.fitness[im] = -1.0

    def _get_inew(self):
        if self._fitness is None:
            return np.arange(self.npop)
        else:
            return np.nonzero(self.fitness == -1)[0]

    inew = property(fget=_get_inew)

class Evolver(Toolbox, Population):
    """
    Class for handling genetic evolution
    """
    def __init__(self, individuals, evaluate, *args, **kwargs):

        self.DEGENERATION = kwargs.pop('degeneration', True)
        
        self.CROSSOVER_PROBABILITY = kwargs.pop('crossover_probability',
                0.5)
        self.CROSSOVER_PROBABILITY =\
                kwargs.pop('px', self.CROSSOVER_PROBABILITY)

        self.MUTATION_PROBABILITY = kwargs.pop('mutation_probability', 0.5)
        self.MUTATION_PROBABILITY =\
                kwargs.pop('pm', self.MUTATION_PROBABILITY)

        self.generations = [Population(individuals=individuals,
            crossover_probability = self.CROSSOVER_PROBABILITY,
            mutation_probability = self.MUTATION_PROBABILITY)]

        self.register('_evaluate', evaluate, *args, **kwargs)
        self.evaluate()

    def _get_individuals(self):
        return self.generations[-1].individuals

    individuals = property(fget=_get_individuals)

    def _get_fitness(self):
        return self.generations[-1].fitness

    def _set_fitness(self, value):
        self.generations[-1].fitness = value
    
    fitness = property(fget=_get_fitness, fset=_set_fitness)

    def _best_fit(self):
        ibest = np.argmax([g.fitness.max() for g in self.generations])

        return self.generations[ibest].individuals[0],\
                self.generations[ibest].fitness[0]

    def _get_best_individual(self):
        return self._best_fit()[0]

    best_individual = property(fget=_get_best_individual)

    def _get_best_fit(self):
        return self._best_fit()[1]

    best_fit = property(fget=_get_best_fit)

    def evaluate(self):
        inew = self.generations[-1].inew
        self.fitness[inew] = self._evaluate(self.individuals[inew])
        self.generations[-1].sort()

    def _evolve(self):
        """
        Helper function that evolves the population by 1 generation
        """
        fit0 = self.fitness.max()
        self.generations.append(copy.deepcopy(self.generations[-1]))

        self.generations[-1].clone()
        self.generations[-1].crossover()
        self.generations[-1].mutate()
        self.evaluate()
        
        fit1 = self.fitness.max()

        # prevent degeneration
        if not self.DEGENERATION and (fit1 < fit0):
            self.generations[-1] = self.generations[-2]

    def evolve(self, ngen=50, target_fitness=np.inf, verbose=True):
        """
        Evolve the population for ngen generations
        """
        if verbose is True:
            verbose = 1
        elif verbose is False:
            verbose = 0

        if verbose >= 1:
            print 'Evolving population by {:} generations...'\
                    .format(ngen)
            print 'Generation  std min mean max'
        

        igen0 = len(self.generations) - 1
        for igen in range(igen0, igen0 + ngen):
            self._evolve()

            #if verbose >= 1:
            #    print '{:}   {:}   {:}   {:}   {:}'\
            #        .format(igen, np.std(self.fitness), self.fitness.min(),
            #                self.fitness.mean(), self.fitness.max())
            
            if verbose >= 2:
                print '    {:} {:}'.format(self.fitness[0],
                        self.individuals[0])

            if verbose >= 3:
                for f, i in zip(self.fitness[1:], self.individuals[1:]):
                    print '    {:} {:}'.format(f, i)

            if self.best_fit >= target_fitness:
                break


        if verbose >= 1:
            print '-' * 80
            print 'Best individual after {:} generations:'.format(ngen)
            print self.best_individual
            print 'Fitness: {:}'.format(self.best_fit)
