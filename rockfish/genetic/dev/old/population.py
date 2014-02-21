"""
Module for working with populations
"""
import copy
import numpy as np
from bitutils import BitSet

class Population(object):
    """
    Class for managing a population
    """
    def __init__(self, ind=[], fit=None, nbits=64, pm=0.5, px=0.5,
            mutate_bit_selection='rand_bits_sign_and_section'):

        self.nbits = nbits
        self.pm = pm
        self.px = px
        self.mutate_bit_selection = mutate_bit_selection

        self.ind = ind
        self.fit = fit

    # Managing individuals and fitness
    def _get_ind(self):
        """
        Returns the individuals as a matrix of floats
        """
        if hasattr(self, '_fit'):
            self.sort()
        return self._ind.float

    def _set_ind(self, values):
        """
        Stores the individuals as a BitSet
        """
        self._ind = BitSet(values, nbits=self.nbits, inplace=True)
    
    ind = property(fget=_get_ind, fset=_set_ind)

    def _get_fit(self):
        """
        Returns values from private fitness array
        """
        self.sort()
        return self._fit

    def _set_fit(self, values):
        """
        Setter for fitness that ensures len() == len(ind)
        """
        if values is None:
            values = np.nan * np.ones(self.size)
        else:
            values = np.asarray(values, dtype='float64')

        if values.shape != (self.size, ):
            msg = 'fit must be an array with shape = (len(ind),) = ({:},)'\
                    .format(self.ind.shape[0])
            msg += ', but fit.shape = {:}'.format(values.shape)
            raise ValueError(msg)
        
        self._fit = values

        self.sort()

    fit = property(fget=_get_fit, fset=_set_fit)

    def _get_inew(self):
        return np.nonzero(np.isnan(self._fit))[0]

    inew = property(fget=_get_inew)

    def _get_isort(self):
        """
        Returns the indices that would sort fit and ind 
        """
        if len(self.inew) == self.size:
            return range(self.size)
        else:
            return np.argsort(self._fit)[::-1]

    isort = property(fget=_get_isort)

    def sort(self, inplace=True):
        """
        Sorts ind and fit by fit
        """
        if inplace:
            pop = self
        else:
            pop = copy.deepcopy(self)

        idx = pop.isort
        flat_idx = pop._ind.flat_idx[idx].flatten()

        pop._ind._bitarray = [pop._ind._bitarray[i] for i in flat_idx]
        pop._fit = pop._fit[idx]

        if not inplace:
            return pop

    # Population statistics
    def _get_size(self):
        return self._ind.shape[0] 
    size = property(fget=_get_size)

    def _get_fit_min(self):
        return self.fit.min()
    fit_min = property(fget=_get_fit_min)
    
    def _get_fit_max(self):
        return self.fit.max()
    fit_max = property(fget=_get_fit_max)

    def _get_fit_mean(self):
        return np.mean(self.fit)
    fit_mean = property(fget=_get_fit_mean)

    def _get_fit_std(self):
        return np.std(self.fit)
    fit_std = property(fget=_get_fit_std)


    # Replication and diversity methods
    def clone(self):
        """
        Create a copy of the population with a bias towards fitter
        individuals
        """
        # determine number of children from each individual 
        cumfit = np.cumsum(self.fit)
        rd = np.sort(np.random.rand(self.size) * np.sum(self.fit))
        nchild = np.zeros(self.size, dtype=np.int)
        nchild[0] = np.sum(rd < cumfit[0])
        for i in range(1, self.size):
             nchild[i] = np.sum((rd < cumfit[i]) * (rd > cumfit[i - 1]))

        ind1 = copy.deepcopy(self.ind)
        fit1 = copy.deepcopy(self.fit)
        j = 0
        for i, d in enumerate(zip(self.ind, self.fit)):
            _ind0, _fit0 = d

            for _j in range(nchild[i]):
                ind1[j] = _ind0
                fit1[j] = _fit0
                
                j += 1

        self.ind = ind1
        self.fit = fit1

    
    def mutate(self, **kwargs):
        """
        Mutate the population by bit flipping
        """
        pm = kwargs.pop('pm', self.pm)
        pos = kwargs.pop('pos', self.mutate_bit_selection)

        n = np.sum(np.random.rand(self.size) < pm)

        im = np.random.randint(0, self.size, size=n)
        idx = [(i, ) for i in im]

        self._ind.invert(pos=pos, idx=idx)
        self.fit[im] = np.nan


    def cross(self, **kwargs):
        """
        Mix bits from individuals in the population
        """
        px = kwargs.pop('px', self.px)
        ncross = np.sum(np.random.rand(self.size) < px)

        for i in range(ncross):
            idx0, idx1 = [(i, ) for i in \
                    np.random.randint(0, self.size, size=2)]

            self._ind.cross(idx0, idx1)

            self.fit[idx0[0]] = np.nan
            self.fit[idx1[0]] = np.nan

    def reproduce(self, inplace=True, **kwargs):
        """
        Clone, mutate, and cross the population
        """
        if inplace:
            pop = self
        else:
            pop = copy.deepcopy(self)

        pop.clone()
        pop.cross(**kwargs)
        pop.mutate(**kwargs)

        if not inplace:
            return pop
