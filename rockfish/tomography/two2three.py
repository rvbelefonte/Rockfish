"""
Methods for creating 3D models from 2D models.
"""
import numpy as np
from scipy.interpolate import interp1d, interp2d
import warnings
from rockfish.tomography.model import VM


def project_point(x, y, theta):
    """
    Project a point onto a line.

    :param x, y: Coordinates of the point to project.  Can be scalars or
        :class:`numpy.ndarray` arrays.
    :param theta: Angle of the line measured clock-wise from the x axis.
    :returns: radius, x coordinate on line, y coordinate on line.
    """
    beta = theta - np.arctan2(y, x)
    r = np.sqrt(x ** 2 + y ** 2) * np.cos(beta)
    xp = r * np.cos(theta)
    yp = r * np.sin(theta)
    return r, xp, yp


def two2three(vm, sol, eol, dx=None, dy=None):
    """
    Convert a 2D model to a 3D model by giving the coordinates of the line
    endpoints.

    Creates a cube with edges that are oriented parallel to the coordinate
    system.
    
    :See also: :meth:`rockfish.tomography.model.VM.extrude`

    :param sol: ``tuple`` of ``(x, y)`` coordinates for the start of the
        line.
    :param eol: ``tuple`` of ``(x, y)`` coordinates for the end of the
        line.
    :param dx: grid spacing in the x direction.  Default is to set
        ``dx`` equal to current model grid spacing in the x-direction.
    :param dy: grid spacing in the y direction.  Default is to set
        ``dy`` equal to the grid spacing in the x-direction.
    """
    # check that current model is 2D
    assert vm.ny == 1, 'Current model must be 2D with ny=1.'
    # set defaults
    if dx is None:
        dx = vm.dx
    if dy is None:
        dy = vm.dx
    # calculate line angle 
    theta = np.arctan2(eol[1] - sol[1], eol[0] - sol[0])
    # initialize a new model
    vm1 = VM(r1=(sol[0], sol[1], vm.r1[2]), 
             r2=(eol[0], eol[1], vm.r2[2]),
             dx=dx, dy=dy, nr=vm.nr)
    # build surface interpolators
    x2rf = []
    x2jp = []
    x2ir = []
    x2ij = []
    xp = vm.x - vm.r1[0]    # x in 2D model relative to 2D origin
    for iref in range(0, vm.nr):
        x2rf.append(interp1d(xp, [v[0] for v in vm.rf[iref]],
                             kind='linear'))
        x2jp.append(interp1d(xp, [v[0] for v in vm.jp[iref]],
                             kind='linear'))
        x2ir.append(interp1d(xp, [v[0] for v in vm.ir[iref]],
                             kind='nearest'))
        x2ij.append(interp1d(xp, [v[0] for v in vm.ij[iref]],
                             kind='nearest'))
    # map 2D model to the 3D model
    x = vm1.x - vm1.r1[0]   # x in 3D model relative to origin

    for _iy in vm1.yrange2i():
        _y = vm1.y[_iy] - vm1.r1[1]  # y in 3D model relative to origin
        a, _, _ = project_point(x, _y, theta)
        a = a.clip(vm.r1[0], vm.r2[0])
        nclip = len(np.nonzero(a == vm.r1[0]))\
                + len(np.nonzero(a == vm.r2[0]))
        if nclip > 2:
            warnings.warn('{:} points off the 2D line at y={:}'\
                          .format(nclip - 2, _y))
        # interpolate interface values
        for iref in range(0, vm.nr):
            try:
                vm1.rf[iref, :, _iy] = x2rf[iref](a)
                vm1.jp[iref, :, _iy] = x2jp[iref](a)
                vm1.ir[iref, :, _iy] = x2ir[iref](a)
                vm1.ij[iref, :, _iy] = x2ij[iref](a)
            except ValueError as e:
                msg = e.message
                msg += ' (min(a),max(a)={:},{:}; vm.r1[0]={:}; vm.r2[0]={:})'\
                        .format(min(a), max(a), vm.r1[0], vm.r2[0])
                raise ValueError(msg)
        # assign velocities
        for _ix, _a in enumerate(a):
            _ixp = vm.x2i([_a])[0]
            vm1.sl[_ix, _iy, :] = vm.sl[_ixp, 0, :]

    return vm1
