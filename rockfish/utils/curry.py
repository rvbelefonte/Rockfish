
class Curry:
    """
    Tie up a function with parameters so it can be called later. 
    
    Taken from the Python Cookbook.
    See <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52549>_.
    """
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.pending = args[:]
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs
        return self.func(*(self.pending + args), **kw)
