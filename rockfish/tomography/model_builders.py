"""
Helper functions for building initial models.
"""
import numpy as np


def add_layers(vm, h, v=None):
    """
    Add a set of interfaces and velocities to velocity model.

    Parameters
    ----------
    vm : :class:`rockfish.tomography.VM` instance that is modified by
        adding new interfaces and defining new velocities.
    h : array_like
        Array of interface depths.  Each element must be a scalar (constant
        depth) or an array of depths with shape ``(vm.nx, vm.ny)``.
    v : array_like, optional
        Array of layer velocity specifications for each new layer with
        a top defined by the elements of ``h``. Each element should
        be a tuple of ``(method, ai)`` where ``method`` is
        a callable function that takes ``vm`` as the first argument,
        the layer index as the second argument, and ``ai`` as
        the remaining arguments. Setting any element of ``v`` to ``None``
        will leave velocities within that layer unchanged. Default is to
        just add interfaces and leave all velocities unchanged.
    """
    if v is not None:
        assert len(h) == len(v), \
                'h must have the same length as v'

    # Insert interfaces
    iref = []
    for i, _h in enumerate(h):
        if np.asarray(_h).shape == ():
            # constant interface depths
            _h *= np.ones((vm.nx, vm.ny))
            _iref = vm.insert_interface(_h)
        elif np.asarray(_h).shape == (vm.nx, vm.ny):
            # explictly defined interface depths
            _iref = vm.insert_interface(_h)
        else:
            msg = 'h[{:}] is not a scalar or an (nx, ny) sized array.'\
                    .format(i)
            raise ValueError(msg)
        iref.append(_iref)

    # Define velocities
    if v is not None:
        for i, _iref in enumerate(iref):
            if v[i] is not None:
                v[i][0](vm, _iref + 1, *v[i][1:])
