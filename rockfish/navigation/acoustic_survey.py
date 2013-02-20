"""
Acoustic location for ocean instruments.
"""
import numpy as np

def slant_time(sx, sy, sz, rx, ry, rz, v):
    """
    Calculate simple travel time from a source to a receiver.

    Units for all parameters should be self-consistant.

    :param sx, sy, sz: Cartesian coordinates for the source position(s).
    :param rx, ry, rz: Cartesian coordinates for the receiver position(s).
    :param v: Velocity.
    :returns: Oneway traveltime between the source and receiver.
    """
    d = np.sqrt((rx - sx) ** 2 + (ry - sy) ** 2)
    h = rz - sz
    r = np.sqrt(d ** 2 + h ** 2)
    return r / v

def locate_on_surface(sx, sy, sz, t, x, y, zz, v=1500):
    """
    Find best-fit location on a surface by grid search.

    Uses :meth:`rockfish.navigation.acoustic_survey.slant_range` to calculate
    forward traveltimes to each node on the surface. These times are compared
    to the observed traveltimes to find the position on the surface with the
    minimum misfit.

    :param sx: x coordinates for the traveltime observations.
    :param sy: y coordinates for the traveltime observations.
    :param sz: z coordinates for the traveltime observations.
    :param t: one-way traveltime observations
    :param x: Array of x coordinates for the surface.
    :param y: Array of y coordinates for the surface.
    :param zz: Surface depths given as an len(x) by len(y) sized
        array.
    :param v: Optional. Velocity to use in forward traveltime calculations.
        Default is 1500 (i.e., typical sound velocity of seawater in m/s).
    :returns: [x, y, z, rms] of the best-fit location
    """
    # Check sizes
    assert (len(sx) == len(sy)) and (len(sx) == len(sz))\
            and (len(sx) == len(t)),\
            'Source position and time arrays must all be of the same size.'
    assert np.shape(zz) == (len(x), len(y)),\
            'shape(zz) must equal (len(x), len(y)).'
    # Calculate RMS for each grid node
    rms = [] 
    pos = []
    for ix, _x in enumerate(x):
        for iy, _y in enumerate(y):
            _t = slant_time(sx, sy, sz, _x, _y, zz[ix, iy], v=v)
            rms.append(np.sqrt(np.sum(np.power(_t - t, 2))))
            pos.append([_x, _y, zz[ix, iy]])
    i = np.argmin(rms)
    return pos[i] + [rms[i]]
