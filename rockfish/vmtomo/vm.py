"""
Routines for working with VM Tomography models.
"""
import os
import numpy as np
from scipy.interpolate import interp1d
import datetime
from struct import unpack
import matplotlib.pyplot as plt
from rockfish import __version__
from rockfish.segy.segy import SEGYFile, SEGYTrace
from rockfish.segy.segy import pack

ENDIAN = pack.BYTEORDER

class VM(object):
    """
    Class for working with VM Tomography models.
    """
    def __init__(self, file=None, endian=ENDIAN, unpack_arrays=True,
                 head_only=False):
        """
        Class for working with VM Tomography models.

        :param file: Optional. An open file-like object or a string which is
            assumed to be a filename. Default is to create an empty instance 
            of the VM class.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        :param unpack_arrays: Optional. Determines whether or not to rearrange
            1D arrays of grid and interface values into 3D matrixes (stacked
            arrays). Default is True.
        :param head_only: Optional. Determines whether or not to read the grid
            data. Useful is only interested in the grid dimension values.
            Default is to read the entire file.
        """
        self.ENDIAN = endian
        if file is not None:
            self.read(file, endian=endian, unpack_arrays=unpack_arrays,
                      head_only=head_only)
        else:
            # create empty instance
            self.file = None
            self.nx = None
            self.ny = None
            self.nz = None
            self.r1 = (None, None, None)
            self.r2 = (None, None, None)
            self.dx = None
            self.dy = None
            self.dz = None
            self.sl = []
            self.rf = []
            self.jp = []
            self.ir = []
            self.ij = []

    def read(self, file, endian=ENDIAN, unpack_arrays=True, head_only=False):
        """
        Read a VM model from a file on the disk or a file-like object.

        :param file: An open file-like object or a string which is
            assumed to be a filename.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        :param unpack_arrays: Optional. Determines whether or not to rearrange
            1D arrays of grid and interface values into 3D matrixes (stacked
            arrays). Default is True.
        :param head_only: Optional. Determines whether or not to read the grid
            data. Useful is only interested in the grid dimension values.
            Default is to read the entire file.
        """
        if not hasattr(file, 'read') or not hasattr(file, 'tell') or not \
            hasattr(file, 'seek'):
            file = open(file, 'rb')
        else:
            file.seek(0)
        self._read(file, endian=endian, unpack_arrays=unpack_arrays,
                   head_only=head_only)
        self.file = file
        self.file.close()

    def _read(self, file, endian=ENDIAN, unpack_arrays=True, head_only=False):
        """
        Read a VM model from a file-like object.

        :param file: A file-like object with the file pointer set at the
            beginning of a VM binary file.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        :param unpack_arrays: Optional. Determines whether or not to rearrange
            1D arrays of grid and interface values into 3D matrixes (stacked
            arrays). Default is True.
        :param head_only: Optional. Determines whether or not to read the grid
            data. Useful is only interested in the grid dimension values.
            Default is to read the entire file.
        """
        # Header information
        fmt = '{:}iiii'.format(endian)
        self.nx, self.ny, self.nz, self.nr = unpack(fmt, file.read(4*4))
        fmt = '{:}fff'.format(endian)
        self.r1 = unpack(fmt, file.read(4*3))
        self.r2 = unpack(fmt, file.read(4*3))
        fmt = '{:}fff'.format(endian)
        self.dx, self.dy, self.dz = unpack(fmt, file.read(4*3))
        if head_only is True:
            self.sl = []
            self.rf = []
            self.jp = []
            self.ir = []
            self.ij = []
            return
        # Slowness grid
        ngrid = self.nx*self.ny*self.nz
        fmt = endian + 'f' * ngrid
        self.sl = np.asarray(unpack(fmt, file.read(4*ngrid)))
        # Interface depths and slowness jumps
        nintf = self.nx*self.ny*self.nr
        fmt = endian + 'f' * nintf
        self.rf = unpack(fmt, file.read(4*nintf))
        self.jp = unpack(fmt, file.read(4*nintf))
        # Interface flags
        fmt = endian + 'i' * nintf
        self.ir = unpack(fmt, file.read(4*nintf))
        self.ij = unpack(fmt, file.read(4*nintf))
        # Rearrage 1D arrays into 3D matrixes
        if unpack_arrays is True:
            self._unpack_arrays()

    def _unpack_arrays(self):
        """
        Rearrange the 1D model arrays into 3D matrices (stacked arrays)
        """
        self.sl = np.reshape(self.sl, (self.nx, self.ny, self.nz))
        rf = []
        jp = []
        ir = []
        ij = []
        for iref in range(0, self.nr):
            i0 = iref*(self.nx * self.ny)
            i1 = i0 + (self.nx * self.ny)
            rf.append(np.reshape(self.rf[i0:i1], (self.nx, self.ny)))
            jp.append(np.reshape(self.jp[i0:i1], (self.nx, self.ny)))
            ir.append(np.reshape(self.ir[i0:i1], (self.nx, self.ny)))
            ij.append(np.reshape(self.ij[i0:i1], (self.nx, self.ny)))
        self.rf = np.asarray(rf)
        self.jp = np.asarray(jp)
        self.ir = np.asarray(ir)
        self.ij = np.asarray(ij)

    def _pack_arrays(self):
        """
        Rearrange the 3D model matrices into 1D arrays.
        """
        self.sl = np.reshape(self.sl, (self.nx*self.ny*self.nz))
        self.rf = np.reshape(self.rf, (self.nx*self.ny*self.nr))
        self.jp = np.reshape(self.jp, (self.nx*self.ny*self.nr))
        self.ir = np.reshape(self.ir, (self.nx*self.ny*self.nr))
        self.ij = np.reshape(self.ij, (self.nx*self.ny*self.nr))

    def _gridpoint2index(self, ix, iy, iz):
        """
        Convert a 3-component slowness grid indices to a single index in the 1D
        packed slowness array.

        :param ix: x-coordinate index
        :param iy: y-coordinate index
        :param iz: z-coordinate index
        """
        return ix*self.ny*self.nz + iy*self.nz + iz

    def _interfacepoint2index(self, ix, iy, ir):
        """
        Convert a 3-component interface indices to a single index in the 1D
        packed interface arrays.

        :param ix: x-coordinate index
        :param iy: y-coordinate index
        :param ir: interface index
        """
        return ir*self.nx + ix*self.ny + iy

    def write(self, filename, fmt='vm', endian=ENDIAN, **kwargs):
        """
        Write the VM model to a disk file.

        .. note:: This is a conveince function for acessing various write
            functions. These write functions are named ``'write_<fmt>'``; see
            the documentation for these functions for parameter descriptions and
            additional documentation.

        :param filename: Name of a file to write data to.
        :param fmt: Optional.  Format to write data in. Default is the native
            VM Tomography binary format (``format='vm'``). Other options are
            ``'ascii_grid'``. See documentation for functions labeled
        :param endian: Optional. The endianness of the file for binary formats.
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
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        """
        f = open(filename, 'w')
        self._pack_arrays()
        # Header information
        for v in [self.nx, self.ny, self.nz, self.nr]:
            pack.pack_4byte_Integer(f, np.int32(v), endian)
        for v in self.r1 + self.r2 + (self.dx, self.dy, self.dz):
            pack.pack_4byte_IEEE(f, np.float32(v), endian)
        # Slowness grid
        pack.pack_4byte_IEEE(f, np.float32(self.sl), endian)
        # Interface depths and slowness jumps
        for v in [self.rf, self.jp]:
            pack.pack_4byte_IEEE(f, np.float32(v), endian)
        # Interface flags
        for v in [self.ir, self.ij]:
            pack.pack_4byte_Integer(f, np.int32(v), endian)
        f.close()

    def write_ascii_grid(self, filename, meters=False, velocity=False):
        """
        Write VM model slowness grid in an ASCII format.

        :param filename: Name of a file to write data to.
        :param meters: Optional. Output distance units in meters. Default is
            kilometers.
        :param velocity: Optional. Output slowness values as velocity. Default
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

        :param endian: Optional. The endianness of the file. Default is big
            endian (the SEG-Y standard).
        :param velocity: Optional. Output slowness values as velocity. Default
            is slowness.
        :param meters: Optional. Output distance units in meters. Default is
            kilometers.
        """
        # Copy data to SEGYFile instance
        raise NotImplementedError

    def vm2segy(self, endian='>', meters=False, velocity=False):
        """
        Convert VM slowness grid to a SEGYFile instance.

        :param endian: Optional. The endianness of the file. Default is big
            endian (the SEG-Y standard).
        :param velocity: Optional. Output slowness values as velocity. Default
            is slowness.
        :param meters: Optional. Output distance units in meters. Default is
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

    def plot(self, x=None, y=None, z=None, velocity=True):
        """
        Plot a slice from a VM slowness model.
        
        :param x,y,z: Optional. Coordinate value of slice to plot. Give one of
            the three. Default is to plot the first x-z plane (y=ymin) in the
            model.
        :param velocity: Optional. Determines whether to grid values in units
            of velocity or slowness. Default is to plot velocity.
        """
        # Determine slice coordinates
        if False not in [v is None for v in [x,y,z]]:
            # Plot the 1st x-z plane
            y = self.r1[1]
        # Extract grid slice to plot
        sl, bounds, _extents, labels = self._slice_for_plot(
            x=x, y=y, z=z)
        extents = (_extents[0], _extents[1], _extents[3], _extents[2])
        if velocity is True:
            sl = 1./sl
        # Plot figure
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.imshow(sl.transpose(), extent=extents)
        print len(bounds[0]), len(bounds[1])
        ax.plot(bounds[0], bounds[1], '-k')
        plt.xlabel(labels[0])
        plt.ylabel(labels[1])
        plt.xlim(self.r1[0], self.r2[0])
        # Show (TODO save, draw) plot
        plt.show()

    def _slice_for_plot(self, x=None, y=None, z=None):
        """
        Extract a slice from the 3D VM model slowness grid for plotting.
        
        :param x,y,z: Coordinate value of orthogonal slice to extract. Give
            one of the three.  
        :param plot_info: Optional. If True, also returns plot extents and axis
            labels. Default is False.
        :returns sl: Slice as a 2D stack of numpy arrays.
        :returns bounds: Interface depths
        :returns extents: Extents of the 2D slice as a tuple.
        :returns labels: Slice axis labels returned as a tuple.
        """
        # Extract the grid slice
        if (x is not None) and (y is None) and (z is None):
            # Take a slice in the y-z plane
            ix = int((x - self.r1[0])/self.dx)
            sl = self.sl[ix]
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
            iy = int((y - self.r1[1])/self.dy)
            sl = np.asarray([d[iy] for d in self.sl])
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
            iz = int((z - self.r1[2])/self.dz)
            sl = self.sl.transpose()[iz]
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

    def slice_along_xy_line(self, x, y, dx=None, nx=None):
        """
        Extract a vertical slice along a line.

        :param x,y: Lists of coordinates to take slice along.
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

    def _x2i(self, x):
        """
        Find an x index for an x coordinate.

        :param x: x coordinate in the model 
        :returns: nearest x index for the given coordinate
        """
        return int((x-self.r1[0])/self.dx)

    def _y2i(self, y):
        """
        Find a y index for a y coordinate.

        :param y: y coordinate in the model 
        :returns: nearest y index for the given coordinate
        """
        return int((y-self.r1[1])/self.dy)

    def _z2i(self, z):
        """
        Find a z index for a z coordinate.

        :param z: z coordinate in the model 
        :returns: nearest z index for the given coordinate
        """
        return int((z-self.r1[2])/self.dz)

    def __str__(self):
        """
        Print an overview of the VM model.
        """
        if self.file is None:
            banner = self._pad_line('VM Model', char='=')
        else:
            banner = self._pad_line(os.path.basename(self.file.name),
                                    char='=')
        sng = banner + '\n'
        sng += self._print_header()
        sng += banner
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

    def _pad_line(self, msg, char=' ', width=78):
        """
        Center a string in a fixed-width line.

        :param char: Optional. Character to fill the pad with. Default is 
            ``' '``.
        :param width: Optional.  Width of the line. Default is 78.
        """
        npad = (width - len(msg))/2
        return char*npad + msg + char*npad



