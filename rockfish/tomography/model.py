"""
Support for working with velocity models.

Reflection Indices
==================

The underlying raytracing and inversion codes are written in
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
import numpy as np
from scipy.interpolate import interp1d, interp2d
import datetime
from struct import unpack
import matplotlib.pyplot as plt
from rockfish import __version__
from rockfish.utils.string_tools import pad_string
from rockfish.segy.segy import SEGYFile, SEGYTrace
from rockfish.segy.segy import pack

ENDIAN = pack.BYTEORDER

class VM(object):
    """
    Class for working with VM Tomography velocity models.
    """
    def __init__(self, r1=(0, 0, 0), r2=(250, 0, 30),
                         dx=0.5, dy=1, dz=0.1, nr=0,
                 init_model=True):
        """
        Create a new model instance.

        :param r1: Minimum values for grid dimensions given as the 
            tuple ``(xmin, ymin, zmin)``. Default is ``(0,0,0)``.
        :param r2: Maximum values for grid dimensions given as the 
            tuple ``(xmax, ymax, zmax)``. Default is ``(250,0,30)``.
        :param dx: Spacing between x-nodes. Default is ``0.5``.
        :param dy: Spacing between y-nodes. Default is ``1``.
        :param dz: Spacing between z-nodes. Default is ``0.1``.
        :param nr: Number of interfaces in the model. Used to 
            define the size of the interface arrays. Default is ``0``.
        :param init_model: Determines whether or not to initialize
            parameters and data arrays. Default is True.
        """
        if init_model:
            self.init_model(r1, r2, dx, dy, dz, nr)

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
        banner = self.pad_string(title, char='=') 
        sng = banner + '\n'
        sng += self._print_header()
        sng += banner
        # TODO: write extended information
        #if not extended:
        #    sng += '\n[Use "print VM.__str__(extended=True)" for'
        #    sng += ' more detailed information]'
        return sng

    def _print_header(self):
        """
        Format header values as plain-text.
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

    def _print_layer_info(self, idx):
        """
        Print details about a layer.

        :param idx: Index of layer to get information for.
        """
        raise NotImplementedError

    def calculate_jumps(self, iref, xmin=None, xmax=None, ymin=None, ymax=None):
        """
        Calculate slowness jumps.

        :param iref: Index of interface to calculate slowness jumps on.
        :param xmin, xmax: Set the x-coordinate limits for 
            calculating jumps. Default is to calculate jumps over the entire
            x-domain.
        :param ymin, ymax: Set the y-coordinate limits for 
            calculating jumps. Default is to calculate jumps over the entire
            y-domain.
        """
        _, z0 = self.get_layer_bounds(iref)
        for ix in self.xrange2i(xmin, xmax):
            for iy in self.yrange2i(ymin, ymax):
                iz0 = self.z2i([z0[ix,iy]])[0]
                sl0 = self.sl[ix,iy,iz0]
                sl1 = self.sl[ix,iy,iz0+1]
                self.jp[iref-1][ix][iy] = sl1 - sl0

    def apply_jumps(self, remove=False):
        """
        Apply slowness jumps to the grid.

        :param remove: Determines whether jumps should be removed or applied.
            Default is ``False`` (i.e., jumps are applied).
        """
        for iref in range(0, self.nr):
            z0, _ = self.get_layer_bounds(iref + 1)
            for ix in range(0, self.nx):
                for iy in range(0, self.ny):
                    iz0 = self.z2i([z0[ix,iy]])[0]
                    if remove is False:
                        self.sl[ix, iy, iz0:] += self.jp[iref, ix, iy]
                    else:
                        self.sl[ix, iy, iz0:] -= self.jp[iref, ix, iy]

    def remove_jumps(self):
        """
        Remove slowness jumps from the grid.
        """
        self.apply_jumps(remove=True)

    def define_stretched_layer_velocities(self, idx, vel=[None, None],
                                          xmin=None, xmax=None, ymin=None,
                                          ymax=None, kind='linear'):
        """
        Define velocities within a layer by stretching a velocity function.

        At each x,y position in the model grid, the list of given velocities
        are first distributed proportionally across the height of the layer.
        Then, this z,v function is used to interpolate velocities for each
        depth node in the layer.
        
        :param idx: Index of layer to work on. 
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
        z0, z1 = self.get_layer_bounds(idx)
        # Define velocity function at each x,y point
        vel = np.asarray(vel)
        nvel = len(vel)
        for ix in self.xrange2i(xmin, xmax):
            for iy in self.yrange2i(ymin, ymax):
                iz0, iz1 = self.z2i((z0[ix,iy], z1[ix,iy]))
                iz1 += 1
                z = self.z[iz0:iz1]
                if len(z) == 0:
                    # in pinchout, nothing to do
                    continue
                # Make a copy of velocities for this iteration
                _vel = np.copy(vel)
                # Get top and bottom velocities, if they are None
                if vel[0] is None:
                    _vel[0] = 1./self.sl[ix, iy, max(iz0-1, 0)]
                if len(vel) > 1:
                    if vel[1] is None:
                        _vel[1] = 1./self.sl[ix, iy, min(iz1+1, self.nx)]
                # Pad interpolates for rounding to grid coordinates
                if nvel == 1:
                    # Set constant value
                    v = np.asarray([_vel])
                else:
                    # Interpolate velocities
                    zi = z0[ix,iy] + (z1[ix,iy] - z0[ix,iy])\
                            *np.arange(0., nvel)/(nvel - 1)
                    vi = np.copy(_vel)
                    if z[0] < zi[0]:
                        zi = np.insert(zi, 0, z[0])
                        vi = np.insert(vi, 0, _vel[0])
                    if z[-1] > zi[-1]:
                        zi = np.append(zi, z[-1])
                        vi = np.append(vi, _vel[-1])
                    zv = interp1d(zi, vi, kind=kind)
                    v = zv(z)
                self.sl[ix, iy, iz0:iz1] = 1./v

    def define_constant_layer_velocity(self, idx, v, xmin=None,
                                          xmax=None, ymin=None, ymax=None):
        """
        Define a constant velocity for an entire layer.

        :param idx: Index of layer to work on.
        :param v: Velocity.
        :param xmin, xmax: Set the x-coordinate limits for modifying
            velocities. Default is to change velocities over the entire
            x-domain.
        :param ymin, ymax: Set the y-coordinate limits for modifying
            velocities. Default is to change velocities over the entire
            y-domain.
        """
        self.define_stretched_layer_velocities(idx, [v], xmin=xmin, xmax=xmax,
                                              ymin=ymin, ymax=ymax)

    def define_variable_layer_gradient(self, idx, dvdz, v0=None):
        """
        Replace velocities within a layer by defining a gtradient that
        varies linearly in the horizontal directions.
        
        :param idx: Index of layer to work on.
        :param dvdz: List of velocity gradient values. Must be of shape
            (nx,ny).
        :param v0: List of velocities at the top of the layer. Must be of 
            shape (nx,ny). Default is to use the value at the 
            base of the overlying layer.
        """
        z0, z1 = self.get_layer_bounds(idx)
        for ix in range(0, self.nx):
            for iy in range(0, self.ny):
                iz0, iz1 = self.z2i((z0[ix,iy], z1[ix,iy]))
                iz1 += 1
                z = self.z[iz0:iz1] - self.z[iz0]
                if v0 is None:
                    if iz0 == 0:
                        _v0 = 0.
                    else:
                        _v0 = 1./self.sl[ix, iy, iz0-1]
                else:
                    _v0 = v0[ix,iy] 
                self.sl[ix, iy, iz0:iz1] = 1./(_v0 + z*dvdz[ix,iy])

    def define_constant_layer_gradient(self, idx, dvdz, v0=None, xmin=None,
                                       xmax=None, ymin=None, ymax=None):
        """
        Replace velocities within a layer by defining a constant gradient.

        :param idx: Index of layer to work on.
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
        z0, z1 = self.get_layer_bounds(idx)
        for ix in self.xrange2i(xmin, xmax):
            for iy in self.yrange2i(ymin, ymax):
                iz0, iz1 = self.z2i((z0[ix,iy], z1[ix,iy]))
                iz1 += 1
                z = self.z[iz0:iz1] - self.z[iz0]
                if v0 is None:
                    if iz0 == 0:
                        _v0 = 0.
                    else:
                        _v0 = 1./self.sl[ix, iy, iz0-1]
                else:
                    _v0 = v0
                self.sl[ix, iy, iz0:iz1] = 1./(_v0 + z*dvdz)

    def get_layer_bounds(self, idx):
        """
        Get surfaces bounding a layer.
        
        :param idx: Index of layer of interest.
        :returns: z0, z1 arrays of top, bottom interface depths.
        """
        if idx == 0:
            z0 = np.ones((self.nx, self.ny))*self.r1[2]
        else:
            z0 = self.rf[idx-1]
        if idx >= self.nr:
            z1 = np.ones((self.nx, self.ny))*self.r2[2]
        else:
            z1 = self.rf[idx]
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
        nx = int(np.round((r2[0] - r1[0])/dx)) + 1
        ny = int(np.round((r2[1] - r1[1])/dy)) + 1
        nz = int(np.round((r2[2] - r1[2])/dz)) + 1
        # Copy variables
        self.r1 = r1
        self.dx = dx 
        self.dy = dy 
        self.dz = dz
        # Initialize arrays to all zeros
        self.sl = np.zeros((nx, ny, nz)) 
        self.rf = np.zeros((nr, nx, ny))
        self.jp = np.zeros((nr, nx, ny))
        self.ir = np.zeros((nr, nx, ny))
        self.ij = np.zeros((nr, nx, ny))
        # Set max dimensions
        self.r2 = (self.x[-1], self.y[-1], self.z[-1])

    def init_empty_model(self):
        """
        Initialize a new empty model.
        """
        self.r1 = (None, None, None)
        self.r2 = (None, None, None)
        self.dx = None
        self.dy = None
        self.dz = None
        self.sl = np.empty_like(0) 
        self.rf = np.empty_like(0) 
        self.jp = np.empty_like(0)
        self.ir = np.empty_like(0)
        self.ij = np.empty_like(0)

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
            data. Useful if one is only interested in the grid dimension values.
            Default is to read the entire file.
        """
        # Header information
        fmt = '{:}iiii'.format(endian)
        nx, ny, nz, nr = unpack(fmt, file.read(4*4))
        fmt = '{:}fff'.format(endian)
        self.r1 = unpack(fmt, file.read(4*3))
        self.r2 = unpack(fmt, file.read(4*3))
        fmt = '{:}fff'.format(endian)
        self.dx, self.dy, self.dz = unpack(fmt, file.read(4*3))
        if head_only is True:
            self.sl = np.empty((nx, ny, nz)) 
            self.rf = np.empty((nr, nx, ny))
            self.jp = np.empty((nr, nx, ny))
            self.ir = np.empty((nr, nx, ny))
            self.ij = np.empty((nr, nx, ny))
            return
        # Slowness grid
        ngrid = nx*ny*nz
        fmt = endian + ('f' * ngrid)
        self.sl = np.asarray(unpack(fmt, file.read(4*ngrid)))
        # Interface depths and slowness jumps
        nintf = nx*ny*nr
        fmt = endian + 'f' * nintf
        self.rf = unpack(fmt, file.read(4*nintf))
        self.jp = unpack(fmt, file.read(4*nintf))
        # Interface flags
        fmt = endian + 'i' * nintf
        self.ir = unpack(fmt, file.read(4*nintf))
        self.ij = unpack(fmt, file.read(4*nintf))
        # Rearrage 1D arrays into 3D matrixes
        self._unpack_arrays(nx, ny, nz, nr)
        # Subtract 1 from array index flags to conform to Python convention
        self.ir -= 1
        self.ij -= 1

    def read_dws_grid(self, filename):
        """
        Read derivative-weight sum (DWS) data.

        :param filename: Filename of an ASCII with columns: x, y, z, dws.
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
            ``'ascii_grid'``. See documentation for functions labeled
        :param endian: The endianness of the file for binary formats.
            Default is to use the machine's native byte order.
        """
        if fmt is 'vm':
            self.write_vm(filename, endian=endian)
        elif fmt is 'ascii_grid':
            self.write_ascii_grid(filename, **kwargs)
        elif fmt is 'segy':
            self.write_segy(filename, endian=endian, **kwargs)
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
        self._pack_arrays() # must be called after writing size properties 
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

    def write_ascii_grid(self, filename, meters=False, velocity=False):
        """
        Write VM model slowness grid in an ASCII format.

        :param filename: Name of a file to write data to.
        :param meters: Output distance units in meters. Default is
            kilometers.
        :param velocity: Output slowness values as velocity. Default
            is slowness.
        """
        file = open(filename, 'w')
        # Write a header
        file.write('# VM Tomography velocity model grid\n')
        if meters is True:
            xscale = 1000.
            units = 'x_m y_m z_m'
            if velocity is True:
                units += ' velocity_meters_per_second'
            else:
                units += ' slowness_seconds_per_meter'
        else:
            xscale = 1.
            units = 'x_km y_km z_km'
            if velocity is True:
                units += ' velocity_kilometers_per_second'
            else:
                units += ' slowness_seconds_per_kilometer'
        file.write('# {:}\n'.format(units))
        file.write('#\n# Exported from: {:}\n'.format(self.file.name))
        file.write('# Created by: {:} (version {:})\n'\
                   .format(os.path.basename(__file__), __version__))
        file.write('# Created on: {:}\n'.format(datetime.datetime.now()))
        file.write('#\n# Grid overview:\n')
        for line in self._get_full_overview().split('\n'):
            file.write('# {:}\n'.format(line))
        for ix in range(0, self.nx):
            x = (self.r1[0] + ix * self.dx)*xscale
            for iy in range(0, self.ny):
                y = (self.r1[1] + iy * self.dy)*xscale
                for iz in range(0, self.nz):
                    z = (self.r1[2] + iz * self.dz)*xscale
                    if velocity is True:
                        _sl = xscale/self.sl[iz][iy][ix]
                    else:
                        _sl = self.sl[iz][iy][ix]/xscale
                    file.write('{:20.3f} {:20.3f} {:20.3f} {:10.5f}\n'\
                               .format(x, y, z, _sl))
        file.close()

    def write_segy(self, filename, endian='>', meters=False, velocity=False):
        """
        Write the VM model slowness grid in the SEG-Y format.

        :param endian: The endianness of the file. Default is big
            endian (the SEG-Y standard).
        :param velocity: Output slowness values as velocity. Default
            is slowness.
        :param meters: Output distance units in meters. Default is
            kilometers.
        """
        # Copy data to SEGYFile instance
        # TODO
        raise NotImplementedError

    def vm2segy(self, endian='>', meters=False, velocity=False):
        """
        Convert VM slowness grid to a SEGYFile instance.

        :param endian: The endianness of the file. Default is big
            endian (the SEG-Y standard).
        :param velocity: Output slowness values as velocity. Default
            is slowness.
        :param meters: Output distance units in meters. Default is
            kilometers.
        """
        segy = SEGYFile()
        # Set header values
        segy.binary_file_header.number_of_data_traces_per_ensemble = 1
        segy.binary_file_header.number_of_samples_per_data_trace = self.nz
        segy.binary_file_header.data_sample_format_code = 5
        segy.binary_file_header.endian = endian
        # Set distance scale (* 100 to get integer for SEG-Y header)
        if meters is True:
            xscale = 1000.
        else:
            xscale = 1.
        # Copy grid values to traces 
        for iy in range(0, self.ny):
            y = (self.r1[1] + iy * self.dy)*xscale*100.
            for ix in range(0, self.nx):
                x = (self.r1[0] + ix * self.dx)*xscale*100.
                tr = SEGYTrace()
                tr.data_encoding = segy.binary_file_header\
                        .data_sample_format_code
                tr.header.inline_number = iy
                tr.header.crossline_number = ix
                tr.header.coordinate_units = 1
                tr.header.scalar_to_be_applied_to_all_coordinates = -100
                tr.header.group_coordinate_x = x
                tr.header.group_coordinate_y = y
                tr.header.source_coordinate_x = x
                tr.header.source_coordinate_y = y
                tr.header.number_of_samples_in_this_trace = self.nz
                tr.header.sample_interval_in_ms_for_this_trace \
                        = self.dz * 1000.
                if velocity is True:
                    tr.data = np.float32(xscale/self.sl[ix][iy][:])
                else:
                    tr.data = np.float32(self.sl[ix][iy][:]/xscale)
                segy.traces.append(tr)
        return segy

    def project_model(self, angle, dx=None, x=None, y=None):
        """
        Project a 2D model onto another line.

        :param angle: Clockwise angle in degrees from the current line.
        :param dx: x-coordinate grid spacing. Default is to use the same grid
            spacing as in the current model.
        :param x,y: Coordinate values of 2D slice to project. Default is to project 
            the first x-z plane in the model.
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
        xdim = (vm0.r2[0] - vm0.r1[0])/np.cos(np.deg2rad(angle))
        xmax = np.floor(xdim/dx)*dx
        print "xmax = ",xmax
        vm1 = VM(r1=(0, 0, vm0.r1[2]), r2=(xmax, 0, vm0.r2[2]),
                 dx=dx, dy=1, dz=vm0.dz, nr=vm0.nr)
        print vm1.r2, vm1.x.max()
        # New model coordinates in old model
        x0 = vm1.x*np.cos(np.deg2rad(angle))
        print x0.max()
        # Project boundaries
        for iref in range(0, vm0.nr):
            # setup interpolators
            x2rf = interp1d(vm0.x, [v[0] for v in vm0.rf[iref]], kind='linear')
            x2jp = interp1d(vm0.x, [v[0] for v in vm0.jp[iref]], kind='linear')
            x2ir = interp1d(vm0.x, [v[0] for v in vm0.ir[iref]], kind='nearest')
            x2ij = interp1d(vm0.x, [v[0] for v in vm0.ij[iref]], kind='nearest')
            # do the interpolating
            vm1.rf[iref] = np.asarray([[v] for v in x2rf(x0)])
            vm1.jp[iref] = np.asarray([[v] for v in x2jp(x0)])
            vm1.ir[iref] = np.asarray([[v] for v in x2ir(x0)])
            vm1.ij[iref] = np.asarray([[v] for v in x2ij(x0)])
        # Project velocities
        for iz in range(0, vm0.nz):
            x2sl = interp1d(vm0.x, vm0.sl[:,0,iz], kind='linear')
            vm1.sl[:,0,iz] = x2sl(x0)
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
            i0 = iref*(nx * self.ny)
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
        return ix*self.ny*self.nz + iy*self.nz + iz
    
    def interfacepoint2index(self, ix, iy, ir):
        """
        Convert a 3-component interface indices to a single index in the 1D
        packed interface arrays.

        :param ix: x-coordinate index
        :param iy: y-coordinate index
        :param ir: interface index
        """
        return ir*self.nx + ix*self.ny + iy

    def x2i(self, x):
        """
        Find an x index for an x coordinate.

        :param x: list of x coordinates in the model 
        :returns: list of nearest x index for the given coordinates
        """
        return [int((_x-self.r1[2])/self.dx) for _x in x]

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
        if xmax is None:
            xmax = self.r2[0]
        return range(self.x2i([xmin])[0], self.x2i([xmax])[0]+1)
    
    def y2i(self, y):
        """
        Find a y index for a y coordinate.

        :param y: list of y coordinates in the model 
        :returns: list of nearest y index for the given coordinates
        """
        return [int((_y-self.r1[2])/self.dy) for _y in y]   

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
        if ymax is None:
            ymax = self.r2[1]
        return range(self.y2i([ymin])[0], self.y2i([ymax])[0]+1)

    def z2i(self, z):
        """
        Find a z index for a z coordinate.

        :param z: list of z coordinates in the model 
        :returns: list of nearest z index for the given coordinates
        """
        return [int((_z-self.r1[2])/self.dz) for _z in z]

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
            zmin = self.r1[1]
        if zmax is None:
            zmax = self.r2[1]
        return range(self.z2i([zmin])[0], self.z2i([zmax])[0]+1)

    def gridpoint2position(self, ix, iy, iz):
        """
        Returns the x,y,z coordinates coresponding to a set of model indices.
        
        :param ix: x-coordinate index
        :param iy: y-coordinate index
        :param iz: z-coordinate index
        :returns: x, y, z 
        """
        x = ix*self.dx + self.r1[0]
        y = iy*self.dy + self.r1[1]
        z = iz*self.dz + self.r1[2]
        return x,y,z

    def slice_along_xy_line(self, x, y, dx=None):
        """
        Extract a vertical slice along a line.

        :param x,y: Lists of coordinates to take slice along.
        :param dx: Grid spacing for the new model. Default is to use
            the x-coordinate spacing of the current model.
        :returns: VM model along the specified line
        """
        assert len(x) == len(y), 'x and y must be the same length'
        assert max(x) <= self.r2[0], 'x coordinates exceed model domain'
        assert min(x) >= self.r1[0], 'x coordinates exceed model domain'
        assert max(y) <= self.r2[1], 'y coordinates exceed model domain'
        assert min(y) > self.r1[1], 'y coordinates exceed model domain'
        # Calculate distance along line
        _xline = [0]
        for i in range(1,len(x)):
            x0 = x[i-1]
            y0 = y[i-1]
            x1 = x[i]
            y1 = y[i]
            deltx = np.sqrt((x1-x0)**2 + (y1-y0)**2)
            _xline.append(_xline[i-1] + deltx)
        # Setup new model
        vm = VM()
        vm.r1 = (min(_xline), 0, self.r1[2])
        vm.r2 = (max(_xline), 0, self.r2[2])
        if dx is None:
            vm.dx = self.dx
        else:
            vm.dx = dx
        vm.nx = int(np.floor((max(_xline) - min(_xline))/vm.dx))
        xline = np.linspace(min(_xline), max(_xline), vm.nx)
        vm.dy = 1
        vm.dz = self.dz
        vm.ny = 1
        vm.nz = self.nz
        vm.nr = self.nr
        if hasattr(self, 'dws_sl'):
            vm.dws_sl = []
        # Pull slowness grid and interface values along line
        interp_y = interp1d(x, y)
        interp_x = interp1d(_xline, x)
        for iref in range(0, self.nr):
            vm.rf.append([])
            vm.jp.append([])
            vm.ir.append([])
            vm.ij.append([])
        for _xl in xline:
            # get coordinates of position on line
            _x = interp_x(_xl)
            _y = interp_y(_x)
            # get indices in 3D model
            ix = self._x2i(_x)
            iy = self._y2i(_y)
            # get slowness collumn
            vm.sl.append([self.sl[ix][iy]])
            # DWS grid
            if hasattr(self, 'dws_sl'):
                vm.dws_sl.append([self.dws_sl[ix][iy]])
            # get interfaces
            for iref in range(0, self.nr):
                vm.rf[iref].append([self.rf[iref][ix][iy]])
                vm.jp[iref].append([self.jp[iref][ix][iy]])
                vm.ir[iref].append([self.ir[iref][ix][iy]])
                vm.ij[iref].append([self.ij[iref][ix][iy]])
        vm.rf = np.asarray(vm.rf)
        vm.jp = np.asarray(vm.jp)
        vm.ir = np.asarray(vm.ir)
        vm.ij = np.asarray(vm.ij)
        return vm

    def remove_interface(self, idx):
        """
        Remove an interface from the model.
        
        :param idx: Index of the interface to remove.
        """
        self.rf = np.delete(self.rf, idx, 0)
        self.jp = np.delete(self.jp, idx, 0)
        self.ir = np.delete(self.ir, idx, 0)
        self.ij = np.delete(self.ij, idx, 0)
        print "Removed interface with index {:}.".format(idx)

    def insert_interface(self, rf, jp=None, ir=None, ij=None):
        """
        Insert an interface.

        :param rf: Interface depths given as a Numpy array_like object with
            shape ``(nx, ny)``.
        :param jp: Slowness jumps given as a Numpy array_like object
            with shape ``(nx, ny)``. Default is to set the slowness jump for 
            all nodes on the new interface to zero.
        :param ir: Indices of the interfaces to use in the inversion
            for interface depths, given as a Numpy array_like object
            with shape ``(nx, ny)``. A ``-1`` value indicates that a node 
            should not be used in the inversion. Default is to assign all 
            nodes to the index of the new interface.
        :param ij: Indices of the interfaces to use in the inversion
            for slowness jumps, given as a Numpy array_like object
            with shape ``(nx, ny)``. A ``-1`` value indicates that a node
            should not be used in the inversion. Default is to assign all
            nodes to the index of the new interface.
        """
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
        # Insert arrays for new interface
        if iref == 0:
            self.rf = np.asarray([rf])
            self.jp = np.asarray([jp])
            self.ir = np.asarray([ir])
            self.ij = np.asarray([jp])
        else:
            self.rf = np.insert(self.rf, iref, rf, 0)
            self.jp = np.insert(self.jp, iref, jp, 0)
            self.ir = np.insert(self.ir, iref, ir, 0)
            self.ij = np.insert(self.ij, iref, ij, 0)
        print "Added interface with index {:}.".format(iref)

    def plot(self, x=None, y=None, velocity=True, ax=None, rf=True, ir=True,
             ij=True, apply_jumps=True, colorbar=False, vmin=None, 
             vmax=None, outfile=None):
        """
        Plot the velocity grid and reflectors.

        :param x,y: Coordinate values of 2D slice to plot. Default is to plot 
            the first x-z plane in the model.
        :param velocity: Determines whether to grid values in units
            of velocity or slowness. Default is to plot velocity.
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes. 
        :param rf: Plot a thin white line for each reflector. Default is
            ``True``.
        :param ir: Plot bold white line for portion of reflector depths
            that are active in the inversion (i.e., ir>0). Default is ``True``.
        :param ij: Plot bold white line for portion of reflector slowness 
            jumps that are active in the inversion (i.e., ij>0). Default is 
            ``True``.
        :param apply_jumps: Determines whether or not to apply slowness jumps
            to the grid before plotting. Default is ``True``.
        :param colorbar: Show a colorbar. Default is ``True``.
        :param vmin, vmax: Used to scale the velocity/slowness grid to 0-1. If
            either is ``None`` (default), the min and max of the grid is
            used.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        # Pull slice from model if not already 2D
        if (x is None) and (y is None):
            vm = self
        else:
            vm = slice_along_xy_line(x=x, y=y, dx=min(self.dx, self.dy))
        # Apply jumps
        if apply_jumps:
            vm.apply_jumps()
        # Plot the slice
        vm._plot2d(velocity=velocity, ax=ax, rf=rf, ir=ir, ij=ij,
                   vmin=vmin, vmax=vmax,
                   colorbar=colorbar, outfile=outfile)
        # remove the jumps
        if apply_jumps:
            vm.remove_jumps()

    def plot_smooth_and_jumped_model(self, x=None, y=None, velocity=True, 
                                     rf=True, ir=True, ij=True, 
                                     apply_jumps=True, outfile=None):
        """
        Plot a comparision of model grids with and without jumps.

        :param x,y: Coordinate values of 2D slice to plot. Default is to plot 
            the first x-z plane in the model.
        :param velocity: Determines whether to grid values in units
            of velocity or slowness. Default is to plot velocity.
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
        self.plot(ax=ax, rf=False, ir=False, ij=False, apply_jumps=False)
        ax.set_title('Smooth Model')
        ax = fig.add_subplot(212)
        self.plot(ax=ax, rf=False, ir=False, ij=False, apply_jumps=True)
        ax.set_title('Jumped Model')
        if outfile:
            fig.savefig(outfile)
        else:
            plt.show()

    def plot_layers(self, x=None, y=None, ax=None, rf=True, ir=False,
             ij=False, apply_jumps=True, outfile=None):
        """
        Plot the model with grid nodes colored by layer id. 

        :param x,y: Coordinate values of 2D slice to plot. Default is to plot 
            the first x-z plane in the model.
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes. 
        :param rf: Plot a thin white line for each reflector. Default is
            ``True``.
        :param ir: Plot bold white line for portion of reflector depths
            that are active in the inversion (i.e., ir>0). Default is ``False``.
        :param ij: Plot bold white line for portion of reflector slowness jumps
            that are active in the inversion (i.e., ij>0). Default is ``False``.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        # Pull slice from model if not already 2D
        if (x is None) and (y is None):
            vm = self
        else:
            vm = slice_along_xy_line(x=x, y=y, dx=min(self.dx, self.dy))
        # Plot the slice
        grid = np.asarray([v[0] for v in self.layers])
        vm._plot2d(velocity=False, ax=ax, rf=rf, ir=ir, ij=ij, grid=grid,
                   outfile=outfile)

    def _plot2d(self, velocity=True, ax=None, rf=True, ir=True, ij=True,
                grid=None, colorbar=True, vmin=None, vmax=None, outfile=None):
        """
        Plot a 2D model.

        :param velocity: Determines whether to grid values in units
            of velocity or slowness. Default is to plot velocity.
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param rf: Plot a thin white line for each reflector. Default is
            ``True``.
        :param ir: Plot bold white line for portion of reflector depths
            that are active in the inversion (i.e., ir>0). Default is ``True``.
        :param ij: Plot bold black line for portion of reflector slowness jumps
            that are active in the inversion (i.e., ij>0). Default is ``True``.
        :param grid: Grid to plot as base plot. Default is to plot slowness or
            velocity from ``self.sl``.
        :param colorbar: Show a colorbar. Default is ``True``.
        :param vmin, vmax: Used to scale the velocity/slowness grid to 0-1. If
            either is ``None`` (default), the min and max of the grid is
            used.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        assert self.ny == 1, "Model must be 2D with ny=1."
        if grid is None:
            grid = np.asarray([d[0] for d in self.sl])
        if velocity:
            grid = 1./grid
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        ax.imshow(grid.transpose(), vmin=vmin, vmax=vmax,
                  extent=(self.r1[0], self.r2[0], self.r2[2], self.r1[2]))
        for iref in range(0, self.nr):
            if rf:
                ax.plot(self.x, self.rf[iref], '-w')
            if ir:
                idx = np.nonzero(self.ir[iref].flatten()>0)
                ax.plot(self.x[idx], self.rf[iref][idx], '-w', linewidth=5)
            if ij:
                idx = np.nonzero(self.ij[iref].flatten()>0)
                ax.plot(self.x[idx], self.rf[iref][idx], '-k', linewidth=3)
        plt.xlim(self.r1[0], self.r2[0])
        plt.ylim(self.r2[2], self.r1[2])
        plt.xlabel('Offset (km)')
        plt.ylabel('Depth (km)')
        if colorbar:
            plt.colorbar()
        if outfile:
            fig.savefig(outfile)
        elif show:
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
                     ax=None, apply_jumps=True):
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
        if False not in [v is None for v in [x,y,z]]:
            x = self.r1[0]
            y = self.r1[1]
            z = None
        if (x is not None) and (y is not None) and (z is None):
            # Plot z vs. v
            ix, = self.x2i([x])
            iy, = self.y2i([y])
            xval = self.sl[ix,iy,:]
            yval = self.z
            ylabel = 'Depth (km)'
            title = 'x = {:}, y = {:} (km)'.format(x,y)
            reverse = True
        elif (x is not None) and (y is None) and (z is not None):
            # Plot v vs. y
            xval = self.y
            ix, = self.x2i([x])
            iz, = self.z2i([z])
            yval = self.sl[ix, :, iz]
            xlabel = 'x-offset (km)'
            title = 'x = {:}, z = {:} (km)'.format(x,z)
            reverse = False
        elif (x is None) and (y is not None) and (z is not None):
            # Plot v vs. x
            xval = self.x
            iy, = self.y2i([x])
            iz, = self.z2i([z])
            yval = self.sl[:, ix, iz]
            xlabel = 'y-offset (km)'
            title = 'y = {:}, z = {:} (km)'.format(y,z)
            reverse = False
        else:
            msg = 'Must specify two of: x, y, z.'
            raise ValueError(msg)
        if velocity:
            if reverse:
                xval = 1./xval
                xlabel = 'Velocity (km/s)'
            else:
                yval = 1./yval
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
        ax.plot(xval, yval)
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
        # XXX depreciated 
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
            ix = int((x - self.r1[0])/dx)
            sl = grid[ix]
            _x = list(np.linspace(self.r1[1],self.r2[1],self.ny))
            x = []; y = []
            for iref in range(0, self.nr):
                x += _x
                x += [None]
                y += [v for v in self.rf[iref][ix]]
                y += [None]
            dims = (1, 2)
            labels = ('y-offset (km)', 'Depth (km)')
        elif (x is None) and (y is not None) and (z is None):
            # Take a slice in the x-z plane
            iy = int((y - self.r1[1])/dy)
            sl = np.asarray([d[iy] for d in grid])
            _x = list(np.linspace(self.r1[0], self.r2[0], self.nx))
            x = []; y = []
            for iref in range(0, self.nr):
                x += _x
                x += [None]
                y += [v[iy] for v in self.rf[iref]]
                y += [None]
            dims = (0, 2)
            labels = ('x-offset (km)', 'Depth (km)')
        elif (x is None) and (y is None) and (z is not None):
            # Take a slice in the x-y plane
            iz = int((z - self.r1[2])/dz)
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

    # Properties
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
        return self.sl.shape[0]
    nx = property(fget=_get_nx)

    def _get_ny(self):
        """
        Returns the number of y-nodes in the model grid.
        """
        return self.sl.shape[1]
    ny = property(fget=_get_ny)

    def _get_nz(self):
        """
        Returns the number of z-nodes in the model grid.
        """
        return self.sl.shape[2]
    nz = property(fget=_get_nz)

    def _get_x(self):
        """
        Returns an array of x-axis coordinates.
        """
        return self.r1[0] + np.asarray(range(0, self.nx))*self.dx
    x = property(fget=_get_x)

    def _get_y(self):
        """
        Returns an array of y-axis coordinates.
        """
        return self.r1[1] + np.asarray(range(0, self.ny))*self.dy
    y = property(fget=_get_y)
    
    def _get_z(self):
        """
        Returns an array of z-axis coordinates.
        """
        return self.r1[2] + np.asarray(range(0, self.nz))*self.dz
    z = property(fget=_get_z)

    def _get_layers(self):
        """
        Returns a grid of layer indices for each node in the slowness grid.
        """
        lyr = np.ones((self.nx, self.ny, self.nz))*self.nr
        for iref in range(0, self.nr):
            # top, bottom boundary depths for current layer
            z0, z1 = self.get_layer_bounds(iref)
            for ix in range(0, self.nx): 
                for iy in range(0, self.ny):
                    iz0, iz1 = self.z2i((z0[ix,iy], z1[ix,iy]))
                    lyr[ix,iy,iz0:iz1] = iref
        return lyr
    layers = property(fget=_get_layers)

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
    vm = VM()
    vm.read(file, endian=endian, head_only=head_only)
    return vm 
