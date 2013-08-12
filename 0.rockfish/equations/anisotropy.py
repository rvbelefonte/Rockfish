"""
Anisotropy equations.
"""
from copy import copy
import numpy as np


def transverse(theta, *ai):
    """
    Wavespeed variation with azimuth in transversely isotropic media.

    Parameters
    ----------
    theta : array_like
        Azimuth values in degrees.
    a0, a1, ..., a4 : array_like
        Matrices with values for the anisotropy parameters. Must all be
        of shape ``(N0, N1, ..., N4)``.

    Returns
    -------
    V : array_like
        Matrix of wavespeed values with the shape
        ``(len(theta), N0, N1, ..., N4)``.

    Examples
    --------

    >>> from rockfish.equations.anisotropy import transverse
    >>> transverse([0, 45, 90, 135, 180], 8.5, 1, 1, 1, 1)
    [10.5, 8.5, 8.5, 6.5, 10.5]
    >>> transverse([0, 45, 90], 8.5, 1, 1)
    [9.5, 9.5, 7.5]
    >>> transverse([0, 45, 90], 8.5, 0.5, 0.5)
    [9.0, 9.0, 8.0]
    >>> transverse([0, 45, 90], [8.5, 8.5], [1, 0.5], [1, 0.5])
    [array([ 9.5,  9. ]), array([ 9.5,  9. ]), array([ 9.5,  9. ])]

    """
    ai = np.asarray(ai)
    shape = ai[0].shape
    for _ai in ai:
        assert _ai.shape == shape

    V = []
    for _theta in np.deg2rad(theta):
        if len(ai) > 0:
            _V = 1. * ai[0]
        if len(ai) > 1:
            _V += ai[1] * np.cos(2 * _theta)
        if len(ai) > 2:
            _V += ai[2] * np.sin(2 * _theta)
        if len(ai) > 3:
            _V += ai[3] * np.cos(4 * _theta)
        if len(ai) > 4:
            _V += ai[4] * np.sin(4 * _theta)
        V.append(_V)
    return V


def velocity2delaytime(dist, vel, vel0=np.max, noise=0.):
    """
    Calculate relative travel times for a set of velocities.


    Parameters
    ----------
    vel : array_like
        Velocities to calculate delay times for.
    dist : array_like
        Distances to calculate traveltimes for.
    vel0 :  {float, callable}, optional
        Reference velocity or callable function used to calculate the
        reference velocity.  If callable, ``vel0`` should take ``vel``
        as its argument. Default is :meth:``numpy.max``.
    noise : float, optional
        Maximum amplitude of random noise to apply to the delay time.
        Default is ``0.0``.

    Returns
    -------
    dt : array_like
        Matrix of delaytimes with shape ``len(dist), shape(vel)``.

    Examples
    --------

    >>> from rockfish.equations.anisotropy import velocity2delaytime
    >>> velocity2delaytime([50.], [7.5, 8.0, 8.5], vel0=7.5)
    [array([ 0.        , -0.41666667, -0.78431373])]
    """
    _vel = np.asarray(vel)
    _dist = np.asarray(dist)
    if hasattr(vel0, '__call__'):
        vel0 = vel0(_vel)
    n = len(vel)
    dt = []
    for x in _dist:
        dt.append(x / _vel - x / vel0)
        if noise != 0.:
            dt[-1] += 2. * noise * (np.random.rand(n) - 0.5)
    return dt

if __name__ == "__main__":
    import doctest
    doctest.testmod()
