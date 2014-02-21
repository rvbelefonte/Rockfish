"""
Module for handling population evolution
"""
import copy
import numpy as np
from functools import partial
from population import Population

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


class Evolver(Toolbox):

    def __init__(self, ind0, evaluate, *args, **kwargs):

        pm = kwargs.pop('pm', 0.5)
        px = kwargs.pop('px', 0.5)

        self.gen = [Population(ind=ind0, pm=pm, px=px)]

        self.register('_evaluate', evaluate, *args, **kwargs)
        self.evaluate()

    def __str__(self, extended=False):

        banner = '=' * 78 + '\n'

        sng = banner
        sng += 'Generation {:}\n'.format(len(self.gen) - 1)
        sng += banner

        if extended:
            sng += 'Includes:\n'
            
            for i in range(self.pop.size):
                sng += '  {:} {:}\n'.format(self.pop.fit[i], self.pop.ind[i])

            sng += '-' * 78 + '\n'

        sng += 'Best fitness: {:}\nBest individual: {:}\n'\
                .format(*self.best_fit)

        return sng

    def _get_pop(self):
        return self.gen[-1]

    pop = property(fget=_get_pop)

    def _get_best_fit(self):
        ibest = np.argmax([g.fit[0] for g in self.gen])
        return self.gen[ibest].fit[0], self.gen[ibest].ind[0]
    best_fit = property(fget=_get_best_fit)

    def evaluate(self):
        inew = self.pop.inew 
        self.pop.fit[inew] = self._evaluate(self.pop.ind[inew])

    def _evolve(self, **kwargs):

        self.gen.append(copy.deepcopy(self.pop))

        self.pop.clone()
        self.pop.cross(**kwargs)
        self.pop.mutate(**kwargs)
        self.evaluate()

