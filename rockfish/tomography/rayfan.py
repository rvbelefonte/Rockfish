"""
Support for working with VM Tomography binary rayfan files.
"""
import os
import warnings
from struct import unpack
import matplotlib.pyplot as plt
from rockfish.segy.segy import pack
from rockfish.picking.database import PickDatabaseConnection
import logging
import numpy as np

ENDIAN = pack.BYTEORDER
DEFAULT_RAYFAN_VERSION = 2

class RayfanError(Exception):
    """
    Base exception class for the Rayfan class. 
    """
    pass

class RayfanReadingError(RayfanError):
    """
    Raised if there is a problem reading a rayfan from the disk.
    """
    pass

class RayfanNotFoundError(RayfanError):
    """
    Raised if a rayfan is not found in the ray file.
    """
    pass

class RayfanGroup(object):
    """
    Class for working with VM Tomography rayfan files.
    """
    def __init__(self, endian='@'):
        """
        Class for working with VM Tomography rayfan files.

        :param file: An open file-like object or a string which is
            assumed to be a filename.
        :param endian: Optional. The endianness of the file. 
            Default is to use machine's native byte order.
        """
        self.file = None
        self.rayfans = []

    def __str__(self):
        """
        Print a summary of the rayfan.
        """
        sng = '{:}:'.format(os.path.basename(self.file.name))
        sng += ' nrayfans = {:},'.format(len(self.rayfans))
        sng += ' Chi^2 = {:}, rms = {:}'.format(self.chi2, self.rms)
        return sng

    def read(self, file, endian='@'):
        """
        Read rayfan data from a rayfan file.

        :param file: An open file-like object or a string which is
            assumed to be a filename.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        """
        if not hasattr(file, 'read') or not hasattr(file, 'tell') or not \
            hasattr(file, 'seek'):
            file = open(file, 'rb')
        else:
            file.seek(0)
        self.file = file
        self._read(file, endian=endian)

    def _read(self, file, endian='@'):
        """
        Read rayfan data from a rayfan file.

        :param file: An open file-like object with the file pointer set at the
            beginning of a rayfan file. 
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        """
        # Read file header
        fmt = '{:}i'.format(endian)
        n = unpack(fmt, file.read(4))[0]
        if n < 0:
            self.FORMAT = -n
            n = unpack(fmt, file.read(4))[0]
        else:
            self.FORMAT = 1
        # Read the individual rayfans
        self.rayfans = []
        for i in range(0, n):
            self.rayfans.append(Rayfan(file, endian=endian,
                                       rayfan_version=self.FORMAT))

    def plot_raypaths(self, dim=[0,2], ax=None, receivers=True, 
                      sources=True, outfile=None):
        """
        Plot all raypaths.

        :param dim: Coordinate dimensions to plot paths into. Default is z 
            vs. x (``dim=[0,2]``).
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param receivers: Determines whether or not to plot symbols at
            the receiver locations. Default is ``True``.
        :param sources: Determines whether or not to plot symbols at
            the source locations. Default is ``False``.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Defaults is ``None``.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            reverse = True
            show = True
        else:
            reverse = False
            show = False
        for rfn in self.rayfans:
            for i, path in enumerate(rfn.paths):
                x = [p[dim[0]] for p in path]
                y = [p[dim[1]] for p in path]
                ax.plot(x, y, color='0.75')
                if receivers:
                    x = rfn.paths[i][-1][dim[0]]
                    y = rfn.paths[i][-1][dim[1]]
                    ax.plot(x, y, 'vy')
                if sources:
                    x = rfn.endpoints[i][dim[0]]
                    y = rfn.endpoints[i][dim[1]]
                    ax.plot(x, y, '*r')
        if reverse:
            ax.set_ylim(ax.get_ylim()[::-1])
        if outfile:
            fig.savefig(outfile)
        else:
            plt.show()

    def plot_time_vs_position(self, end='source', dimension='x',
                              traced=True, predicted=True,
                              ax=None, outfile=None):
        """
        Plot traveltimes in the rayfan vs. position.

        :param end: Specifies which end of the raypath to plot as on the
            abscissa.  Options are: 'source' (default) or 'receiver'.
        :param dimension: Specifies which dimension of the raypath end to plot
            on the abscissa. Options are: 'x' (default), 'y', or 'z'.
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Default is ``None``.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
        end_opts = {'source':0, 'receiver':-1}
        dim_opts = {'x':0, 'y':1, 'z':2}
        iend = end_opts[end]
        idim = dim_opts[dimension]
        for rfn in self.rayfans:
            x = [p[iend][idim] for p in rfn.paths]
            # pick times
            ax.errorbar(x, rfn.pick_times, yerr=rfn.pick_errors,
                        fmt='r.', markersize=0, capsize=0)
            # calculated times
            ax.plot(x, rfn.travel_times, '.k', markersize=5)
        plt.xlabel('{:} {:} (km)'.format(end, dimension))
        plt.ylabel('t (s)')
        if outfile:
            fig.savefig(outfile)
        else:
            plt.show()

    def plot_residuals_vs_azimuth(self, ax=None, outfile=None, markersize=2):
        """
        Plot residuals vs. source-receiver azimuth.
        
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Default is ``None``.
        :param markersize: Sets :class:`matplotlib.lines.Line2D` markersize
            propertry. Default is 2.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
        for rfn in self.rayfans:
            ax.scatter(rfn.azimuths, rfn.residuals, c=rfn.offsets,
                       cmap='hsv', s=markersize, edgecolor=None)
        plt.xlabel('Azimuth (degrees)')
        plt.ylabel('Delay Time (s)')
        plt.xlim(0, 360)
        if outfile:
            fig.savefig(outfile)
        else:
            plt.show()

    def plot_residuals_vs_offset(self, ax=None, outfile=None, markersize=2):
        """
        Plot residuals vs. source-receiver offset.
        
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Default is ``None``.
        :param markersize: Sets :class:`matplotlib.lines.Line2D` markersize
            propertry. Default is 2.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
        for rfn in self.rayfans:
            #ax.plot(rfn.azimuths, rfn.residuals, '.k', markersize=2)
            ax.scatter(rfn.offsets, rfn.residuals, c=rfn.azimuths,
                       cmap='hsv', s=markersize, edgecolor=None)
        plt.xlabel('Offset (km)')
        plt.ylabel('Delay Time (s)')
        plt.xlim(0, 360)
        if outfile:
            fig.savefig(outfile)
        else:
            plt.show()

    def _get_all_azimuths(self):
        """
        Returns a list of all azimuths in the rayfans.
        """
        return np.concatenate([rfn.azimuths for rfn in self.rayfans])
    azimuths = property(fget=_get_all_azimuths)
    
    def _get_all_offsets(self):
        """
        Returns a list of all azimuths in the rayfans.
        """
        return np.concatenate([rfn.offsets for rfn in self.rayfans])
    offsets = property(fget=_get_all_offsets)

    def _get_all_residuals(self):
        """
        Returns a list of all residuals in the rayfans.
        """
        return np.concatenate([rfn.residuals for rfn in self.rayfans])
    residuals = property(fget=_get_all_residuals)

    def _get_nrays(self):
        """
        Returns the total number of rays in all rayfans.
        """
        return len(self._get_all_offsets())
    nrays = property(fget=_get_nrays)

    def _calc_mean_rms(self):
        """
        Calculate mean RMS of all rayfans.
        """
        return np.mean([rfn.rms for rfn in self.rayfans])
    rms = property(fget=_calc_mean_rms)

    def _calc_mean_chi2(self):
        """
        Calculate mean Chi-squared value for all rayfans.
        """
        return np.mean([rfn.chi2_mean for rfn in self.rayfans])
    chi2 = property(fget=_calc_mean_chi2)

class Rayfan(object):
    """
    Class for working with a single rayfan.
    """
    def __init__(self, file, endian='@', 
                 rayfan_version=DEFAULT_RAYFAN_VERSION):
        """
        Class for handling an individual rayfan.

        :param file: An open file-like object with the file pointer set at the
            beginning of a rayfan file. 
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        :param rayfan_version: Optional. Sets the version number of the
            rayfan file format. Default is version 2.
        """
        self.read(file, endian=endian, rayfan_version=rayfan_version)

    def read(self, file, endian='@', rayfan_version=DEFAULT_RAYFAN_VERSION):
        """
        Read data for a single rayfan.

        :param file: An open file-like object with the file pointer set at the
            beginning of a rayfan file. 
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        :param rayfan_version: Optional. Sets the version number of the
            rayfan file format. Default is version 2.
        """
        filesize = os.fstat(file.fileno()).st_size
        # read the rayfan header information
        fmt = '{:}i'.format(endian)
        self.start_point_id = unpack(fmt, file.read(4))[0]
        self.nrays = unpack(fmt, file.read(4))[0]
        nsize = unpack(fmt, file.read(4))[0]
        # make sure the expected amount of data exist
        pos = file.tell()
        data_left = filesize - pos
        data_needed = 7*self.nrays + 3*nsize
        if data_needed > data_left or data_needed < 0:
            msg = '''
                  Too little data in the file left to unpack. This is most
                  likely caused by an incorrect size in the rayfan header.
                  '''.strip()
            raise RayfanReadingError(msg)
        # Static correction
        if rayfan_version > 1:
            fmt = '{:}f'.format(endian)
            self.static_correction = unpack(fmt, file.read(4))[0]
        else:
            self.static_correction = 0.
        # ID arrays and sizes
        fmt = '{:}'.format(endian) + 'i'*self.nrays
        self.end_point_ids = unpack(fmt, file.read(4*self.nrays))
        self.event_ids = unpack(fmt, file.read(4*self.nrays))
        self.event_subids = unpack(fmt, file.read(4*self.nrays))
        lens = unpack(fmt, file.read(4*self.nrays)) # raypath length
        # Picks, travel-times, and errors
        fmt = '{:}'.format(endian) + 'f'*self.nrays
        self.pick_times = unpack(fmt, file.read(4*self.nrays))
        self.travel_times = unpack(fmt, file.read(4*self.nrays))
        self.pick_errors = unpack(fmt, file.read(4*self.nrays))
        # Actual ray path coordinates
        self.paths = [] 
        for i in range(0, self.nrays):
            fmt = '{:}'.format(endian) + 'f'*3*lens[i]
            self.paths.append(np.reshape(
                unpack(fmt,file.read(4*3*lens[i])),
                (lens[i],3)))
        # Endpoint coordinates
        self.endpoints = []
        for path in self.paths:
            if len(path) > 0:
                self.endpoints.append(path[0])
            else:
                self.endpoints.append([None, None, None])

    def _calc_offsets(self):
        """
        Calculate source-reciever offset for each path.
        """
        x = np.zeros(len(self.paths))
        for i, path in enumerate(self.paths):
            deltx = path[-1][0] - path[0][0] 
            delty = path[-1][1] - path[0][1]
            x[i] = np.sqrt(deltx**2 + delty**2)
        return x
    offsets = property(fget=_calc_offsets)

    def _calc_azimuths(self):
        """
        Calculate source-receiver azimuth for each path.
        """
        az = np.zeros(len(self.paths))
        for i, path in enumerate(self.paths):
            deltx = path[-1][0] - path[0][0] 
            delty = path[-1][1] - path[0][1] 
            az[i] = (90 - np.rad2deg(np.arctan2(delty, deltx)))
            if az[i] < 0: az[i] += 360.
        return az
    azimuths = property(fget=_calc_azimuths)

    def _calc_residuals(self):
        """
        Calculate residuals.
        """
        return np.asarray(self.pick_times) - np.asarray(self.travel_times) \
            + self.static_correction
    residuals = property(fget=_calc_residuals)

    def _calc_rms(self):
        """
        Calculate the RMS of travel-time residuals.
        """
        return np.sqrt(np.sum(self.residuals**2)/self.nrays)
    rms = property(fget=_calc_rms)

    def _calc_chi2(self):
        """
        Calculate the Chi-squared value.
        """
        return (self.residuals/self.pick_errors)**2
    chi2 = property(fget=_calc_chi2)

    def _calc_mean_chi2(self):
        """
        Calculate the mean Chi-squared value.
        """
        return np.sum(self.chi2)/self.nrays
    chi2_mean = property(fget=_calc_mean_chi2)

def readRayfanGroup(file, endian=ENDIAN):
    """
    Read a VM tomography rayfan file.

    :param file: An open file-like object or a string which is
        assumed to be a filename.
    :param endian: Optional. The endianness of the file. Default is
        to use machine's native byte order. 
    """
    rfn = RayfanGroup()
    rfn.read(file, endian=endian)
    return rfn

def rayfan2pickdb(rayfan_file, pickdb_file, noise=None):
    """
    Read a rayfan file and store its data in a
    :class:`rockfish.picking.database.PickDatabaseConnection`.

    :param rayfan_file: An open file-like object or a string which is
        assumed to be a filename of a rayfan binary file.
    :param pickdb_file: The filename of the pick database.
    :param noise: Maximum amplitude of random noise to add the travel times. 
        Default is to not add any noise.
    """
    pickdb = PickDatabaseConnection(pickdb_file)
    rays = readRayfanGroup(rayfan_file)
    print "Adding {:} traveltimes to {:} ..."\
            .format(rays.nrays, pickdb_file)
    ndb0 = pickdb.execute('SELECT COUNT(rowid) FROM picks').fetchone()[0]
    for rfn in rays.rayfans: 
        for i,_t in enumerate(rfn.travel_times):
            if noise is not None:
                _noise = noise*2*(np.random.random() - 0.5)
            else:
                _noise = 0.0
            sx = rfn.paths[i][0][0]
            sy = rfn.paths[i][0][1]
            rx = rfn.endpoints[i][0]
            ry = rfn.endpoints[i][1]
            d = {'event':rfn.event_ids[i],
                 'ensemble':rfn.start_point_id,
                 'vm_branch':rfn.event_ids[i],
                 'vm_subid':rfn.event_subids[i],
                 'trace':rfn.end_point_ids[i],
                 'time':rfn.pick_times[i] + _noise,
                 'time_reduced':rfn.pick_times[i] + _noise,
                 'predicted':rfn.travel_times[i],
                 'residual':rfn.residuals[i],
                 'error':rfn.pick_errors[i],
                 'source_x':sx, 'source_y':sy,
                 'source_z':rfn.paths[i][0][2],
                 'receiver_x':rx, 'receiver_y':ry,
                 'receiver_z':rfn.endpoints[i][2],
                 'offset':rfn.offsets[i],
                 'faz':rfn.azimuths[i],
                 'method':'rayfan2pickdb({:}, {:}, noise={:})'\
                            .format(rayfan_file, pickdb_file, noise),
                 'data_file':rays.file.name}
            pickdb.update_pick(**d)
        pickdb.commit()
    ndb = pickdb.execute('SELECT COUNT(rowid) FROM picks').fetchone()[0]
    if (ndb - ndb0) != rays.nrays:
        msg = 'Only added {:} of {:} travel times to the database.'\
                .format(ntimes, ndb - ndb0)
        warnings.warn(msg)
    return pickdb

