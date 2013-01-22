"""
Managers for plotting classes
"""

from rockfish.segy.database import SEGYHeaderDatabase
import numpy as np
from scipy.interpolate import interp1d
from sympy.physics import units
import logging

class SEGYPlotManager(object):
    """
    Plot manager for displaying SEG-Y data and picks.

    Handles plot layers, parameters, and unit conversions.
    """
    def __init__(self, ax, segy, pickdb=None,
                 trace_header_database=':memory:'):
        """
        Set default plotter configuration parameters

        :param ax: :class:`matplotlib.axes.Axes` instance to manage.
        :param segy: :class:`SEGYFile` with data to plot.
        :param pickdb: Optional. :class:`PickDatabaseConnection` with picks 
            to plot. Default is ``None``.
        :param trace_header_database: Optional. Filename for the
            trace header attribute look-up table database.  Default                        is to create the database in memory.
        """
        # Layer managers
        self.ACTIVE_LINES = {}
        self.INACTIVE_LINES = {}
        self.ACTIVE_PATCHES = {}
        self.INACTIVE_PATCHES = {}
        # General parameters
        self.ABSCISSA_KEY = 'computed_source_receiver_offset_in_m'
        # Data plotting parameters
        self.GAIN = 5.0
        self.CLIP = 1.0 
        self.NORMALIZATION_METHOD = 'trace'
        self.OFFSET_GAIN_POWER = 1.8
        self.WIGGLE_PEN_COLOR = 'black'
        self.WIGGLE_PEN_WIDTH = 0.5
        self.NEG_FILL_COLOR = 'red'
        self.POS_FILL_COLOR = 'black'
        # Unit parameters
        self.DISTANCE_UNIT = 'km'
        self.TIME_UNIT = 's'
        self.SEGY_TIME_UNITS = {'time':'ms',
                                'delay':'ms',
                                'sample_interval':'microseconds'}
        self.SEGY_DISTANCE_UNITS = {'offset':'m'}
        # Define aliases for SEGY header words
        self.SEGY_HEADER_ALIASES = {
            'shot':'original_field_record_number',
            'channel':'trace_number_within_the_original_field_record',
            'ensemble':'ensemble_number',
            'trace':'trace_number_within_the_ensemble',
            'sample_interval':'sample_interval_in_ms_for_this_trace',
            'delay':'delay_recording_time_in_ms',
            'trace_in_file':'trace_sequence_number_within_segy_file',
            'npts':'number_of_samples_in_this_trace',
            'offset':'source_receiver_offset_in_m'}
        # Link to a segy file and pick database
        self.segy = segy
        self.pickdb = pickdb
        # Build header look up table, if we have picks to plot
        if self.pickdb is not None:
            self._build_header_database(database=trace_header_database)
        # Attach axes
        self.ax = ax
        # Set global range parameters and build interpolators
        self._set_global_ranges()
        self._init_interpolators()

    def _activate_line(self, plot_item):
        """
        Moves a line from the inactive to active lines dictionary and adds
        it to the plot axes.

        :param plot_item: Name of plot item.
        """
        self.ACTIVE_LINES[plot_item] = self.INACTIVE_LINES.pop(plot_item)
        for line in self.ACTIVE_LINES[plot_item]:
            self.ax.lines.append(line)

    def _deactivate_line(self, plot_item):
        """
        Moves a line from the active to inactive lines dictionary and removes
        it from the plot axes.

        :param plot_item: Name of plot item.
        """
        self.INACTIVE_LINES[plot_item] = self.ACTIVE_LINES.pop(plot_item)
        for line in self.INACTIVE_LINES[plot_item]:
            self.ax.lines.remove(line)

    def _activate_patch(self, plot_item):
        """
        Moves a patch from the inactive to active lines dictionary and adds
        it to the plot axes.

        :param plot_item: Name of plot item.
        """
        self.ACTIVE_PATCHES[plot_item] = self.INACTIVE_PATCHES.pop(plot_item)
        for patch in self.ACTIVE_PATCHES[plot_item]:
            self.ax.patches.append(patch)

    def _deactivate_patch(self, plot_item):
        """
        Moves a patch from the active to inactive lines dictionary and removes
        it from the plot axes.

        :param plot_item: Name of plot item.
        """
        self.INACTIVE_PATCHES[plot_item] = self.ACTIVE_PATCHES.pop(plot_item)
        for patch in self.INACTIVE_PATCHES[plot_item]:
            self.ax.patches.remove(patch)

    def _delete_line(self, plot_item):
        """
        Removes line from the layer manager dictionaries and the plot.
        
        :param plot_item: Name of plot item.
        """
        if plot_item in self.ACTIVE_LINES:
            for line in self.ACTIVE_LINES.pop(plot_item):
                self.ax.lines.remove(line)
        if plot_item in self.INACTIVE_LINES:
            del self.INACTIVE_LINES[plot_item]

    def _delete_patch(self, plot_item):
        """
        Removes patch from the layer manager dictionaries and the plot.
        
        :param plot_item: Name of plot item.
        """
        if plot_item in self.ACTIVE_PATCHES:
            for patch in self.ACTIVE_PATCHES.pop(plot_item):
                self.ax.patches.remove(patch)
        if plot_item in self.INACTIVE_PATCHES:
            del self.INACTIVE_PATCHES[plot_item]

    def _manage_layers(self, force_new=False, **kwargs):
        """
        Activate or deactivate plot items and return a dictionary of
        ``True``/``False`` values for items that need to be replotted.

        :param force_new: Optional, bool. If ``True``, delete plot items from
            the dictionary and return ``True`` for all items.
        :param **kwargs: Keyword=Bool arguments for plot items to
            activate/deactivate.  If plot item is not currently in one of the
            plot item dictionaries, it is set ``True``.
        :returns: Dictionary of ``True`` or ``False`` values for plot items. 
            If the plot item needs to be plotted, returns ``True``, else
            ``False``.
        """
        for plot_item in kwargs:
            if plot_item in self.ACTIVE_LINES or self.INACTIVE_LINES:
                if kwargs[plot_item] and force_new:
                    self._delete_line(plot_item)
                elif kwargs[plot_item] and plot_item in self.ACTIVE_LINES:
                    # item is already plotted
                    kwargs[plot_item] = False
                elif not kwargs[plot_item] and plot_item in self.ACTIVE_LINES:
                    # remove from current plot
                    kwargs[plot_item] = False
                    self._deactivate_line(plot_item)
                elif kwargs[plot_item] and plot_item in self.INACTIVE_LINES:
                    # just reactivate it
                    kwargs[plot_item] = False
                    self._activate_line(plot_item)
            elif plot_item in self.ACTIVE_PATCHES or self.INACTIVE_PATCHES:
                if kwargs[plot_item] and force_new:
                    self._delete_patch(plot_item)
                elif kwargs[plot_item] and plot_item in self.ACTIVE_PATCHES:
                    # item is already plotted
                    kwargs[plot_item] = False
                elif not kwargs[plot_item] and plot_item in self.ACTIVE_PATCHES:
                    # remove from current plot
                    kwargs[plot_item] = False
                    self._deactivate_patch(plot_item)
                elif kwargs[plot_item] and plot_item in self.INACTIVE_PATCHES:
                    # just reactivate it
                    kwargs[plot_item] = False
                    self._activate_patch(plot_item)
        logging.debug('active lines: %s', self.ACTIVE_LINES)
        logging.debug('inactive lines: %s', self.INACTIVE_LINES)
        logging.debug('active patches: %s', self.ACTIVE_PATCHES)
        logging.debug('inactive patches: %s', self.INACTIVE_PATCHES)
        logging.debug('items to plot: %s', kwargs)
        return kwargs


    def _build_header_database(self, database=':memory:'):
        """
        Builds a look-up table for trace header attributes.
        """
        # Make sure abcissa key is in the table (trace in file = rowid)
        header_keys = [self._get_header_alias(self.ABSCISSA_KEY)]
        # Add pick primary keys if we need them
        if self.pickdb is not None:
            pick_keys = self.pickdb._get_primary_fields(
                self.pickdb.TRACE_TABLE)
            for k in [self._get_header_alias(k) for k in pick_keys]:
                if k not in header_keys:
                    header_keys.append(k)
        # Build a database table for looking up header values
        self.sdb = SEGYHeaderDatabase(self.segy, *header_keys, 
                                      database=database)

    def get_time_array(self, header, convert_units=True):
        """
        Get an array of time for a single trace header.

        :param header: single ``SEGYTraceHeader`` instance
        :param convert_units: Bool, optional.  If true, convert units to plot
            units.
        :returns: ``list`` of time values
        """
        delay = self.get_header_value(header,'delay', 
                                      convert_units=convert_units)
        npts = self.get_header_value(header,'npts', 
                                     convert_units=convert_units)
        dt = self.get_header_value(header, 'sample_interval',
                                   convert_units=convert_units)
        return  list(delay + np.asarray(range(0,npts)) * dt)

    def get_header_value(self, header, key, convert_units=True):
        """
        Gets a value from trace header.  

        :param header: single ``SEGYTraceHeader`` object
        :param key: ``bool``, name of trace header attribute
        :param convert_units: ``bool``, convert units to plot units if true
        :returns: value of trace header attribute
        """
        _key = self._get_header_alias(key)
        try:   
            # use the unpacked value
            value = header.__getattribute__(_key)
        except AttributeError:
            value = header.__getattr__(_key)

        if convert_units is True:
            return self._convert_units(key, [value])[0]
        else:
            return value

    def _get_header_alias(self, key):
        """
        Finds the header attribute name for an alias.  If none exists, returns
        input ``key``.

        :param key: keyword ``str`` in ``HEADER_ALIASES``
        """
        try:
            return self.SEGY_HEADER_ALIASES[key.lower()]
        except KeyError:
            return key

    def _convert_units(self, key, values):
        """
        Convert SEGY units to plot units.
        """
        _units = self._get_units(key)
        if _units is not None:
            scl =  float(units.__getattribute__(_units[0])\
                         /units.__getattribute__(_units[1]))
            return [v * scl for v in values]
        else:
            return values

    def _get_units(self, key):
        """
        :param key: Trace header attribute name.
        :returns: (<segy units>, <plot units>) if ``key`` is in SEGY_TIME_UNITS
            or SEGY_DISTANCE_UNITS, or ``None`` if units are not specified.
        """
        _key = self._get_header_alias(key)
        if key in self.SEGY_TIME_UNITS:
            return (self.SEGY_TIME_UNITS[key], self.TIME_UNIT)
        elif _key in self.SEGY_TIME_UNITS:
            return (self.SEGY_TIME_UNITS[_key], self.TIME_UNIT)
        elif key in self.SEGY_DISTANCE_UNITS:
            return (self.SEGY_DISTANCE_UNITS[key], self.DISTANCE_UNIT)
        elif _key in self.SEGY_DISTANCE_UNITS:
            return (self.SEGY_DISTANCE_UNITS[_key], self.DISTANCE_UNIT)
        else:
            return None

    def _get_abscissa(self, keys, values, convert_units=True):
        """
        Get plot abscissa values from the trace header database.
        """
        _keys = [self._get_header_alias(k) for k in keys]
        sql = "SELECT " + self._get_header_alias(self.ABSCISSA_KEY)
        sql += " FROM " + self.sdb.TRACE_TABLE
        sql += " WHERE " + " and ".join(['%s=?' %k for k in _keys])
        x = []
        for row in values:
            msg = 'calling sdb.execute(' + str(sql) + ', '
            msg += str(row) + ')'
            logging.debug(msg)
            _x = self.sdb.execute(sql, row).fetchone()
            if _x:
                x.append(_x[0])
            else:
                x.append(None)
        return x

    def _set_global_ranges(self):
        """
        Set parameters based on the range of all traces.
        """
        self.X = [self.get_header_value(tr.header, self.ABSCISSA_KEY) \
                  for tr in self.segy.traces]
        self.DX = abs(np.mean(np.diff(self.X)))
        self.T = self.get_time_array(self.segy.traces[0].header)
        self.XLIMITS = [self.X[0], self.X[-1]]
        self.TLIMITS = [self.T[0], self.T[-1]]
        self.AMP_MAX = np.max([tr.data for tr in self.segy.traces])

    def _init_interpolators(self):
        """
        Creates the methods ``abscissa2trace(xplt)`` and 
        ``trace2abscissa(idx)`` for converting an x-coordinate to
        a trace index and visa versa.
        """
        ntrc = len(self.segy.traces)
        idx = range(0, ntrc)
        self.trace2abscissa = interp1d(idx, self.X, kind='nearest')
        self.abscissa2trace = interp1d(self.X, idx, kind='nearest')

