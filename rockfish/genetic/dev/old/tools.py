"""
Tools for working with genetic algorithms
"""
import numpy as np
from scipy.optimize import newton

def linear_rank(fit, sp=2):
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
    n = len(fit)
    pos = np.argsort(fit) + 1.
    rank = 2. - sp + 2. * (sp - 1.) * (pos - 1.) / (n - 1.)

    return rank
       
def nonlinear_rank(fit, sp=2):
    """
    Rank indiviuals using a non-linear scheme.
    """
    # FIXME not working yet
    n = len(fit)
    assert (sp >= 1.) and (sp <= n - 2.),\
            'sp must be in the interval [1, n - 2] = [1, {:}]'\
            .format(n - 2)

    xfunc = lambda x, sp, n: (sp - n) * x **(n - 1)\
            + np.sum([sp * (x ** (n - i)) for i in np.arange(2, n + 1)])\
            + sp

    x = newton(xfunc, 0., args=(sp, n))

    norm = np.sum(np.power(x * np.ones(n), [i - 1 for i in range(1, n + 1)]))

    pos = np.argsort(fit)
    rank = (n * (x ** (pos - 1.))) / norm

    raise NotImplementedError

    return rank

def bga_mutate(values, r=0.1, k=0.0001):
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
    i = np.random.randint(0, n0, np.random.randint(n0))

    n = len(i)
    s = 2. * (np.random.rand(n) - 0.5)
    u = np.random.rand(n)
    a = 2. ** (-u * k)

    values[i] += s * r * values[i] * a

    return values.reshape(shape0)





