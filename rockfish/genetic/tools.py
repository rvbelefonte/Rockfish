"""
Tools for working with genetic algorithms
"""
import numpy as np
from functools import partial
from scipy.optimize import newton

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



def position(a, axis=0):
    """
    Take a list of numbers and return the sorted position number
    """
    order = np.argsort(a, axis=axis)
    return order.argsort(axis=axis)

def linear_rank(fitness, sp=2):
    """
    Rank individuals using a linear scheme.

    Consider n the number of individuals in the population, pos the
    position of an individual in this population (least fit individual has
    pos=1, the fittest individual pos=n) and sp the selective pressure.
    The fitness value for an individual is calculated as:

    $$fit(pos) = 2 - sp + 2(sp - 1)(pos - 1)/(n - 1)$$

    Linear ranking allows values of selective pressure in [1.0, 2.0].

    Parameters
    ----------
    fit: array_like
        Array of fitness values
    sp: float
        Selection pressure.  Must be a value between 1 and 2.

    Returns
    -------
    rank: array_like
        Array of rank values
    """
    assert (sp >= 1.) and (sp <= 2.), 'sp must be in the interval [1, 2]'
    n = len(fitness)
    pos = position(fitness) + 1. 

    rank = 2. - sp + 2. * (sp - 1.) * (pos - 1.) / (n - 1.)

    return rank
       
def bga_mutate(values, r=0.1, k=0.001):
    """
    Mutate values as described by the Breeder Genetic Algorithm.

    Values are modifed according to:

    values[i] += s * r * values[i] * a

    where:

    i is choosen uniformly at random from {1, 2, ..., n}
    s is choosen uniformly at random from {-1., 1.}
    r is the mutation range (0.1 is the default)
    a = 2 ** (-u * k)
    u is chooden uniformly at random from {0., 1}
    k is the mutation precision


    References
    ----------
    The Breeder Genetic Algorithm - a provable optimal search algorithm and
    its application. Colloquium on Applications of Genetic Algorithms, 
    IEE 94/067, London, 1994.

    Muhlenbein, H. and Schlierkamp-Voosen, D.: Predictive Models for the
    Breeder Genetic Algorithm: I. Continuous Parameter Optimization.
    Evolutionary Computation, 1 (1), pp. 25-49, 1993.
    """

    values = np.atleast_1d(values)
    shape0 = values.shape

    values = values.flatten()

    n0 = len(values)
    imutate = np.random.randint(0, n0, np.random.randint(n0))

    n = len(imutate)
    s = 2. * (np.random.rand(n) - 0.5)
    u = np.random.rand(n)
    a = 2. ** (-u * k)

    values[imutate] += s * r * values[imutate] * a

    return values.reshape(shape0)


def clone(values, nchildren):
    """
    Clones a set of numbers

    Parameters
    ----------
    values: array_like
        Values to copy

    nchildren: array_like
        Number of children to produce from each value in values

    Returns
    -------
    children: np.ndarray
        Cloned values
    """
    values = np.atleast_1d(values)
    i0 = 0
    children = np.zeros(np.append((np.sum(nchildren)), values.shape[1:]))
    for n, v in zip(nchildren, values):
        i1 = i0 + n
        children[i0:i1] = v
        i0 = i1

    return children
