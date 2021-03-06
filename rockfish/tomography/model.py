"""
Support for working with velocity models.

.. note:: The underlying raytracing and inversion codes are written in
Fortran, and thus array indices start at ``1``, not ``0`` as in Python.
This discrepency becomes an issue when setting the interface flags
(i.e., ``ir`` and ``ij``). To reconcile this issue, this module
subtracts ``1`` from the ``ir`` and ``ij`` arrays when reading a VM
model from the disk and adds ``1`` to these arrays before writing
a VM model. In the Python tools, a value of ``-1`` for ``ir`` or
``ij`` is equivalent to a value of ``0`` in the Fortran codes, and
indicates that a node is to be excluded from the inversion.
"""
import os
import warnings
import subprocess
import numpy as np
from scipy.io import netcdf_file as netcdf
from scipy.interpolate import interp1d, interp2d
import datetime
from struct import unpack
import matplotlib.pyplot as plt
import copy
from rockfish import __version__
from rockfish.utils.string_tools import pad_string
from rockfish.io import pack
from rockfish.signals.smoothing import smooth1d, smooth2d


ENDIAN = pack.BYTEORDER

UNITS = {'slowness': 's/km',
         'velocity': 'km/s',
         'twt': 's',
         'x': 'km',
         'y': 'km',
         'z': 'km'}

x2i = lambda x, x0, dx, nx: np.clip([int(round((_x - x0) / dx))\
                                    for _x in np.atleast_1d(x)], 0, nx - 1)


class GMTCallError(Exception):
    """
    Raised if there is a problem calling a shell script
    """


class VM(object):
    """
    Class for working with VM Tomography velocity models.
    """
    def __init__(self, r1=(0, 0, 0), r2=(250, 0, 30), dx=0.5, dy=1, dz=0.1,
                 nx=None, ny=None, nz=None, nr=0, init_model=True):
        """
        Create a new model instance.

        :param r1: Minimum values for grid dimensions given as the
            tuple ``(xmin, ymin, zmin)``. Default is ``(0,0,0)``.
        :param r2: Maximum values for grid dimensions given as the
            tuple ``(xmax, ymax, zmax)``. Default is ``(250,0,30)``.
        :param dx: Spacing between x-nodes. Default is ``0.5``.
        :param dy: Spacing between y-nodes. Default is ``1``.
        :param dz: Spacing between z-nodes. Default is ``0.1``.
        :param nx: Number of nodes in the x direction.  Overides ``dx``.
            Default is to use ``dx`` to calculate the number of nodes.
        :param ny: Number of nodes in the y direction.  Overides ``dy``.
            Default is to use ``dy`` to calculate the number of nodes.
        :param nz: Number of nodes in the z direction.  Overides ``dz``.
            Default is to use ``dz`` to calculate the number of nodes.
        :param nr: Number of interfaces in the model. Used to
            define the size of the interface arrays. Default is ``0``.
        :param init_model: Determines whether or not to initialize
            parameters and data arrays. Default is True.
        """
        if init_model:
            if nx is not None:
                _dx = (r2[0] - r1[0]) / nx
                if dx is not None:
                    msg = 'Overiding dx={:} with dx={:} such that nx={:}.'\
                            .format(dx, _dx, nx)
                    warnings.warn(msg)
            else:
                _dx = dx

            if ny is not None:
                _dy = (r2[0] - r1[0]) / ny
                if dy is not None:
                    msg = 'Overiding dy={:} with dy={:} such that ny={:}.'\
                            .format(dy, _dy, ny)
                    warnings.warn(msg)
            else:
                _dy = dy

            if nz is not None:
                _dz = (r2[0] - r1[0]) / nz
                if dz is not None:
                    msg = 'Overiding dz={:} with dz={:} such that nz={:}.'\
                            .format(dz, _dz, nz)
                    warnings.warn(msg)
            else:
                _dz = dz

            self.init_model(r1, r2, _dx, _dy, _dz, nr)

    def __str__(self, extended=False, title='Velocity Model'):
        """
        Print an overview of the VM model.

        :param extended: Determines whether or not to print detailed
            information about each layer. Default is to print an overview.
        :param title: Sets the title in the banner. Default is
            'Velocity Model'.
        """
        if (title is None) and hasattr(self, 'file'):
            title = os.path.basename(self.file.name)
        banner = pad_string(title, char='=')
        sng = banner + '\n'
        sng += self._header()
        sng += banner
        if not extended:
            sng += '\n[Use "print VM.__str__(extended=True)" for'
            sng += ' more detailed information]'
        else:
            self.apply_jumps()
            sng += '\nModel top: z = {:}\n'.format(self.r1[2])
            for layer in range(0, self.nr):
                sng += 'Interface {:}: zmin = {:}, zmax={:}\n'\
                        .format(layer, np.min(self.rf[layer]),
                                np.max(self.rf[layer]))
                sng += '   ' + self._layer_info(layer) + '\n'
            sng += 'Model bottom: z = {:}'.format(self.r2[2])
            self.remove_jumps()
        return sng

    def _header(self):
        """
        Format header values as plain text.
        """
        sng = 'Grid Dimensions:\n'
        sng += ' xmin = {:7.3f}'.format(self.r1[0])
        sng += ', xmax = {:7.3f}'.format(self.r2[0])
        sng += ', dx = {:7.3f}'.format(self.dx)
        sng += ', nx = {:5d}\n'.format(self.nx)
        sng += ' ymin = {:7.3f}'.format(self.r1[1])
        sng += ', ymax = {:7.3f}'.format(self.r2[1])
        sng += ', dy = {:7.3f}'.format(self.dy)
        sng += ', ny = {:5d}\n'.format(self.ny)
        sng += ' zmin = {:7.3f}'.format(self.r1[2])
        sng += ', zmax = {:7.3f}'.format(self.r2[2])
        sng += ', dz = {:7.3f}'.format(self.dz)
        sng += ', nz = {:5d}\n'.format(self.nz)
        sng += 'Interfaces:'
        sng += ' nr = {:d}\n'.format(self.nr)
        return sng

    def _layer_info(self, layer):
        """
        Format layer information as plain text.

        :param layer: Index of layer to get information for.
        """
        idx = np.nonzero(self.layers.flatten() == layer)
        sl = self.sl.flatten()
        sng = 'Layer {:}: '.format(layer)
        sng += 'smin = {:7.3f}'.format(min(sl[idx]))
        sng += ', smax = {:7.3f}'.format(max(sl[idx]))
        sng += ', vmin = {:7.3f}'.format(min(1./sl[idx]))
        sng += ', vmax = {:7.3f}'.format(max(1./sl[idx]))
        return sng

    def recalculate_jumps(self, iref, xmin=None, xmax=None, ymin=None,
                        ymax=None):
        """
        Recalculate slowness jumps.

        :param iref: Index of interface to calculate slowness jumps on.
        :param xmin, xmax: Set the x-coordinate limits for
            calculating jumps. Default is to calculate jumps over the entire
            x-domain.
        :param ymin, ymax: Set the y-coordinate limits for
            calculating jumps. Default is to calculate jumps over the entire
            y-domain.
        """
        self.apply_jumps(iref=range(0, iref - 1))
        _, z0 = self.get_layer_bounds(iref)
        for ix in self.xrange2i(xmin, xmax):
            for iy in self.yrange2i(ymin, ymax):
                iz0 = self.z2i([z0[ix, iy]])[0]
                sl0 = self.sl[ix, iy, iz0]
                sl1 = self.sl[ix, iy, iz0 + 1]
                self.jp[iref - 1][ix][iy] = sl1 - sl0
        self.remove_jumps(iref=range(0, iref - 1))

    def apply_jumps(self, iref=None, remove=False):
        """
        Apply slowness jumps to the grid.

        :param iref: Optional. ``list`` of interface indices to apply jumps 
            to. Default is to apply jumps to all interfaces.
        :param remove: Optional. Determines whether jumps should be removed 
            or applied. Default is ``False`` (i.e., jumps are applied).
        """
        if iref is None:
            iref = range(0, self.nr)
        for _iref in iref:
            z0, _ = self.get_layer_bounds(_iref + 1)
            for ix in range(0, self.nx):
                for iy in range(0, self.ny):
                    iz0 = self.z2i([z0[ix, iy]])[0]
                    if remove is False:
                        self.sl[ix, iy, iz0:] += self.jp[_iref, ix, iy]
                    else:
                        self.sl[ix, iy, iz0:] -= self.jp[_iref, ix, iy]

    def remove_jumps(self, iref=None):
        """
        Remove slowness jumps from the grid.
        
        :param iref: Optional. ``list`` of interface indices to remove jumps 
            from. Default is to remove jumps from all interfaces.
        """
        self.apply_jumps(iref=iref, remove=True)

    def smooth_jumps(self, n, ny=None, idx=None):
        """
        Smooth slowness jumps by convolving a gaussian kernal of typical size
        n.  The optional keyword argument ``ny`` allows for a different
        size in the y direction.
        :param n: Typical size of the guassian kernal.
        :param ny: Optional. Specifies a different dimension for the smoothing
            kernal in the y direction. Default is to set the y size equal to 
            to the size in x.
        :param idx: Optional. ``list`` of indices for interfaces to operate on
            Default is operate on all interfaces.
        """
        if idx is None:
            idx = range(0, self.nr)
        n = min(self.nx, n)
        if ny is None:
            ny = n
        ny = min(self.ny, ny)
        for i in idx:
            if ny == 1:
                self.jp[i] = smooth1d(self.jp[i].flatten(), n)\
                    .reshape((self.nx, 1))
            else:
                self.jp[i] = smooth2d(self.jp[i], n, ny=ny)

    def smooth_interface(self, iref, n, ny=None):
        """
        Smooth interface depth by convolving a gaussian kernal of typical size
        n.  The optional keyword argument ``ny`` allows for a different
        size in the y direction.
        
        :param iref: Index of interface to smooth.
        :param n: Typical size of the guassian kernal.
        :param ny: Optional. Specifies a different dimension for the smoothing
            kernal in the y direction. Default is to set the y size equal to 
            to the size in x.
        """
        n = min(self.nx, n)
        if ny is None:
            ny = n
        ny = min(self.ny, ny)
        if ny == 1:
            self.rf[iref] = smooth1d(self.rf[iref].flatten(), n)\
                .reshape((self.nx, 1))
        else:
            self.rf[iref] = smooth2d(self.rf[iref], n, ny=ny)


    def define_stretched_layer_velocities(self, ilyr, vel=[None, None],
                                          xmin=None, xmax=None, ymin=None,
                                          ymax=None, kind='linear'):
        """
        Define velocities within a layer by stretching a velocity function.

        At each x,y position in the model grid, the list of given velocities
        are first distributed proportionally across the height of the layer.
        Then, this z,v function is used to interpolate velocities for each
        depth node in the layer.

        :param ilyr: Index of layer to work on.
        :param vel: ``list`` of layer velocities. Default is to
            stretch a 1d function between the deepest velocity of the overlying
            layer and the shallowest velocity of the underlying layer.
        :param xmin, xmax: Set the x-coordinate limits for modifying
            velocities. Default is to change velocities over the entire
            x-domain.
        :param ymin, ymax: Set the y-coordinate limits for modifying
            velocities. Default is to change velocities over the entire
            y-domain.
        :param kind: str or int, optional.  Specifies the kind of
            interpolation as a string ('linear','nearest', 'zero',
            'slinear', 'quadratic, 'cubic') or as an integer
            specifying the order of the spline interpolator to use.
            Default is 'linear'.
        """
        # Get layer boundary depths
        z0, z1 = self.get_layer_bounds(ilyr)
        # Define velocity function at each x,y point
        vel = np.asarray(vel)
        nvel = len(vel)
        for ix in self.xrange2i(xmin, xmax):
            for iy in self.yrange2i(ymin, ymax):
                iz0, iz1 = self.z2i((z0[ix, iy], z1[ix, iy]))
                iz1 += 1
                z = self.z[iz0:iz1]
                if len(z) == 0:
                    # in pinchout, nothing to do
                    continue
                # Make a copy of velocities for this iteration
                _vel = np.copy(vel)
                # Get top and bottom velocities, if they are None
                if vel[0] is None:
                    _vel[0] = 1. / self.sl[ix, iy, max(iz0 - 1, 0)]
                if len(vel) > 1:
                    if vel[1] is None:
                        _vel[1] = 1. / self.sl[ix, iy, min(iz1 + 1, self.nx)]
                # Pad interpolates for rounding to grid coordinates
                if nvel == 1:
                    # Set constant value
                    v = np.asarray([_vel])
                else:
                    # Interpolate velocities
                    zi = z0[ix, iy] + (z1[ix, iy] - z0[ix, iy])\
                            * np.arange(0., nvel) / (nvel - 1)
                    vi = np.copy(_vel)
                    if z[0] < zi[0]:
                        zi = np.insert(zi, 0, z[0])
                        vi = np.insert(vi, 0, _vel[0])
                    if z[-1] > zi[-1]:
                        zi = np.append(zi, z[-1])
                        vi = np.append(vi, _vel[-1])
                    zv = interp1d(zi, vi, kind=kind)
                    v = zv(z)
                self.sl[ix, iy, iz0:iz1] = 1. / v

    def insert_layer_velocities(self, ilyr, vel, is_slowness=False):
        """
        Insert a grid of velocities for a single layer.

        :param ilyr: Index of layer to work on.
        :param vel: :class:`numpy.ndarray` with shape (nx, ny, nz) containing
            velocities to insert.
        :param is_slowness: Determines whether ``vel`` contains velocities
            (default) or slowness values.
        """
        assert vel.shape == (self.nx, self.ny, self.nz),\
                'vel must be of shape (nx, ny, nz)'
        isl = np.nonzero(self.layers == ilyr)
        if is_slowness:
            self.sl[isl] = vel[isl]
        else:
            self.sl[isl] = 1. / vel[isl]

    def define_constant_layer_velocity(self, ilyr, v, xmin=None,
                                          xmax=None, ymin=None, ymax=None):
        """
        Define a constant velocity for an entire layer.

        :param ilyr: Index of layer to work on.
        :param v: Velocity.
        :param xmin, xmax: Set the x-coordinate limits for modifying
            velocities. Default is to change velocities over the entire
            x-domain.
        :param ymin, ymax: Set the y-coordinate limits for modifying
            velocities. Default is to change velocities over the entire
            y-domain.
        """
        self.define_stretched_layer_velocities(ilyr, [v], xmin=xmin, xmax=xmax,
                                              ymin=ymin, ymax=ymax)

    def define_variable_layer_gradient(self, ilyr, dvdz, v0=None):
        """
        Replace velocities within a layer by defining a gtradient that
        varies linearly in the horizontal directions.

        :param ilyr: Index of layer to work on.
        :param dvdz: List of velocity gradient values. Must be of shape
            (nx, ny).
        :param v0: List of velocities at the top of the layer. Must be of
            shape (nx, ny). Default is to use the value at the
            base of the overlying layer.
        """
        z0, z1 = self.get_layer_bounds(ilyr)
        for ix in range(0, self.nx):
            for iy in range(0, self.ny):
                iz0, iz1 = self.z2i((z0[ix, iy], z1[ix, iy]))
                iz1 += 1
                z = self.z[iz0:iz1] - self.z[iz0]
                if v0 is None:
                    if iz0 == 0:
                        _v0 = 0.
                    else:
                        _v0 = 1. / self.sl[ix, iy, iz0 - 1]
                else:
                    _v0 = v0[ix, iy]
                self.sl[ix, iy, iz0:iz1] = 1. / (_v0 + z * dvdz[ix, iy])

    def define_constant_layer_gradient(self, ilyr, dvdz, v0=None, xmin=None,
                                       xmax=None, ymin=None, ymax=None):
        """
        Replace velocities within a layer by defining a constant gradient.

        :param ilyr: Index of layer to work on.
        :param dvdz: Velocity gradient.
        :param v0:  Velocity at the top of the layer. Default is to use the
            value at the base of the overlying layer.
        :param xmin, xmax: Set the x-coordinate limits for modifying
            velocities. Default is to change velocities over the entire
            x-domain.
        :param ymin, ymax: Set the y-coordinate limits for modifying
            velocities. Default is to change velocities over the entire
            y-domain.
        """
        z0, z1 = self.get_layer_bounds(ilyr)
        for ix in self.xrange2i(xmin, xmax):
            for iy in self.yrange2i(ymin, ymax):
                iz0, iz1 = self.z2i((z0[ix, iy], z1[ix, iy]))
                iz1 += 1
                z = self.z[iz0:iz1] - self.z[iz0]
                if v0 is None:
                    if iz0 == 0:
                        _v0 = 0.
                    else:
                        _v0 = 1. / self.sl[ix, iy, iz0 - 1]
                else:
                    _v0 = v0
                self.sl[ix, iy, iz0:iz1] = 1. / (_v0 + z * dvdz)

    def get_layer_bounds(self, ilyr):
        """
        Get surfaces bounding a layer.

        :param idx: Index of layer of interest.
        :returns: z0, z1 arrays of top, bottom interface depths.
        """
        assert (ilyr >= 0) and (ilyr <= self.nr),\
            "Layer {:} does not exist.".format(ilyr)
        if ilyr == 0:
            z0 = np.ones((self.nx, self.ny)) * self.r1[2]
        else:
            z0 = self.rf[ilyr - 1]
        if ilyr >= self.nr:
            z1 = np.ones((self.nx, self.ny)) * self.r2[2]
        else:
            z1 = self.rf[ilyr]
        return z0, z1

    def init_model(self, r1, r2, dx, dy, dz, nr):
        """
        Initialize a new model.

        :param r1: Minimum values for grid dimensions given as the
            tuple ``(xmin, ymin, zmin)``.
        :param r2: Maximum values for grid dimensions given as the
            tuple ``(xmax, ymax, zmax)``.
        :param dx: Spacing between x-nodes.
        :param dy: Spacing between y-nodes.
        :param dz: Spacing between z-nodes.
        :param nr: Number of interfaces in the model. Used to define the
            the size of the interface arrays.
        """
        # Calculate grid sizes
        nx = int(np.round((r2[0] - r1[0]) / dx)) + 1
        ny = int(np.round((r2[1] - r1[1]) / dy)) + 1
        nz = int(np.round((r2[2] - r1[2]) / dz)) + 1
        # Initialize arrays to all zeros
        self.grids = VMGrids(dx, dy, dz, np.zeros((nx, ny, nz)), 
                xmin=r1[0], ymin=r1[1], zmin=r1[2])
        self.rf = np.zeros((nr, nx, ny))
        self.jp = np.zeros((nr, nx, ny))
        # Initialize flags as inactive
        self.ir = -1 * np.ones((nr, nx, ny))
        self.ij = -1 * np.ones((nr, nx, ny))

        # Initialize the time model
        self.time_model = VMTime(self)

    def read(self, file, endian=ENDIAN, head_only=False):
        """
        Read a VM model from a file on the disk or a file-like object.

        :param file: An open file-like object or a string which is
            assumed to be a filename.
        :param endian: The endianness of the file. Default is
            to use machine's native byte order.
        :param head_only: Determines whether or not to read the grid
            data. Useful is only interested in the grid dimension values.
            Default is to read the entire file.
        """
        if not hasattr(file, 'read') or not hasattr(file, 'tell') or not \
            hasattr(file, 'seek'):
            file = open(file, 'rb')
        else:
            file.seek(0)
        self._read(file, endian=endian, head_only=head_only)
        self.file = file
        self.file.close()

    def _read(self, file, endian=ENDIAN, head_only=False):
        """
        Read a VM model from a file-like object.

        :param file: A file-like object with the file pointer set at the
            beginning of a VM binary file.
        :param endian: The endianness of the file. Default is
            to use machine's native byte order.
        :param head_only: Determines whether or not to read the grid
            data. Useful if one is only interested in the grid dimension
            values. Default is to read the entire file.
        """
        # Header information
        fmt = '{:}iiii'.format(endian)
        nx, ny, nz, nr = unpack(fmt, file.read(4 * 4))
        fmt = '{:}fff'.format(endian)
        r1 = unpack(fmt, file.read(4 * 3))
        r2 = unpack(fmt, file.read(4 * 3))
        fmt = '{:}fff'.format(endian)
        dx, dy, dz = unpack(fmt, file.read(4 * 3))
        if head_only is True:
            sl = np.empty((nx, ny, nz))
            self.rf = np.empty((nr, nx, ny))
            self.jp = np.empty((nr, nx, ny))
            self.ir = np.empty((nr, nx, ny))
            self.ij = np.empty((nr, nx, ny))

            self.grids = VMGrids(dx, dy, dz, sl, xmin=r1[0],
                    ymin=r1[1], zmin=r1[2])

            return

        # Slowness grid
        ngrid = nx * ny * nz
        fmt = endian + ('f' * ngrid)
        sl = np.asarray(unpack(fmt, file.read(4 * ngrid)))
        self.grids = VMGrids(dx, dy, dz, sl, xmin=r1[0], ymin=r1[1],
                zmin=r1[2])

        # Interface depths and slowness jumps
        nintf = nx * ny * nr
        fmt = endian + 'f' * nintf
        self.rf = unpack(fmt, file.read(4 * nintf))
        self.jp = unpack(fmt, file.read(4 * nintf))

        # Interface flags
        fmt = endian + 'i' * nintf
        self.ir = unpack(fmt, file.read(4 * nintf))
        self.ij = unpack(fmt, file.read(4 * nintf))

        # Rearrage 1D arrays into 3D matrixes
        self._unpack_arrays(nx, ny, nz, nr)

        # Subtract 1 from array index flags to conform to Python convention
        self.ir -= 1
        self.ij -= 1
        
        # Initialize the time model
        self.time_model = VMTime(self)

    def _read_fmtomo(self, file):
        """
        Read a FMTOMO velocity model.
        """
        dat = file.readlines()

        i0, i1 = [int(v) for v in dat[0].split()]
        nx, ny, nz = [int(v) for v in dat[1].split()]
        dx, dy, dz = [float(v) for v in dat[2].split()]
        r0 = [float(v) for v in dat[3].split()]

        print [float(v) for v in dat[4:]]

        vel = [float(v) for v in dat[4:]]

        print len(vel)
        print nx, ny, nz
        print nx * ny * nz

        self.dx = dx
        self.dy = dy
        self.dz = dz

        self.r0 = r0





    def read_dws_grid(self, filename):
        """
        Read derivative-weight sum (DWS) data.

        :param filename: Filename of an ASCII file with columns: x, y, z, dws.
        """
        f = open(filename)
        dws = []
        for row in f:
            dws.append(float(row.split()[3]))
        dws = np.asarray(dws)
        self.dws_sl = np.reshape(dws, (self.nx, self.ny, self.nz))

    def write(self, filename, fmt='vm', endian=ENDIAN, **kwargs):
        """
        Write the VM model to a disk file.

        .. note:: This is a convienence function for acessing various write
            functions. These write functions are named ``'write_<fmt>'``; see
            the documentation for these functions for parameter descriptions
            and additional documentation.

        :param filename: Name of a file to write data to.
        :param fmt:  Format to write data in. Default is the native
            VM Tomography binary format (``format='vm'``). Other options are
            ``'ascii_grid'``.
        :param endian: The endianness of the file for binary formats.
            Default is to use the machine's native byte order.
        :param kwargs: Keyword=value arguments that are passed along to the
            writing function.
        """
        if fmt is 'vm':
            self.write_vm(filename, endian=endian)
        elif fmt is 'ascii_grid':
            self.write_ascii_grid(filename, **kwargs)
        else:
            msg = "Unknown format '{:}'.".format(fmt)
            raise ValueError(msg)

    def write_vm(self, filename, endian=ENDIAN):
        """
        Write the VM model in the native VM Tomography format.

        :param filename: Name of a file to write data to.
        :param endian: The endianness of the file. Default is
            to use machine's native byte order.
        """
        f = open(filename, 'w')
        # Header information
        nx = self.nx
        ny = self.ny
        nz = self.nz
        nr = self.nr
        for v in [nx, ny, nz, nr]:
            pack.pack_4byte_Integer(f, np.int32(v), endian)
        for v in self.r1 + self.r2 + (self.dx, self.dy, self.dz):
            pack.pack_4byte_IEEE(f, np.float32(v), endian)
        # Slowness grid
        self._pack_arrays()  # must be called after writing size properties
        pack.pack_4byte_IEEE(f, np.float32(self.sl), endian)
        # Interface depths and slowness jumps
        for v in [self.rf, self.jp]:
            pack.pack_4byte_IEEE(f, np.float32(v), endian)
        # Add 1 to interface flags to conform to Fortran convention
        ir = self.ir + 1
        ij = self.ij + 1
        # Write interface flags
        for v in [ir, ij]:
            pack.pack_4byte_Integer(f, np.int32(v), endian)
        f.close()
        # Unpack the arrays for future use
        self._unpack_arrays(nx, ny, nz, nr)

    def write_ascii_grid(self, filename, grid='sl', meters=False,
            velocity=False):
        """
        Write VM model slowness grid in an ASCII format.

        :param filename: Name of a file to write data to.
        :param grid: Grid attribute to write data from. Default is `sl`
            (slowness).
        :param meters: Output distance units in meters. Default is
            kilometers.
        :param velocity: Output slowness values as velocity. Default
            is slowness.
        """
        file = open(filename, 'w')
        # Get grid
        grd = self.__getattribute__(grid)
        # Write a header
        file.write('# VM Tomography velocity model grid\n')
        if meters is True:
            xscale = 1000.
            units = 'x_m y_m z_m'
        else:
            xscale = 1.
            units = 'x_km y_km z_km'
        units += ' {:}'.format(grid)
        file.write('# {:}\n'.format(units))
        if hasattr(self, 'file'):
            file.write('#\n# Exported from: {:}\n'.format(self.file.name))
        else:
            file.write('#\n# Exported from: memory\n')
        file.write('# Created by: {:} (version {:})\n'\
                   .format(os.path.basename(__file__), __version__))
        file.write('# Created on: {:}\n'.format(datetime.datetime.now()))
        #file.write('#\n# Grid overview:\n')
        #for line in self._get_full_overview().split('\n'):
        #    file.write('# {:}\n'.format(line))
        for ix in self.xrange2i(): 
            x = (self.r1[0] + ix * self.dx) * xscale
            for iy in self.yrange2i(): 
                y = (self.r1[1] + iy * self.dy) * xscale
                for iz in self.zrange2i(): 
                    z = (self.r1[2] + iz * self.dz) * xscale
                    if velocity is True:
                        _grd = 1. / grd[ix][iy][iz]
                    else:
                        _grd = grd[ix][iy][iz]

                    file.write('{:20.3f} {:20.3f} {:20.3f} {:10.5f}\n'\
                               .format(x, y, z, _grd))
        file.close()

    def write_grd(self, grdfile, grid='sl', velocity=False):

        assert self.ny == 1, 'write_grd() only works with 2D models (ny=1)'

        xyzfile = '.temp.vm.xyzv'

        self.write_ascii_grid(xyzfile, grid=grid, velocity=velocity,
                meters=False)

        gmt = "awk '(substr($0, 1, 1)!=" + '"#"'\
                + "){print $1, $3, $4}' " + xyzfile

        gmt += ' | gmt xyz2grd -G{:} -R{:}/{:}/{:}/{:} -I{:}/{:}'\
                .format(grdfile, self.r1[0], self.r2[0],
                        self.r1[2], self.r2[2], self.dx, self.dz)

        subprocess.call(gmt, shell=True)

        if not os.path.isfile(grdfile):
            raise GMTCallError('Problem executing shell script: {:}'\
                    .format(gmt))

        os.remove(xyzfile)

    def project_model(self, angle, dx=None, x=None, y=None):
        """
        Project a 2D model onto another line.

        :param angle: Clockwise angle in degrees from the current line.
        :param dx: x-coordinate grid spacing. Default is to use the same grid
            spacing as in the current model.
        :param x,y: Coordinate values of 2D slice to project. Default is to
            project the first x-z plane in the model.
        :returns: :class:`rockfish.tomography.model.VM` model along the new
            line.
        """
        # Pull slice from model if not already 2D
        if (x is None) and (y is None):
            vm0 = self
        else:
            vm0 = slice_along_xy_line(x=x, y=y, dx=min(self.dx, self.dy))
        # Create new model
        if dx is None:
            dx = vm0.dx
        xdim = (vm0.r2[0] - vm0.r1[0]) / np.cos(np.deg2rad(angle))
        xmax = np.floor(xdim / dx) * dx
        vm1 = VM(r1=(0, 0, vm0.r1[2]), r2=(xmax, 0, vm0.r2[2]),
                 dx=dx, dy=1, dz=vm0.dz, nr=vm0.nr)
        # New model coordinates in old model
        x0 = vm1.x * np.cos(np.deg2rad(angle))
        # Project boundaries
        for iref in range(0, vm0.nr):
            # setup interpolators
            x2rf = interp1d(vm0.x, [v[0] for v in vm0.rf[iref]], kind='linear')
            x2jp = interp1d(vm0.x, [v[0] for v in vm0.jp[iref]], kind='linear')
            x2ir = interp1d(vm0.x, [v[0] for v in vm0.ir[iref]],
                            kind='nearest')
            x2ij = interp1d(vm0.x, [v[0] for v in vm0.ij[iref]],
                            kind='nearest')
            # do the interpolating
            vm1.rf[iref] = np.asarray([[v] for v in x2rf(x0)])
            vm1.jp[iref] = np.asarray([[v] for v in x2jp(x0)])
            vm1.ir[iref] = np.asarray([[v] for v in x2ir(x0)])
            vm1.ij[iref] = np.asarray([[v] for v in x2ij(x0)])
        # Project velocities
        for iz in range(0, vm0.nz):
            x2sl = interp1d(vm0.x, vm0.sl[:, 0, iz], kind='linear')
            sl = x2sl(x0)
            vm1.sl[:, 0, iz] = sl
        nbogus = len(np.nonzero(vm1.sl < 0))
        if nbogus > 0:
            msg = 'Interpolation of slowness resulted in {:}'.format(nbogus)
            msg += ' nodes with negative values.'
            warnings.warn(msg)
        return vm1

    def _unpack_arrays(self, nx, ny, nz, nr):
        """
        Rearrange the 1D model arrays into 3D matrices (stacked arrays)
        """
        self.sl = np.reshape(self.sl, (nx, ny, nz))
        rf = []
        jp = []
        ir = []
        ij = []
        for iref in range(0, nr):
            i0 = iref * (nx * self.ny)
            i1 = i0 + (nx * self.ny)
            rf.append(np.reshape(self.rf[i0:i1], (nx, ny)))
            jp.append(np.reshape(self.jp[i0:i1], (nx, ny)))
            ir.append(np.reshape(self.ir[i0:i1], (nx, ny)))
            ij.append(np.reshape(self.ij[i0:i1], (nx, ny)))
        self.rf = np.asarray(rf)
        self.jp = np.asarray(jp)
        self.ir = np.asarray(ir)
        self.ij = np.asarray(ij)

    def _pack_arrays(self):
        """
        Rearrange the 3D model matrices into 1D arrays.
        """
        ngrid = self.nx * self.ny * self.nz
        nrefl = self.nx * self.ny * self.nr
        self.sl = np.reshape(self.sl, (ngrid))
        self.rf = np.reshape(self.rf, (nrefl))
        self.jp = np.reshape(self.jp, (nrefl))
        self.ir = np.reshape(self.ir, (nrefl))
        self.ij = np.reshape(self.ij, (nrefl))

    def gridpoint2index(self, ix, iy, iz):
        """
        Convert a 3-component slowness grid indices to a single index in the 1D
        packed slowness array.

        :param ix: x-coordinate index
        :param iy: y-coordinate index
        :param iz: z-coordinate index
        :returns: index in the 1D packed slowness array
        """
        return ix * self.ny * self.nz + iy * self.nz + iz

    def index2gridpoint(self, idx):
        """
        Convert an index in the 1D, packed slowness array to 3-component
        indices.

        Parameters
        ----------
        idx : int
            Index in the 1D, packed slowness array
        
        Returns
        -------
        ix, iy, iz : int
            x, y, and z indices in the 3D grid.
        """
        iz = np.mod(idx, self.nz)
        iy = np.mod(idx / self.nz, self.ny)
        ix = idx / (self.ny * self.nz)
        return ix, iy, iz


    def interfacepoint2index(self, ix, iy, ir):
        """
        Convert a 3-component interface indices to a single index in the 1D
        packed interface arrays.

        :param ix: x-coordinate index
        :param iy: y-coordinate index
        :param ir: interface index
        """
        return ir * self.nx + ix * self.ny + iy

    def x2i(self, x):
        """
        Find x indices for x coordinates.

        :param x: list of x coordinates in the model
        :returns: list of nearest x index for the given coordinates
        """
        return x2i(x, self.r1[0], self.dx, self.nx) 

    def i2x(self, ix):
        """
        Find x coordinates for x indices.

        :param ix: list of x indices
        :returns: list of x coordinates
        """
        return [self.r1[0] + _ix * self.dx for _ix in ix]

    def x2x(self, x):
        """
        Find x-coordinate of nearest node
        
        :param x: x coordinate
        :returns: x-coordinate of nearest node 
        """
        return self.x[self.x2i(np.atleast_1d(x))]

    def xrange2i(self, xmin=None, xmax=None):
        """
        Returns a list of x indices for a given x range.

        :param xmin: Minimum value of x. Default is the minimum x
            value in the model.
        :param xmax: Maximum value of x. Default is the maximum x
            value in the model.
        :returns: ``list`` of x indices.
        """
        if xmin is None:
            xmin = self.r1[0]
        else:
            xmin = max(self.r1[0], xmin)
        if xmax is None:
            xmax = self.r2[0]
        else:
            xmax = min(self.r2[0], xmax)
        return range(self.x2i([xmin])[0], self.x2i([xmax])[0] + 1)

    def y2i(self, y):
        """
        Find a y index for a y coordinate.

        :param y: list of y coordinates in the model
        :returns: list of nearest y index for the given coordinates
        """
        return x2i(y, self.r1[1], self.dy, self.ny) 

    def i2y(self, iy):
        """
        Find y coordinates for y indices.

        :param iy: list of y indices
        :returns: list of y coordinates
        """
        return [self.r1[1] + _iy * self.dy for _iy in iy]

    def y2y(self, y):
        """
        Find y-coordinate of nearest node
        
        :param y: y coordinate
        :returns: y-coordinate of nearest node 
        """
        return self.y[self.y2i(np.atleast_1d(y))]

    def yrange2i(self, ymin=None, ymax=None):
        """
        Returns a list of y indices for a given y range.

        :param ymin: Minimum value of y. Default is the minimum y
            value in the model.
        :param ymax: Maximum value of y. Default is the maximum y
            value in the model.
        :returns: ``list`` of y indices.
        """
        if ymin is None:
            ymin = self.r1[1]
        else:
            ymin = max(self.r1[1], ymin)
        if ymax is None:
            ymax = self.r2[1]
        else:
            ymax = min(self.r2[1], ymax)
        return range(self.y2i([ymin])[0], self.y2i([ymax])[0] + 1)

    def z2i(self, z):
        """
        Find a z index for a z coordinate.

        :param y: list of y coordinates in the model
        :returns: list of nearest y index for the given coordinates
        """
        return x2i(z, self.r1[2], self.dz, self.nz) 

    def i2z(self, iz):
        """
        Find z coordinates for z indices.

        :param iz: list of z indices
        :returns: list of z coordinates
        """
        return [self.r1[2] + _iz * self.dz for _iz in iz]

    def z2z(self, z):
        """
        Find z-coordinate of nearest node
        
        :param z: z coordinate
        :returns: z-coordinate of nearest node 
        """
        return self.z[self.z2i(np.atleast_1d(z))]

    def zrange2i(self, zmin=None, zmax=None):
        """
        Returns a list of z indices for a given z range.

        :param zmin: Minimum value of z. Default is the minimum z
            value in the model.
        :param zmax: Maximum value of z. Default is the maximum z
            value in the model.
        :returns: ``list`` of z indices.
        """
        if zmin is None:
            zmin = self.r1[2]
        else:
            zmin = max(self.r1[2], zmin)
        if zmax is None:
            zmax = self.r2[2]
        else:
            zmax = min(self.r2[2], zmax)
        return range(self.z2i([zmin])[0], self.z2i([zmax])[0] + 1)

    def xyz2ijk(self, x, y, z):
        """
        Converts three-component coordinates to indices.

        Parameters
        ----------
        x, y, z: float
            x, y, z coordinates

        Returns
        -------
        i, j, k: int
            Indices for the point x, y, z
        """
        return self.x2i([x])[0], self.y2i([y])[0], self.z2i([z])[0]

    def xyz2xyz(self, x, y, z):
        """
        Find the nearest grid node to an x, y, z point
        
        Parameters
        ----------
        x, y, z: float
            x, y, z coordinates

        Returns
        -------
        x, y, z: float
            Coordinates of the nearest grid node
        """
        return self.x2x(x), self.y2y(y), self.z2z(z)

    def gridpoint2position(self, ix, iy, iz):
        """
        Returns the x,y,z coordinates coresponding to a set of model indices.

        :param ix: x-coordinate index
        :param iy: y-coordinate index
        :param iz: z-coordinate index
        :returns: x, y, z
        """
        x = ix * self.dx + self.r1[0]
        y = iy * self.dy + self.r1[1]
        z = iz * self.dz + self.r1[2]
        return x, y, z

    def slice_along_xy_line(self, x, y, dx=None):
        """
        Extract a vertical slice along a line.

        :param x,y: Lists of coordinates to take slice along.
        :param dx: Grid spacing for the new model. Default is to use
            the x-coordinate spacing of the current model.
        :returns: VM model along the specified line

        .. warning:: Fails with constant x-slices.
        """
        assert len(x) == len(y), 'x and y must be the same length'
        assert max(x) <= self.r2[0], 'x coordinates exceed model domain'
        assert min(x) >= self.r1[0], 'x coordinates exceed model domain'
        assert max(y) <= self.r2[1], 'y coordinates exceed model domain'
        assert min(y) >= self.r1[1], 'y coordinates exceed model domain'
        # Calculate distance along line
        _xline = [0]
        for i in range(1, len(x)):
            x0 = x[i - 1]
            y0 = y[i - 1]
            x1 = x[i]
            y1 = y[i]
            deltx = np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            _xline.append(_xline[i - 1] + deltx)
        # Setup new model
        if dx is None:
            dx = self.dx
        vm = VM(r1=(min(_xline), 0, self.r1[2]),
                r2=(max(_xline) - dx, 0, self.r2[2]),
                dx=dx, dy=1, dz=self.dz, nr=self.nr)
        # Pull slowness grid and interface values along line
        interp_y = interp1d(x, y)
        interp_x = interp1d(_xline, x)
        for _ixl, _xl in enumerate(vm.x):
            # get coordinates of position on line
            try:
                _x = interp_x(_xl)
            except ValueError as e:
                msg = ' (min, max x-coordinate in 2D model is'
                msg += ' {:}, {:}'.format(min(_xline), max(_xline))
                msg += '; at x = {:}.)'.format(_xl)
                raise ValueError(e.message + msg)
            _y = interp_y(_x)
            # get indices in 3D model
            ix = self.x2i([_x])[0]
            iy = self.y2i([_y])[0]
            # get slowness collumn
            vm.sl[_ixl][0] = self.sl[ix][iy]
            # get interfaces
            for iref in range(0, self.nr):
                vm.rf[iref][_ixl][0] = self.rf[iref][ix][iy]
                vm.jp[iref][_ixl][0] = self.jp[iref][ix][iy]
                vm.ir[iref][_ixl][0] = self.ir[iref][ix][iy]
                vm.ij[iref][_ixl][0] = self.ij[iref][ix][iy]
        vm.rf = np.asarray(vm.rf)
        vm.jp = np.asarray(vm.jp)
        vm.ir = np.asarray(vm.ir)
        vm.ij = np.asarray(vm.ij)
        return vm

    def remove_interface(self, iref, apply_jumps=False):
        """
        Remove an interface from the model.

        :param iref: Index of the interface to remove.
        :param apply_jumps: Optional. Determines whether or not to apply
            slowness jumps for the interface before removing the interface.
            Default is ``False``.
        """
        if apply_jumps:
            self.remove_jumps(iref=[iref])
        self.rf = np.delete(self.rf, iref, 0)
        self.jp = np.delete(self.jp, iref, 0)
        self.ir = np.delete(self.ir, iref, 0)
        self.ij = np.delete(self.ij, iref, 0)
        for _iref in range(iref, self.nr):
            idx = np.nonzero(self.ir[_iref] >= iref)
            self.ir[_iref][idx] -= 1
            idx = np.nonzero(self.ij[_iref] >= iref)
            self.ij[_iref][idx] -= 1

    def insert_interface(self, rf, jp=None, ir=None, ij=None):
        """
        Insert a new interface into the model.

        Parameters
        ----------
        rf : {scalar, array_like}
            Constant depth or matrix of depths with shape ``(nx, ny)``.
        jp : {scalar, array_like, None}, optional
            Constant slowness jumps, matrix of depths with shape
            ``(nx, ny)``, or None. If None (default), jumps are set to zero.
        ir : {scalar, array_like, None}, optional
            Sets indices of the interface to use in the inversion
            for interface depths at each interface node. A value of ``-1``
            indicates that a node should not be used in the inversion. 
            Can be a scalar value that is copied to all nodes, a matrix of
            with shape ``(nx, ny)``, or None. If None (default), all
            values are set to the index of the new interface.
        ij : {scalar, array_like, None}, optional
            Sets indices of the interface to use in the inversion
            for slowness jumps at each interface node. A value of ``-1``
            indicates that a node should not be used in the inversion. 
            Can be a scalar value to be copied to all nodes, a matrix
            with shape ``(nx, ny)``, or None. If None (default), all
            values are set to the index of the new interface.

        Returns
        -------
        iref : int
            Index of the new interface.
        """
        # Expand scalar depth value to array
        if np.asarray(rf).size == 1:
            rf *= np.ones((self.nx, self.ny))
        # Determine index for new interface
        iref = 0
        for _iref in range(0, self.nr):
            if np.nanmax(rf) >= np.nanmax(self.rf[_iref]):
                iref += 1
        # Create default arrays if not given
        if jp is None:
            jp = np.zeros((self.nx, self.ny))
        if ir is None:
            ir = iref * np.ones((self.nx, self.ny))
        if ij is None:
            ij = iref * np.ones((self.nx, self.ny))
        # Expand jump and flag arrays if scalars
        if np.asarray(jp).size == 1:
            jp *= np.ones((self.nx, self.ny))
        if np.asarray(ir).size == 1:
            ir *= np.ones((self.nx, self.ny))
        if np.asarray(ij).size == 1:
            ij *= np.ones((self.nx, self.ny))
        # Check for proper dimensions
        for v in [rf, jp, ir, ij]:
            assert np.asarray(v).shape == (self.nx, self.ny),\
                'Arrays must have shape (nx, ny)'
        # Insert arrays for new interface
        if self.nr == 0:
            self.rf = np.asarray([rf])
            self.jp = np.asarray([jp])
            self.ir = np.asarray([ir])
            self.ij = np.asarray([jp])
        else:
            self.rf = np.insert(self.rf, iref, rf, 0)
            self.jp = np.insert(self.jp, iref, jp, 0)
            self.ir = np.insert(self.ir, iref, ir, 0)
            self.ij = np.insert(self.ij, iref, ij, 0)
        for _iref in range(iref + 1, self.nr):
            idx = np.nonzero(self.ir[_iref] >= iref)
            self.ir[_iref][idx] += 1
            idx = np.nonzero(self.ij[_iref] >= iref)
            self.ij[_iref][idx] += 1
        return iref

    def plot(self, x=None, y=None, grid='velocity', ax=None, rf=True, ir=True,
             ij=True, show_grid=False, apply_jumps=True, colorbar=False,
             vmin=None, vmax=None, outfile=None, xlim=None, ylim=None,
             aspect=1):
        """
        Plot the velocity grid and reflectors.

        :param x,y: Coordinate values of 2D slice to plot. Default is to plot
            the first x-z plane in the model.
        :param grid: Determines what type of grid values to plot. Options are
            'velocity' (default), 'slowness', and 'twt' (two-way travel
            time).
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param rf: Plot a thin black line for each reflector. Default is
            ``True``.
        :param ir: Plot bold white line for portion of reflector depths
            that are active in the inversion (i.e., ir>=1). Default is 
            ``True``.
        :param ij: Plot bold white line for portion of reflector slowness
            jumps that are active in the inversion (i.e., ij>=0). Default is
            ``True``.
        :param apply_jumps: Determines whether or not to apply slowness jumps
            to the grid before plotting. Default is ``True``.
        :param colorbar: Show a colorbar. Default is ``True``.
        :param vmin, vmax: Used to scale the grid to 0-1. If
            either is ``None`` (default), the min and max of the grid is
            used.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        # Pull slice from model if not already 2D
        if (x is None) and (y is None):
            if self.ny == 0:
                vm = self
            else:
                vm = self.slice_along_xy_line(x=self.x,
                                         y=self.y[0] * np.ones(self.nx),
                                         dx=self.dx)
        else:
            vm = self.slice_along_xy_line(x=x, y=y, dx=min(self.dx, self.dy))
        # Apply jumps
        if apply_jumps:
            vm.apply_jumps()
        # Plot the slice
        vm._plot2d(grid=grid, ax=ax, rf=rf, ir=ir, ij=ij,
                   show_grid=show_grid, vmin=vmin, vmax=vmax,
                   colorbar=colorbar, outfile=outfile, xlim=xlim,
                   ylim=ylim, aspect=aspect)
        # remove the jumps
        if apply_jumps:
            vm.remove_jumps()

    def plot_surface(self, idx, ax=None, outfile=None):
        """
        Plot a surface.

        :param idx: Index of the surface to plot.
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param colorbar: Show a colorbar. Default is ``True``.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        ax.imshow(self.rf[idx].transpose(),
                  extent=(self.r1[0], self.r2[0], self.r2[1], self.r1[1]))
        plt.xlim(self.r1[0], self.r2[0])
        plt.ylim(self.r1[1], self.r2[1])
        plt.xlabel('x (km)')
        plt.ylabel('y (km)')
        if outfile:
            fig.savefig(outfile)
        if show:
            plt.show()

    def plot_smooth_and_jumped_model(self, x=None, y=None, grid='velocity',
                                     rf=True, ir=True, ij=True,
                                     apply_jumps=True, outfile=None):
        """
        Plot a comparision of model grids with and without jumps.

        :param x,y: Coordinate values of 2D slice to plot. Default is to plot
            the first x-z plane in the model.
        :param grid: Determines what type of grid values to plot. Options are
            'velocity' (default), 'slowness', and 'twt' (two-way travel
            time).
        :param rf: Plot a thin white line for each reflector. Default is
            ``True``.
        :param ir: Plot bold white line for portion of reflector depths
            that are active in the inversion (i.e., ir>0). Default is ``True``.
        :param ij: Plot bold white line for portion of reflector slowness jumps
            that are active in the inversion (i.e., ij>0). Default is ``True``.
        :param apply_jumps: Determines whether or not to apply slowness jumps
            to the grid before plotting. Default is ``True``.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        fig = plt.figure()
        ax = fig.add_subplot(211)
        self.plot(ax=ax, rf=False, ir=False, ij=False, apply_jumps=False,
                grid=grid)
        ax.set_title('Smooth Model')
        ax = fig.add_subplot(212)
        self.plot(ax=ax, rf=False, ir=False, ij=False, apply_jumps=True,
                grid=grid)
        ax.set_title('Jumped Model')
        if outfile:
            fig.savefig(outfile)
        else:
            plt.show()

    def _plot2d(self, grid='velocity', ax=None, rf=True, ir=True, ij=True,
                show_grid=False, colorbar=True, vmin=None, vmax=None,
                outfile=None, aspect=None, ylim=None, xlim=None):
        """
        Plot a 2D model.

        Keyword Arguments
        -----------------
        :param grid: Determines what type of grid values to plot. Options are
            'velocity' (default), 'slowness', and 'twt' (two-way travel
            time).
        ax : {None, :class:`matplotlib.Axes.axes`}
            Axes to plot into. Default is to create a new figure and axes.
        rf : bool
            Plot a thin black line for each reflector.
        ir : bool
            Plot bold white line for portion of reflector depths
            that are active in the inversion (i.e., ir>0).
        ij : bool
            Plot bold black line for portion of reflector slowness jumps
            that are active in the inversion (i.e., ij>0).
        grid : array_like
            Grid to plot as base plot. Default is to plot slowness or
            velocity from ``self.sl``.
        show_grid : bool
            If true, plot the grid mesh.
        colorbar : bool
            Show a colorbar.
        vmin, vmax : {None, scalar}
            Used to scale the velocity/slowness grid to 0-1. If
            either is ``None`` (default), the min and max grid values will be
            used.
        outfile : {None, str}
            Filename to save the plot to. Extension is used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg.
        aspect : {None, 'auto', 'equal', scalar}
            If 'auto', changes the image aspect ratio to match that of the
            axes. If 'equal', the axes aspect ratio is changed to match that
            of the model extent.  If None, defaults to the matplotlib
            configuration ``image.aspect`` value.
        """
        assert self.ny == 1, "Model must be 2D with ny=1."

        grid = np.asarray([d[0] for d in self.grids.__getattribute__(grid)])

        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        
        img = ax.imshow(grid.transpose(), vmin=vmin, vmax=vmax,
            extent=(self.r1[0], self.r2[0], self.r2[2], self.r1[2]),
            aspect=aspect)

        if show_grid:
            
            for x in self.x:
                ax.plot([x, x], [self.r1[2], self.r2[2]], '-k')

            for z in self.z:
                ax.plot([self.r1[0], self.r2[0]], [z, z], '-k')
                

        for iref in range(0, self.nr):
            if rf:
                ax.plot(self.x, self.rf[iref], '-k')
            if ir:
                idx = np.nonzero(self.ir[iref].flatten() >= 0)
                ax.plot(self.x[idx], self.rf[iref][idx], '-w', linewidth=5)
            if ij:
                idx = np.nonzero(self.ij[iref].flatten() >= 0)
                ax.plot(self.x[idx], self.rf[iref][idx], '-k', linewidth=3)

        if xlim is None:
            plt.xlim(self.r1[0], self.r2[0])
        else:
            plt.xlim(xlim)
        if ylim is None:
            plt.ylim(self.r2[2], self.r1[2])
        else:
            plt.ylim(ylim)
        plt.xlabel('Offset (km)')
        plt.ylabel('Depth (km)')
        if colorbar:
            plt.colorbar(img, orientation='horizontal', fraction=0.05,
                         aspect=10)
        if outfile:
            fig.savefig(outfile)
        elif show:
            plt.tight_layout()
            plt.show()
        else:
            plt.draw()

    def plot_dws(self, x=None, y=None, ax=None, ir=True, ij=True,
             outfile=None):
        """
        Plot the derivative-weight sum grid and reflectors.

        :param x,y: Coordinate values of 2D slice to plot. Default is to plot
            the first x-z plane in the model.
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param ir: Plot bold white line for portion of reflector depths
            that are active in the inversion (i.e., ir>0). Default is ``True``.
        :param ij: Plot bold white line for portion of reflector slowness jumps
            that are active in the inversion (i.e., ij>0). Default is ``True``.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        if not hasattr(self, 'dws_sl'):
            msg = 'Instance has does not have a DWS grid to plot.'
            msg += ' Please use read_dws_grid() to load one.'
            raise AttributeError(msg)
        # Pull slice from model if not already 2D
        if (x is None) and (y is None):
            vm = self
        else:
            vm = slice_along_xy_line(x=x, y=y, dx=min(self.dx, self.dy))
        # Plot the slice
        vm._plot2d(velocity=False, ax=ax, grid=np.log10(self.dws_sl),
                   outfile=outfile)

    def plot_profile(self, x=None, y=None, z=None, velocity=True,
                     ax=None, apply_jumps=True, **kwargs):
        """
        Plot a 1D profile from the model grid.

        :param x,y,z: Coordinate value of profile to plot. Give two
            of the three. Default is to plot the first collumn in the model.
        :param velocity: Determines whether to grid values in units
            of velocity or slowness. Default is to plot velocity.
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create and show a new figure.
        :param apply_jumps: Determines whether or not to apply slowness jumps
            to the grid before plotting. Default is ``True``.
        """
        if apply_jumps:
            self.apply_jumps()
        if False not in [v is None for v in [x, y, z]]:
            x = self.r1[0]
            y = self.r1[1]
            z = None
        if (x is not None) and (y is not None) and (z is None):
            # Plot z vs. v
            z0 = kwargs.pop('z0', 0)
            ix, = self.x2i([x])
            iy, = self.y2i([y])
            xval = self.sl[ix, iy, :]
            yval = self.z - z0
            ylabel = 'Depth (km)'
            title = 'x = {:}, y = {:} (km)'.format(x, y)
            reverse = True
        elif (x is not None) and (y is None) and (z is not None):
            # Plot v vs. y
            xval = self.y
            ix, = self.x2i([x])
            iz, = self.z2i([z])
            yval = self.sl[ix, :, iz]
            xlabel = 'x-offset (km)'
            title = 'x = {:}, z = {:} (km)'.format(x, z)
            reverse = False
        elif (x is None) and (y is not None) and (z is not None):
            # Plot v vs. x
            xval = self.x
            iy, = self.y2i([x])
            iz, = self.z2i([z])
            yval = self.sl[:, ix, iz]
            xlabel = 'y-offset (km)'
            title = 'y = {:}, z = {:} (km)'.format(y, z)
            reverse = False
        else:
            msg = 'Must specify two of: x, y, z.'
            raise ValueError(msg)
        if velocity:
            if reverse:
                xval = 1. / xval
                xlabel = 'Velocity (km/s)'
            else:
                yval = 1. / yval
                ylabel = 'Velocity (km/s)'
        else:
            if reverse:
                xlabel = 'Slowness (s/km)'
            else:
                ylabel = 'Slowness (s/km)'
        # Make a new figure
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        # Plot
        ax.plot(xval, yval, **kwargs)
        if reverse:
            ax.set_ylim(ax.get_ylim()[::-1])
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        # Show (TODO save, draw) plot
        if show:
            plt.show()
        else:
            plt.draw()
        if apply_jumps:
            self.remove_jumps()

    def _slice_for_plot(self, x=None, y=None, z=None, grid=None):
        """
        Extract a slice from the 3D VM model slowness grid for plotting.

        :param x,y,z: Coordinate value of orthogonal slice to extract. Give
            one of the three.
        :param plot_info: If True, also returns plot extents and axis
            labels. Default is False.
        :param grid: Grid to slice. Default is to slice the slowness
            grid.
        :returns sl: Slice as a 2D stack of numpy arrays.
        :returns bounds: Interface depths
        :returns extents: Extents of the 2D slice as a tuple.
        :returns labels: Slice axis labels returned as a tuple.
        """
        raise DeprecationWarning
        # Prevent dividing by zero for 2d models
        if self.dx == 0:
            dx = 1
        else:
            dx = self.dx
        if self.dy == 0:
            dy = 1
        else:
            dy = self.dy
        if self.dz == 0:
            dz = 1
        else:
            dz = self.dz
        # Set grid to slice
        if grid is None:
            grid = self.sl
        # Extract the grid slice
        if (x is not None) and (y is None) and (z is None):
            # Take a slice in the y-z plane
            ix = int((x - self.r1[0]) / dx)
            sl = grid[ix]
            _x = list(np.linspace(self.r1[1], self.r2[1], self.ny))
            x = []
            y = []
            for iref in range(0, self.nr):
                x += _x
                x += [None]
                y += [v for v in self.rf[iref][ix]]
                y += [None]
            dims = (1, 2)
            labels = ('y-offset (km)', 'Depth (km)')
        elif (x is None) and (y is not None) and (z is None):
            # Take a slice in the x-z plane
            iy = int((y - self.r1[1]) / dy)
            sl = np.asarray([d[iy] for d in grid])
            _x = list(np.linspace(self.r1[0], self.r2[0], self.nx))
            x = []
            y = []
            for iref in range(0, self.nr):
                x += _x
                x += [None]
                y += [v[iy] for v in self.rf[iref]]
                y += [None]
            dims = (0, 2)
            labels = ('x-offset (km)', 'Depth (km)')
        elif (x is None) and (y is None) and (z is not None):
            # Take a slice in the x-y plane
            iz = int((z - self.r1[2]) / dz)
            sl = grid.transpose()[iz]
            x = [None]
            y = [None]
            dims = (0, 1)
            labels = ('x-offset (km)', 'y-offset (km)')
        else:
            msg = 'Specify one (and only one) of: x, y, z'
            raise ValueError(msg)
        bounds = [x, y]
        extents = (self.r1[dims[0]], self.r2[dims[0]],
                   self.r1[dims[1]], self.r2[dims[1]])
        return sl, bounds, extents, labels

    def point2layer(self, x, y, z):
        """
        Find the layer that a point is in.

        Parameters
        ----------
        x, y, z: float
            x, y, z coordinates of the point

        Returns
        -------
        ilyr: int
            Index of the layer that the point is within.
        """
        ix = self.x2i([x])[0]
        iy = self.y2i([y])[0]
        for iref in range(self.nr + 1):
            z0, z1 = self.get_layer_bounds(iref)
            if (z >= z0[ix, iy]) and (z <= z1[ix, iy]):
                return iref
        return None


    # Properties
    def _get_sl(self):
        """
        Getter for aliasing sl to grids.slowness
        """
        return self.grids.slowness

    def _set_sl(self, value):
        """
        Setter for aliasing sl to grids.slowness
        """
        self.grids.slowness = value
        
    sl = property(fget=_get_sl, fset=_set_sl)

    def _get_dx(self):
        """
        Getter for aliasing dx to grids.dx
        """
        return self.grids.dx

    def _set_dx(self, value):
        """
        Setter for aliasing dx to grids.dx
        """
        self.grids.dx = value
        
    dx = property(fget=_get_dx, fset=_set_dx)

    def _get_dy(self):
        """
        Getter for aliasing dy to grids.dy
        """
        return self.grids.dy

    def _set_dy(self, value):
        """
        Setter for aliasing dy to grids.dy
        """
        self.grids.dy = value
        
    dy = property(fget=_get_dy, fset=_set_dy)

    def _get_dz(self):
        """
        Getter for aliasing dz to grids.dz
        """
        return self.grids.dz

    def _set_dz(self, value):
        """
        Setter for aliasing dz to grids.dz
        """
        self.grids.dz = value
        
    dz = property(fget=_get_dz, fset=_set_dz)

    def _get_nr(self):
        """
        Returns the number of reflectors in the model.
        """
        if len(self.rf.shape) == 0:
            return 0
        else:
            return self.rf.shape[0]
    nr = property(fget=_get_nr)

    def _get_nx(self):
        """
        Returns the number of x-nodes in the model grid.
        """
        return self.grids.nx
    nx = property(fget=_get_nx)

    def _get_ny(self):
        """
        Returns the number of y-nodes in the model grid.
        """
        return self.grids.ny
    ny = property(fget=_get_ny)

    def _get_nz(self):
        """
        Returns the number of z-nodes in the model grid.
        """
        return self.grids.nz
    nz = property(fget=_get_nz)

    def _get_x(self):
        """
        Returns an array of x-axis coordinates.
        """
        return self.r1[0] + np.asarray(range(0, self.nx)) * self.dx
    x = property(fget=_get_x)

    def _get_y(self):
        """
        Returns an array of y-axis coordinates.
        """
        return self.r1[1] + np.asarray(range(0, self.ny)) * self.dy
    y = property(fget=_get_y)

    def _get_z(self):
        """
        Returns an array of z-axis coordinates.
        """
        return self.r1[2] + np.asarray(range(0, self.nz)) * self.dz
    z = property(fget=_get_z)

    def _get_r1(self):
        """
        Returns a tuple of minimum model coordinates
        """
        return (self.grids.xmin, self.grids.ymin, self.grids.zmin)

    def _set_r1(self, value):
        """
        Sets minimum model coordinates from a tuple of x, y, z values
        """
        self.grids.xmin, self.grids.ymin, self.grids.zmin = value
    
    r1 = property(fget=_get_r1, fset=_set_r1)

    def _get_r2(self):
        """
        Returns a tuple of maximum model coordinates
        """
        return (self.x[-1], self.y[-1], self.z[-1])
    r2 = property(fget=_get_r2)

    def _get_layers(self):
        """
        Returns a grid of layer indices for each node in the slowness grid.
        """
        lyr = np.ones((self.nx, self.ny, self.nz))
        for iref in range(self.nr + 1):
            # top, bottom boundary depths for current layer
            z0, z1 = self.get_layer_bounds(iref)
            for ix in range(0, self.nx):
                for iy in range(0, self.ny):
                    iz = self.zrange2i(z0[ix, iy], z1[ix, iy])
                    lyr[ix, iy, iz] = iref
        return lyr
    layers = property(fget=_get_layers)


class VMGrids(object):
    """
    Class for managing grids in VM Tomography models
    """
    def __init__(self, dx, dy, dz, sl, xmin=0, ymin=0, zmin=0):
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.slowness = sl
        self.xmin = xmin
        self.ymin = ymin
        self.zmin = zmin

    def _get_nx(self):
        """
        Returns the number of x-nodes in the model grid.
        """
        return self.slowness.shape[0]
    nx = property(fget=_get_nx)

    def _get_ny(self):
        """
        Returns the number of y-nodes in the model grid.
        """
        return self.slowness.shape[1]
    ny = property(fget=_get_ny)

    def _get_nz(self):
        """
        Returns the number of z-nodes in the model grid.
        """
        return self.slowness.shape[2]
    nz = property(fget=_get_nz)

    
    def _get_twt(self):
        """
        Returns the model grid in verticle two-way travel time
        """
        twt = 2 * self.dz * np.cumsum(self.slowness, axis=2)
        for ix in range(self.nx):
            for iy in range(self.ny):
                twt[ix, iy, :] -= twt[ix, iy, 0]
        return twt
    twt = property(fget=_get_twt)

    def _get_velocity(self):
        """
        Returns the model grid in velocity
        """
        return 1. / self.slowness

    def _set_velocity(self, value):
        """
        Sets the main slowness grid using velocity values
        """
        self.slowness = 1. / value

    velocity = property(fget=_get_velocity, fset=_set_velocity)


class VMTime(object):
    """
    Class for working with VM Tomography models in time, rather than depth.
    """
    def __init__(self, vm, dt=0.1):
        self._vm = vm
        self.dt = dt

    def write_ascii_grid(self, filename, grid='velocity'):


        file = open(filename, 'w')
        # Write a header
        file.write('# VM Tomography velocity model grid in time\n')
       
        if hasattr(self._vm, 'file'):
            file.write('#\n# Exported from: {:}\n'.format(self._vm.file.name))
        else:
            file.write('#\n# Exported from: memory\n') 
        file.write('# Created by: {:} (version {:})\n'\
                   .format(__name__, __version__))
        file.write('# Created on: {:}\n'.format(datetime.datetime.now()))
        file.write('#\n')
        units = ', '.join(['{:} [{:}]'.format(v, UNITS[v])\
                for v in ['x', 'y', 'twt', grid]])
        file.write('# {:}\n'.format(units))
        twt = self.twt[:]
        nt = len(twt)
        grd = self.grids.__getattribute__(grid)[:, :, :]
        for ix in range(0, self._vm.nx):
            x = (self._vm.r1[0] + ix * self._vm.dx)
            for iy in range(0, self._vm.ny):
                y = (self._vm.r1[1] + iy * self._vm.dy)
                for it in range(0, nt):
                    file.write('{:}, {:}, {:}, {:}\n'\
                               .format(x, y, twt[it], grd[ix, iy, it]))
        file.close()

        

    def _plot2d(self, ax=None, grid='velocity', vmin=None, vmax=None,
            aspect=1):
        """
        Plot the time model. 
        """
        assert self._vm.ny == 1, "Model must be 2D with ny=1."
        grid = np.asarray([d[0] for d in self.grids.__getattribute__(grid)])

        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False

        img = ax.imshow(grid.transpose(), vmin=vmin, vmax=vmax,
                extent=(self._vm.r1[0], self._vm.r2[0], self.twt[0],
                    self.twt[-1]), aspect=aspect)

        if show:
            plt.show()
        else:
            plt.draw()
    
    def _get_twt(self):
        """
        Calculates time range
        """
        twt = np.arange(self._vm.grids.twt.min(),
               self._vm.grids.twt.max(), self.dt)
        return twt
    twt = property(fget=_get_twt)

    def _get_sl(self):
        """
        Interpolates a grid of slowness values for a uniform time grid
        """
        sl = np.zeros((self._vm.nx, self._vm.ny, len(self.twt)))
        for ix in self._vm.xrange2i():
            for iy in self._vm.yrange2i():
                twt2sl = interp1d(self._vm.grids.twt[ix, iy, :],
                        self._vm.grids.slowness[ix, iy, :], kind='linear')
                sl[ix, iy, :] = twt2sl(self.twt)

        return sl

    def _get_grids(self):
        """
        Reinitializes the grids
        """
        grids = VMGrids(self._vm.dx, self._vm.dy, self.dt, self._get_sl(),
                xmin=self._vm.r1[0], ymin=self._vm.r1[1], zmin=0)
        return grids

    grids = property(fget=_get_grids)






def readVM(file, endian=ENDIAN, head_only=False):
    """
    Read a VM model binary file.

    :param file: An open file-like object or a string which is
        assumed to be a filename.
    :param endian: The endianness of the file. Default is
        to use machine's native byte order.
    :param head_only: Determines whether or not to read the grid
        data. Useful is only interested in the grid dimension values.
        Default is to read the entire file.
    """
    vm = VM(init_model=False)
    vm.read(file, endian=endian, head_only=head_only)
    return vm
