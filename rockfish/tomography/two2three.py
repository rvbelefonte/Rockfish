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

    Parameters
    ----------
    x, y : float, numpy.ndarray
        Coordinates of the point to project.
    theta : float
        Angle of the line measured clockwise from the x axis.

    Returns
    -------
    r, xp, yp : float
        Distance along line and x, y coordinates on line.
    """
    beta = theta - np.arctan2(y, x)
    r = np.sqrt(x ** 2 + y ** 2) * np.cos(beta)
    xp = r * np.cos(theta)
    yp = r * np.sin(theta)
    return r, xp, yp


def project_model_points(vm2d, vm3d, phi, indices=False):
    """
    Project points in a 3D model to points along a 2D model line.

    Parameters
    ----------
    vm2d : :class:`rockfish.tomography.model.VM`
        2D model. Must have ``vm2d.ny==1``.
    vm3d : :class:`rockfish.tomography.model.VM`
        3D model.
    phi : float
        Angle of the 2D line measured clockwise from the x-axis in the
        3D model.
    indices : bool, optional
        Specifies whether to return indices (True) or x-coordinate values
        (False, default).

    Returns
    -------
    x_2d : numpy.ndarray
        Matrix of x-coordinates or x-indices in the 2D model for
        each x, y point in the 3D model. Has shape ``(vm3d.nx, vm3d.ny)``.
    """
    assert vm2d.ny == 1, 'vm2d must be 2D with vm2d.ny == 1'
    x_3d = vm3d.x - vm3d.r1[0]
    x_2d = np.zeros((vm3d.nx, vm3d.ny))
    for _iy in vm3d.yrange2i():
        _y_3d = vm3d.y[_iy] - vm3d.r1[1]
        x_2d[:, _iy], _, _ = project_point(x_3d, _y_3d, phi)
    x_2d = x_2d.clip(vm2d.r1[0], vm2d.r2[0])
    if indices:
        return np.asarray(vm2d.x2i(x_2d.flatten()))\
                .reshape((vm3d.nx, vm3d.ny))
    else:
        return x_2d


def project_layer_velocities(vm2d, vm3d, phi, ilyr_3d, ilyr_2d=None,
                             method='stretch'):
    """
    Project velocities from a 2D model into a 3D model.

    At each x, y position,  velocities from the 2D layer are stretched 
    (or compressed) in the vertical direction to fit into the 3D layer.

    Parameters
    ----------
    vm2d : :class:`rockfish.tomography.model.VM`
        2D model. Must have ``vm2d.ny==1``.
    vm3d : :class:`rockfish.tomography.model.VM`
        3D model.
    phi : float
        Angle of the 2D line measured clockwise from the x-axis in the
        3D model.
    ilyr_3d : int
        Index of the layer in the 3D model to project velocities into.
    ilyr_2d : int, optional
        Index of the layer in the 2D model to project velocities from.
        Default is to set ``ilyr_2d==ilyr_3d``.
    """
    if ilyr_2d is None:
        ilyr_2d = ilyr_3d
    ix_2d = project_model_points(vm2d, vm3d, phi, indices=True)
    z_2d = vm2d.get_layer_bounds(ilyr_2d)
    z_3d = vm3d.get_layer_bounds(ilyr_3d)
    for ix in vm3d.xrange2i():
        for iy in vm3d.yrange2i():
            # get slowness collumn from 2d model
            _z0_2d = z_2d[0][ix_2d[ix, iy], 0]
            _z1_2d = z_2d[1][ix_2d[ix, iy], 0]
            iz_2d = vm2d.zrange2i(_z0_2d, _z1_2d)
            sl_2d = vm2d.sl[ix_2d[ix, iy], 0, iz_2d]
            # get depth range in 3d model 
            _z0_3d = z_3d[0][ix, iy]
            _z1_3d = z_3d[1][ix, iy]
            iz_3d = vm2d.zrange2i(_z0_3d, _z1_3d)
            # fit 2d range into 3d range
            n2d = len(iz_2d)
            n3d = len(iz_3d)
            i2d = np.arange(n2d)
            i3d = np.arange(n3d) * float(n2d) / float(n3d)
            z2sl = interp1d(i2d, sl_2d)
            vm3d.sl[ix, iy, iz_3d] = z2sl(np.clip(i3d, 0, i2d[-1]))


def two2three(vm, sol, eol, dx=None, dy=None, phi=90.0):
    """
    Convert a 2D model to a 3D model by giving the coordinates of the line
    endpoints.

    Creates a cube with edges that are oriented parallel to the coordinate
    system.
    
    :See also: :meth:`rockfish.tomography.model.VM.extrude`
    
    Parameters
    ----------
    vm : :class:`rockfish.tomography.model.VM`
        2D model to convert to a 3D model. Must have ``vm.ny==1``.
    sol, eol : (float, float)
        Coordinates for the start and end of the line, respectively.
    dx : float, optional
        Grid spacing in the x direction. Default is to use the same x spacing
        in the 2D input mdel.
    dy : float, optional
        Grid spacing in the y direction.  Default is to set ``dy=dx``.
    phi : float
        Angle of the extrusion direction, measured in degrees from the line
        azimuth. Default is ``90.0`` (i.e., in the line-perpendicular 
        direction).
    """
    # check that current model is 2D
    assert vm.ny == 1, 'vm must be 2D with vm.ny == 1'
    # set defaults
    if dx is None:
        dx = vm.dx
    if dy is None:
        dy = vm.dx
    # calculate line angle 
    theta = np.arctan2(eol[1] - sol[1], eol[0] - sol[0]) \
            + np.deg2rad(phi - 90.)
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
