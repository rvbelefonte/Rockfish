"""
Tools for working with raypath geometries.
"""
import numpy as np
from scipy.interpolate import interp1d
from shapely.geometry import LineString


def distance(pt0, pt1):
    """
    Cartesian distance between two points.

    Parameters
    ----------
    pt0, pt1 : tuple 
         Coordinates for the first and second points.

    Returns
    -------
    r : float
        Distance between pt0 and pt1
    """
    s2 = 0
    for i in range(len(pt0)):
        s2 += (pt1[i] - pt0[i]) ** 2
    return np.sqrt(s2)


def assign_points_to_layers(vm, px, py, pz):
    """
    Determine layer indices for a series of points. 
    
    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    px, py, pz : array_like
        Arrays of x, y, z coordinates to find layers for.  Must all be the
        same size.

    Returns
    -------
    pi : numpy.ndarray
        Layer index for each point.
    """
    pi = []
    for pt in zip(px, py, pz):
        pi.append(vm.point2layer(*pt))
    return pi


def get_indices_near_piercing(pi, iref, downward=True, upward=True):
    """
    Indentify points that are near where the path crosses a surface.

    Parameters
    ----------
    pi: array_like
        Indices of layers containing each point along a path.
    iref: int
        Index of the interface of interest.
    downward: bool, optional
        Determines whether or not to include peircing points on the downward
        leg.
    upward: bool, optional
        Determines whether or not to include peircing points on the upward
        leg.

    Returns
    -------
    ip : list
        List of tuples with ``(i_above, i_below)`` for each piercing point,
        where ``i_above`` and ``i_below`` are the indices of points in ``pi``.
    """
    pi = np.asarray(pi)
    j0 = []
    j1 = []
    if downward: 
        # points near crossing on the downward leg
        i0 = np.nonzero(np.diff(pi) > 0)[0] #  above
        i1 = i0 + 1 #  below
        j0 = list(i0[np.nonzero(pi[i0] == iref)])
        j1 = list(i1[np.nonzero(pi[i1] == iref + 1)])
    if upward: 
        # points near crossing on the upward leg
        i1 = np.nonzero(np.diff(pi) < 0)[0] #  below
        i0 = i1 + 1 #  above
        j0 += list(i0[np.nonzero(pi[i0] == iref)])
        j1 += list(i1[np.nonzero(pi[i1] == iref + 1)])
    return zip(j0, j1)


def get_piercing_points(vm, iref, px, py, pz, ip):
    """
    Find where a path crosses an interface.

    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    iref : int
        Index of the interface of interest.
    px, py, pz: array_like
        1D arrays of x, y, z coordinates along a path. Must all have the 
        same length and should be ordered sequentially.
    ip : list
        List of tuples with ``(i_above, i_below)`` for each piercing point,
        where ``i_above`` and ``i_below`` are the indices of points in
        ``px, py, pz``.

    Returns
    -------
    pp : numpy.ndarray
        N x 3 array of piercing point coordinates.
    """
    pp = np.zeros((len(ip), 3))
    for i, _ip in enumerate(ip):
        # points on path closest to the piercing point
        p0 = (px[_ip[0]], py[_ip[0]], pz[_ip[0]])
        p1 = (px[_ip[1]], py[_ip[1]], pz[_ip[1]])
        pline = LineString([(0, p0[2]), 
                            (distance(p0[0:2], p1[0:2]), p1[2])])
        # surface coordinates between the nearest points
        ix = vm.xrange2i(*np.sort([p0[0], p1[0]]))
        iy = vm.yrange2i(*np.sort([p0[1], p1[1]]))
        z = vm.rf[iref][ix, iy]
        xx, yy = np.meshgrid(vm.i2x(ix), vm.i2y(iy))
        sr = np.zeros(len(z))
        for j in range(1, len(z)):
            sr[j] = distance((xx[0][0], yy[0][0]), (xx[j][0], yy[j][0]))
        sline = LineString(zip(sr, z))
        # get crossing point
        ppr, ppz = pline.intersection(sline).xy
        ppx = interp1d(sr, xx.flatten())(ppr)
        ppy = interp1d(sr, yy.flatten())(ppr)
        pp[i] = [ppx[0], ppy[0], ppz[0]]
    return pp

def get_path_in_layer(vm, ilyr, px, py, pz):
    """
    Find coordinates where a path is within a layer.

    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    ilyr : int
        Index of the layer of interest.
    px, py, pz: array_like
        1D arrays of x, y, z coordinates along a path. Must all have the 
        same length and should be ordered sequentially.

    Returns
    -------
    down, up
        Lists of (x, y, z) coordinates for the downgoing and upgoing
        portions of the path that are in the specified layer. If the path
        turns within a layer, ``up = None``.
    """
    full_path = np.asarray(zip(px, py, pz))
    
    # get indices of points near piercing points
    pi = assign_points_to_layers(vm, px, py, pz)
    ip0 = get_indices_near_piercing(pi, ilyr - 1) #  top
    ip1 = get_indices_near_piercing(pi, ilyr) #  bottom

    # get piercing points
    if len(ip0) > 0:
        pp0 = get_piercing_points(vm, ilyr - 1, px, py, pz, ip0)
    else:
        pp0 = None
    if len(ip1) > 0:
        pp1 = get_piercing_points(vm, ilyr, px, py, pz, ip1)
    else:
        pp1 = None

    # collect coordinates for the downgoing leg
    if pp0 is not None:
        down = [pp0[0]]
    else:
        down = [] 
    if len(ip0) == 0:
        i0 = 0
    else:
        i0 = ip0[0][1]
    if len(ip1) > 0:
        i1 = ip1[0][0]
    else:
        i1 = ip0[1][1]
    down += list(full_path[i0:i1 + 1])
    if pp1 is not None:
        down.append(pp1[0])
    else:
        # turns in layer
        down.append(pp0[1])
        return down, None
    
    # collect coordinates for the upgoing leg
    if len(ip1) > 0:
        up = [pp1[1]]
    else:
        up = []
    i0 = ip1[1][0]
    if len(ip0) > 0:
        i1 = ip0[1][1]
    else:
        i1 = len(pi)
    up += list(full_path[i0:i1 + 1])
    if pp0 is not None:
        up.append(pp0[1])
    return down, up
