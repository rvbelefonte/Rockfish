"""
Utilities for working with raypaths
"""
import numpy as np
from scipy.interpolate import Rbf
from rockfish.tomography.model import VM
from rockfish.tomography.geometry.utils import point_in_poly, line_plane_isect


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
    return np.asarray([vm.point2layer(*pt) for pt in zip(px, py, pz)])

def split_downup(px, py, pz, pi=None):
    """
    Split down-going and up-going raypaths

    Parameters
    ----------
    px, py, pz : array_like
        Arrays of x, y, z coordinates. Must all be the same size.

    pi: array_like, optional
        Array of layer indices for all points. If given, this array is also
        split into down- and up-going legs.
    
    Returns
    -------
    down, up: numpy.ndarray
        Arrays of (x, y, z) coordinates for the downgoing and upgoing paths.
    """
    dz = np.diff(pz)
    iup = np.append(np.nonzero(dz < 0), [len(pz) - 1])
    idn = np.append(np.nonzero(dz > 0), [iup[0]])

    if len(iup) == 1:
        iup = []

    if len(idn) == 1:
        idn = []

    if pi is None:
        return np.asarray([px[idn], py[idn], pz[idn]]).T,\
                np.asarray([px[iup], py[iup], pz[iup]]).T
    else:
        return np.asarray([px[idn], py[idn], pz[idn], pi[idn]]).T,\
                np.asarray([px[iup], py[iup], pz[iup], pi[iup]]).T

def get_points_in_layer(vm, ilyr, px, py, pz, pi=None, overlap=False):
    """
    Selects points that are within a layer

    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    ilyr: int
        Index of a layer in the velocity model
    px, py, pz : array_like
        Arrays of x, y, z coordinates of points along a path.
    pi: array_like, optional
        Array of layer indices for all points

    overlap: bool, optional
        If True, the first point in the over- and under-lying layers are
        included.  Useful when the full path within a layer is of interest.
    
    Returns
    -------
    px, py, pz, pi: numpy.ndarray
        Arrays of x, y, z coordinates and layer indices for all points.
    """
    if len(px) == 0:
        return [], [], [], []

    if pi is None:
        pi = assign_points_to_layers(vm, px, py, pz)

    idx = list(np.nonzero(pi == ilyr)[0])
        
    if (len(idx) == 0) and ((min(pi) >= ilyr) or (max(pi) <= ilyr)):
        # path does not cross layer
        return [], [], [], []

    if overlap:
        dpi = pi - ilyr
        if len(idx) == 0:
            # include at least one point from above
            iabove = np.nonzero(dpi < 0)[0]
            idx = [iabove[-1]]
        
        #if len(idx) == 1:
        #    # include at least one point from below
        #    ibelow = np.nonzero(dpi > 0)[0]
        #    idx = [ibelow[0]]

        # include neighboring points
        idx = [max(0, idx[0] - 1)] + idx
        idx += [min(len(pi) - 1, idx[-1] + 1)]
        idx = np.unique(idx)

    return px[idx], py[idx], pz[idx], pi[idx]

def find_line_intersection(vm, iref, l1, l2):
    """
    Find coordinates of intersection between a line and an interface

    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    iref: int
        Index of an interface in the velocity model
    l1, l2: array_like
        x, y, z coordinates of line endpoints.

    Returns
    -------
    x, y, z: numpy.ndarray
        x, y, z coordinates of intersection point
    """
    # grid between the points
    xi = np.sort(vm.x2x([l1[0] - vm.dx, l2[0] + vm.dx]))
    yi = np.sort(vm.y2y([l1[1] - vm.dx, l2[1] + vm.dy]))
    ix = vm.xrange2i(*xi)
    iy = vm.yrange2i(*yi)
    xx, yy = np.meshgrid(vm.x[ix], vm.y[iy], indexing='ij')
    ixx, iyy = np.meshgrid(ix, iy, indexing='ij')
    zz = vm.rf[iref][ixx, iyy]

    # search all polygons
    isect = None
    for i in range(len(ix) - 1):
        for j in range(len(iy) - 1):
            p1 = (xx[i, j], yy[i, j], zz[i, j])
            p2_0 = (xx[i + 1, j], yy[i + 1, j], zz[i + 1, j])
            p2_1 = (xx[i, j + 1], yy[i, j + 1], zz[i, j + 1])
            p3 = (xx[i + 1, j + 1], yy[i + 1, j + 1], zz[i + 1, j + 1])

            for p2 in [p2_0, p2_1]:
                x, y, z = line_plane_isect(p1, p2, p3, l1, l2)
                if point_in_poly(p1, p2, p3, x, y, z):
                    return x, y, z
        
    return

def _trim_path_ends_to_layer(vm, px, py, pz, pi=None):
    """
    Trims path ends to the layer boundaries

    .. Note:: This function assumes that only the first and/or last points
        may lie outside the layer of interest.  That is, pi[0] != pi[1] and
        pi[-2] != pi[-1], and pi[1] = pi[-2] = layer of interest. This is
        true for paths processed by (1) split_downup() and
        (2) get_points_in_layer(overlap=True).

    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    px, py, pz : array_like
        Arrays of x, y, z coordinates of points along a path.
    
    Returns
    -------
    px, py, pz: numpy.ndarray
        Arrays of x, y, z coordinates of points along the trimmed path.
    """
    # get points for portion of segment that crosses layer
    if pi is None:
        pi = assign_points_to_layers(vm, px, py, pz)

    # trim start of line
    if pi[0] != pi[1]:
        iref = pi[1] - 1
        pt0 = [px[0], py[0], pz[0]]
        pt1 = [px[1], py[1], pz[1]]
        isect = find_line_intersection(vm, iref, pt0, pt1) 

        assert isect is not None, 'Problem finding intersection with'\
                ' iref = {:} between {:} and {:}.'.format(iref, pt0, pt1)

        px[0], py[0], pz[0] = isect

    # trim end of line
    if pi[-2] != pi[-1]:
        iref = pi[-1] - 1
        pt0 = [px[-2], py[-2], pz[-2]]
        pt1 = [px[-1], py[-1], pz[-1]]

        isect = find_line_intersection(vm, iref, pt0, pt1) 

        assert isect is not None, 'Problem finding intersection with'\
                ' iref = {:} between {:} and {:}.'.format(iref, pt0, pt1)

        px[-1], py[-1], pz[-1] = isect

    return px, py, pz


def insert_intersections(vm, px, py, pz, pi=None, duplicate=False):
    """
    Insert points where path crosses interfaces

    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    px, py, pz : array_like
        Arrays of x, y, z coordinates of points along a path.
    pi: array_like, optional
        Array of layer indices for all points.  If these are already known,
        they can be passed to speed execution.
    duplicate: bool, optional
        If True, two points are added for each intersection: one with the
        layer index of the overlying layer and one with the layer index of the
        underlying layer.  Useful for dividing paths by layer.
    
    Returns
    -------
    px, py, pz, pi: numpy.ndarray
        Arrays of x, y, z coordinates and layer indices for points along the
        path with intersections added.
    """
    if pi is None:
        pi = assign_points_to_layers(vm, px, py, pz)

    _px = np.asarray(px[:], dtype='Float64')
    _py = np.asarray(py[:], dtype='Float64')
    _pz = np.asarray(pz[:], dtype='Float64')
    _pi = np.asarray(pi[:], dtype='Float64')

    _i = 0
    for i in range(1, len(pi)): # check all points
        if pi[i] != pi[i - 1]: # just crossed interface
            p0 = [px[i - 1], py[i - 1], pz[i - 1]]
            p1 = [px[i], py[i], pz[i]]

            # loop over interfaces between points
            for ir in np.arange(*np.sort([pi[i - 1], pi[i]])):

                isect = find_line_intersection(vm, ir, p0, p1)

                if isect is not None:
                    x, y, z = isect

                    if duplicate:
                        j = [0, 1]
                    else:
                        j = [0]

                    for _j in j:
                        _px = np.insert(_px, i + _i, x)
                        _py = np.insert(_py, i + _i, y)
                        _pz = np.insert(_pz, i + _i, z)
                        _pi = np.insert(_pi, i + _i, ir + _j)

                        _i += 1
                    
    return _px, _py, _pz, _pi


def split_path_at_interface_intersections(vm, px, py, pz):
    """
    Splits path into segments within each layer.

    
    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    px, py, pz : array_like
        Arrays of x, y, z coordinates of points along a path.
    
    Returns
    -------
    segments: list
        List with nlayers rows of npaths x [x, y, z] coordinates.
        If a path does not cross a layer, an empty ([]) list is included as
        a placeholder.
    """
    segments = []
    for ilyr in range(vm.nr + 1):
        segments.append([[], []])

    dn, up = split_downup(px, py, pz)
    for i, p in enumerate([dn, up]):
        if len(p) == 0:
            continue

        _px, _py, _pz, _pi = insert_intersections(vm, p[:, 0], p[:, 1],
                                                  p[:, 2], duplicate=True)
        for ilyr in range(vm.nr + 1):
            idx = np.nonzero(_pi == ilyr)[0]

            segments[ilyr][i] = np.asarray([_px[idx], _py[idx], _pz[idx]]).T

    return segments

def resample_path(px, py, pz, dx, dy=None, function='linear'):
    """
    Resample a path

    Parameters
    ----------
    px, py, pz : array_like
        Arrays of x, y, z coordinates of points along a path.
    dx : float
        New sample interval for the x-dimension
    dy : float, optional
        New sample interval for the y-dimension.  Default is to set dx=dy.
    function : str or callable, optional
        The radial basis function, based on the radius, r, given by the norm
        (default is linear distance).  See :method:`scipy.interpolate.rbf.Rbf`
        for more information.

    Returns
    -------
    px, py, pz : array
        Arrays of x, y, z coordinates of points along a path.
    """
    f = Rbf(px, py, pz, function=function)

    xi = np.arange(min(px), max(px) + dx, dx)


    if dy is None:
        dy = dx
    
    yi = np.arange(min(py), max(py) + dy, dy)

    return xi, yi, f(xi, yi)
