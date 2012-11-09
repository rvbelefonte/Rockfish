"""
Support for working with velocity model files.
"""
import os
import warnings
import numpy as np
from scipy.interpolate import interp1d, interp2d
import datetime
from struct import unpack
import matplotlib.pyplot as plt
from rockfish import __version__
from rockfish.segy.segy import SEGYFile, SEGYTrace
from rockfish.segy.segy import pack
from rockfish.vmtomo.plotting import VMPlotter
from rockfish.vmtomo.vm import VM

ENDIAN = pack.BYTEORDER

class VMFile(VM):
    """
    Class that adds file i/o support to the base VM model class.
    """
    def __init__(self, file=None, endian=ENDIAN, head_only=False):
        """
        Class for working with VM Tomography models.

        :param file: Optional. An open file-like object or a string which is
            assumed to be a filename. Default is to create an empty instance 
            of the VM class.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        :param head_only: Optional. Determines whether or not to read the grid
            data. Useful is only interested in the grid dimension values.
            Default is to read the entire file.
        """
        self.ENDIAN = endian
        if file is not None:
            self.read(file, endian=endian, head_only=head_only)
        else:
            # create empty instance
            self.file = None
            self.init_empty_model()
            
    def __str__(self, extended=False, title=None):
        """
        Print an overview of the VM model.

        :param extended: Optional. Determines whether or not to print detailed
            information about each layer. Default is to print an overview.
        :param title: Optional. Sets the title in the banner. Default is
            the filename.
        """
        if (title is None) and (self.file is not None):
            title = os.path.basename(self.file.name)
        VM.__str__(self, extended=extended, title=title)

    def read(self, file, endian=ENDIAN, head_only=False):
        """
        Read a VM model from a file on the disk or a file-like object.

        :param file: An open file-like object or a string which is
            assumed to be a filename.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        :param head_only: Optional. Determines whether or not to read the grid
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
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        :param head_only: Optional. Determines whether or not to read the grid
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
        fmt = endian + 'f' * ngrid
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

    def write(self, filename, fmt='vm', endian=ENDIAN, **kwargs):
        """
        Write the VM model to a disk file.

        .. note:: This is a convienence function for acessing various write
            functions. These write functions are named ``'write_<fmt>'``; see
            the documentation for these functions for parameter descriptions
            and additional documentation.

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
        # Header information
        for v in [self.nx, self.ny, self.nz, self.nr]:
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
        # TODO
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

class VMFilePlotter(VMFile, VMPlotter):
    """
    Class that adds file i/o and plotting support to the base VM model class.
    
    In general, this is the main class for working with VM models.
    """
    pass
