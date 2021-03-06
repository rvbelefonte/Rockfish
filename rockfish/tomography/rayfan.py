"""
Support for working with VM Tomography binary rayfan files.
"""
import os
import warnings
from struct import unpack
import matplotlib.pyplot as plt
from rockfish.utils.dictlistutil import get_dict_default
from rockfish.io import pack
from rockfish.picking.database import PickDatabaseConnection
import logging
import numpy as np

ENDIAN = pack.BYTEORDER
DEFAULT_RAYFAN_VERSION = 2
DEFAULT_RAYPATH_COLOR = '0.75'
DEFAULT_TRAVELTIME_COLOR = 'k'
DEFAULT_RESIDUAL_COLOR = 'k'

# structure for new tables created by rayfan2db
RAYPATH_TABLE = 'raypaths'
RAYPATH_FIELDS = [#(name, sql_type, default_value, is_not_null, is_primary)
                  ('event', 'TEXT', None, True, True),
                  ('ensemble', 'INTEGER', None, True, True),
                  ('trace', 'INTEGER', None, True, True),
                  ('ray_btm_x', 'REAL', None, False, False),
                  ('ray_btm_y', 'REAL', None, False, False),
                  ('ray_btm_z', 'REAL', None, False, False),
                  ('ray_x', 'TEXT', None, False, False),
                  ('ray_y', 'TEXT', None, False, False),
                  ('ray_z', 'TEXT', None, False, False)]


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

    def plot_raypaths(self, dim=[0, 2], ax=None, receivers=True,
                      sources=True, outfile=None, event_colors={},
                      default_color=DEFAULT_RAYPATH_COLOR):
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
            svg. Default is ``None``.
        :param event_colors: Optional. Dictionary of event names and colors
            to use for plotting raypaths for different events. If
            ``event_colors`` is not given, or if an event ID is not in
            ``event_colors``, raypaths are plotted in the color given by
            ``default_color``.
        :param default_color: Optional. Color to use when plotting raypaths
            for events not in ``event_colors``.  Default is grey.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            reverse = True
            show = True
        else:
            reverse = False
            show = False
        for irfn, rfn in enumerate(self.rayfans):
            for i, path in enumerate(rfn.paths):
                x = [p[dim[0]] for p in path]
                y = [p[dim[1]] for p in path]
                c = get_dict_default(rfn.event_ids[i], event_colors,
                                     default_color)
                ax.plot(x, y, color=c)
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
        elif show:
            plt.show()
        else:
            plt.draw()

    def plot_time_vs_position(self, end='source', dimension='x',
                              traced=True, picked=True,
                              ax=None, outfile=None, event_colors={},
                              default_color=DEFAULT_TRAVELTIME_COLOR):
        """
        Plot traveltimes in each rayfan vs. position.

        :param end: Optional. Specifies which end of the raypath to plot as
            on the abscissa.  Options are: 'source' (default) or 'receiver'.
        :param dimension: Specifies which dimension of the raypath end to plot
            on the abscissa. Options are: 'x' (default), 'y', or 'z'.
        :param ax:  Optional. A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param traced: Optional. Determines whether or not to plot raytraced 
            travel times, if they exist. Default is ``True``.
        :param picked: Optional. Determines whether or not to plot picked
            travel times, if they exist. Default is ``True``.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Default is ``None``.
        :param event_colors: Optional. Dictionary of event names and colors
            to use for plotting traveltimes for different events. If
            ``event_colors`` is not given, or if an event ID is not in
            ``event_colors``, traveltimes are plotted in the color given by
            ``default_color``.
        :param default_color: Optional. Color to use when plotting traveltimes 
            for events not in ``event_colors``.  Default is black.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        end_opts = {'source': 0, 'receiver': -1}
        dim_opts = {'x': 0, 'y': 1, 'z': 2}
        iend = end_opts[end]
        idim = dim_opts[dimension]
        for rfn in self.rayfans:
            x = [p[iend][idim] for p in rfn.paths]
            if picked:
                for i, t in enumerate(rfn.pick_times):
                    c = get_dict_default(rfn.event_ids[i], event_colors,
                                         default_color)
                    ax.errorbar(x[i], t, yerr=rfn.pick_errors[i], fmt=c + '.',
                                markersize=0, capsize=0)
            if traced:
                for i, t in enumerate(rfn.travel_times):
                    c = get_dict_default(rfn.event_ids[i], event_colors,
                                         default_color)
                    ax.scatter(x[i], t, marker='.', color=c, s=1, linewidths=0)
        plt.xlabel('{:} {:} (km)'.format(end, dimension))
        plt.ylabel('t (s)')
        if outfile:
            fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            plt.draw()

    def plot_residual_vs_position(self, end='source', dimension='x',
                                  ax=None, outfile=None, event_colors={},
                              default_color=DEFAULT_RESIDUAL_COLOR):
        """
        Plot residuals in each rayfan vs. position.

        :param end: Specifies which end of the raypath to plot on the
            abscissa.  Options are: 'source' (default) or 'receiver'.
        :param dimension: Specifies which dimension of the raypath end to plot
            on the abscissa. Options are: 'x' (default), 'y', or 'z'.
        :param ax:  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create a new figure and axes.
        :param outfile: Output file string. Also used to automatically
            determine the output format. Supported file formats depend on your
            matplotlib backend. Most backends support png, pdf, ps, eps and
            svg. Default is ``None``.
        :param event_colors: Optional. Dictionary of event names and colors
            to use for plotting residuals for different events. If
            ``event_colors`` is not given, or if an event ID is not in
            ``event_colors``, residuals are plotted in the color given by
            ``default_color``.
        :param default_color: Optional. Color to use when plotting residuals 
            for events not in ``event_colors``.  Default is black.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        end_opts = {'source': 0, 'receiver': -1}
        dim_opts = {'x': 0, 'y': 1, 'z': 2}
        iend = end_opts[end]
        idim = dim_opts[dimension]
        for rfn in self.rayfans:
            x = [p[iend][idim] for p in rfn.paths]
            for i, e in enumerate(rfn.residuals):
                c = get_dict_default(rfn.event_ids[i], event_colors, 
                                     default_color)
                ax.scatter(x[i], e, marker='.', color=c, s=5, linewidths=0)
        plt.xlabel('{:} {:} (km)'.format(end, dimension))
        plt.ylabel('Error (s)')
        if outfile:
            fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            plt.draw()


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
            show = True
        else:
            show = False
        for rfn in self.rayfans:
            ax.scatter(rfn.azimuths, rfn.residuals, c=rfn.offsets,
                       cmap='hsv', s=markersize, edgecolor=None)
        plt.xlabel('Azimuth (degrees)')
        plt.ylabel('Delay Time (s)')
        plt.xlim(0, 360)
        if outfile:
            fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            plt.draw()

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
            show = True
        else:
            show = False
        for rfn in self.rayfans:
            #ax.plot(rfn.azimuths, rfn.residuals, '.k', markersize=2)
            ax.scatter(rfn.offsets, rfn.residuals, c=rfn.azimuths,
                       cmap='hsv', s=markersize, edgecolor=None)
        plt.xlabel('Offset (km)')
        plt.ylabel('Delay Time (s)')
        plt.xlim(0, 360)
        if outfile:
            fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            plt.draw()

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

    def _get_all_bottom_points(self):
        """
        Returns a list of all ray bottom points.
        """
        return np.concatenate([rfn.bottom_points for rfn in self.rayfans])
    bottom_points = property(fget=_get_all_bottom_points)

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
        data_needed = 7 * self.nrays + 3 * nsize
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
        fmt = '{:}'.format(endian) + 'i' * self.nrays
        self.end_point_ids = unpack(fmt, file.read(4 * self.nrays))
        self.event_ids = unpack(fmt, file.read(4 * self.nrays))
        self.event_subids = unpack(fmt, file.read(4 * self.nrays))
        lens = unpack(fmt, file.read(4 * self.nrays))  # raypath length
        # Picks, travel-times, and errors
        fmt = '{:}'.format(endian) + 'f' * self.nrays
        self.pick_times = unpack(fmt, file.read(4 * self.nrays))
        self.travel_times = unpack(fmt, file.read(4 * self.nrays))
        self.pick_errors = unpack(fmt, file.read(4 * self.nrays))
        # Actual ray path coordinates
        self.paths = []
        for i in range(0, self.nrays):
            fmt = '{:}'.format(endian) + 'f' * 3 * lens[i]
            self.paths.append(np.reshape(
                unpack(fmt, file.read(4 * 3 * lens[i])),
                (lens[i], 3)))
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
            x[i] = np.sqrt(deltx ** 2 + delty ** 2)
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
            if az[i] < 0:
                az[i] += 360.
        return az
    azimuths = property(fget=_calc_azimuths)

    def _calc_residuals(self):
        """
        Calculate residuals.
        """
        return np.asarray(self.travel_times) - np.asarray(self.pick_times) \
            + self.static_correction
    residuals = property(fget=_calc_residuals)

    def _calc_rms(self):
        """
        Calculate the RMS of travel-time residuals.
        """
        return np.sqrt(np.sum(self.residuals ** 2) / self.nrays)
    rms = property(fget=_calc_rms)

    def _calc_chi2(self):
        """
        Calculate the Chi-squared value.
        """
        return (self.residuals / self.pick_errors) ** 2
    chi2 = property(fget=_calc_chi2)

    def _calc_mean_chi2(self):
        """
        Calculate the mean Chi-squared value.
        """
        return np.sum(self.chi2) / self.nrays
    chi2_mean = property(fget=_calc_mean_chi2)

    def _get_ray_bottom_points(self):
        """
        Find the bottoming point for each raypath.
        """
        pts = np.zeros((self.nrays, 3))
        for i, path in enumerate(self.paths):
            pts[i] = path[np.argmax([p[2] for p in path])]
        return pts
    bottom_points = property(fget=_get_ray_bottom_points)


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


def rayfan2db(rayfan_file, raydb_file=':memory:', synthetic=False, noise=None,
              pickdb=None, raypaths=False):
    """
    Read a rayfan file and store its data in a database.

    Data are stored in a modified version of a
    :class:`rockfish.picking.database.PickDatabaseConnection`.

    Parameters
    ----------
    rayfan_file: {str, file}
        An open file-like object or a string which is assumed to be a
        filename of a rayfan binary file.
    raydb_file: str, optional
        The filename of the new database. Default is to create
        a new database in memory.
    synthetic: bool, optional
        Determines whether or not to record traced traveltimes as picked 
        traveltimes.
    noise: {float, None}
        Maximum amplitude of random noise to add the travel times.  If
        ``None``, no noise is added.
    pickdb: :class:`rockfish.database.PickDatabaseConnection`, optional
        An active connection to the pick database that was used
        trace rays in ``rayfan_file``. Values for extra fields (e.g., 
        'trace_in_file') are copied from this database to the new
        database along with rayfan data. Default is ignore these extra fields.
    raypaths: bool, optional
        If ``True``, raypath coordinates are stored as text in a new table
        'raypaths'.
    """
    raydb = PickDatabaseConnection(raydb_file)
    rays = readRayfanGroup(rayfan_file)
    print "Adding {:} traveltimes to {:} ..."\
            .format(rays.nrays, raydb_file)
    # add fields for raypaths
    if raypaths:
        raydb._create_table_if_not_exists(RAYPATH_TABLE, RAYPATH_FIELDS)
    ndb0 = raydb.execute('SELECT COUNT(rowid) FROM picks').fetchone()[0]
    for rfn in rays.rayfans:
        for i, _t in enumerate(rfn.travel_times):
            if noise is not None:
                _noise = noise * 2 * (np.random.random() - 0.5)
            else:
                _noise = 0.0
            sx, sy, sz = rfn.paths[i][0]
            rx, ry, rz = rfn.paths[i][-1]
            if pickdb is not None:
                event = pickdb.vmbranch2event[rfn.event_ids[i]]
            else:
                event = rfn.event_ids[i]
            if synthetic:
                time = rfn.travel_times[i] + _noise
                time_reduced = time
                predicted = None
                residual = 0.
            else:
                time = rfn.pick_times[i]
                time_reduced = time
                predicted = rfn.travel_times[i]
                residual = rfn.residuals[i] 
            d = {'event': event,
                 'ensemble': rfn.start_point_id,
                 'trace': rfn.end_point_ids[i],
                 'vm_branch': rfn.event_ids[i],
                 'vm_subid': rfn.event_subids[i],
                 'time' : time,
                 'time_reduced' : time_reduced,
                 'predicted' : predicted,
                 'residual' : residual,
                 'error': rfn.pick_errors[i],
                 'source_x': sx, 'source_y': sy, 'source_z': sz,
                 'receiver_x': rx, 'receiver_y': ry, 'receiver_z': rz,
                 'offset': rfn.offsets[i],
                 'faz': rfn.azimuths[i],
                 'method': 'rayfan2db({:})'.format(rayfan_file),
                 'data_file': rays.file.name}
            # Copy data from pickdb
            if pickdb is not None:
                pick = pickdb.get_picks(event=[event],
                                        ensemble=[d['ensemble']],
                                        trace=[d['trace']])
                if len(pick) > 0:
                    for f in ['trace_in_file', 'line', 'site', 'data_file']:
                        try:
                            d[f] = pick[0][f]
                        except KeyError:
                            pass
            # add data to standard tables
            raydb.update_pick(**d)
            # add raypath data to new table
            if raypaths:
                d = {'event': event,
                     'ensemble': rfn.start_point_id,
                     'trace': rfn.end_point_ids[i],
                     'ray_btm_x': rays.bottom_points[i][0],
                     'ray_btm_y': rays.bottom_points[i][1],
                     'ray_btm_z': rays.bottom_points[i][2],
                     'ray_x': str([p[0] for p in rfn.paths[i]]),
                     'ray_y': str([p[1] for p in rfn.paths[i]]),
                     'ray_z': str([p[2] for p in rfn.paths[i]])}
                raydb._insert(RAYPATH_TABLE, **d)

        raydb.commit()
    ndb = raydb.execute('SELECT COUNT(rowid) FROM picks').fetchone()[0]
    if (ndb - ndb0) != rays.nrays:
        msg = 'Only added {:} of {:} travel times to the database.'\
                .format(ndb - ndb0, rays.nrays)
        warnings.warn(msg)
    return raydb
