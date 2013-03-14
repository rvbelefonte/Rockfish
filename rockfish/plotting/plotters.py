"""
Classes for plotting SEG-Y data and picks
"""
import logging
import matplotlib.pyplot as plt
from rockfish.plotting.managers import SEGYPlotManager
import numpy as np


class SEGYPlotter(SEGYPlotManager):
    """
    Convience class for plotting SEG-Y data. 
    """
    def __init__(self, ax, segy,
                 trace_header_database=':memory:'):
        """
        :param ax: :class:`matplotlib.axes.Axes` instance to manage.
        :param segy: :class:`SEGYFile` with data to plot.
        :param trace_header_database: Optional. Filename for the
            trace header attribute look-up table database.  Default                        is to create the database in memory.
        """
        SEGYPlotManager.__init__(self, ax, segy, pickdb=None,
            trace_header_database=trace_header_database)

    def plot_wiggles(self, force_new=False, traces=None, **kwargs):
        """
        Plots wiggle traces.

        :param traces: Optional. Give a subset of traces to plot. Default is
            to plot all traces.
        :param negative_fills: Optional. ``bool``.  If ``True``, draws or
            replaces negative wiggle fills.  If ``False``, removes any existing            negative wiggle fills.  Default is to leave negative fills 
            unchanged.
        :param positive_fills: Optional. ``bool``.  If ``True``, draws or
            replaces positive wiggle fills.  If ``False``, removes any existing            positive wiggle fills.  Default is to leave positive fills 
            unchanged.
        :param wiggle_traces: Optional. ``bool``.  If ``True``, draws or
            replaces wiggle traces.  If ``False``, removes any existing wiggle             fills.  Default is to leave wiggle traces unchanged.
        :param force_new: Optional.  If ``True``, existing wiggle plot items 
            are removed from the plot if they exist and replotted for all plot
            items set to ``True``.  Default is to look for existing items in 
            the layer manager and add them back to the axes without replotting.
        """
        # Activate/deactivate plot items and get items to plot 
        plot_items = self._manage_layers(**kwargs)
        for item in ['negative_fills', 'positive_fills', 'wiggle_traces']:
            if item not in plot_items:
                plot_items[item] = False
        if True not in [plot_items[item] for item in plot_items]:
            # nothing to do here
            return
        if traces is None:
            traces = self.segy.traces
        # Collect plot data
        x_neg = []; x_pos = []; x_wig = []; t = []
        for tr in traces: 
            t += self.get_time_array(tr.header) + [None]
            xplt = self.get_header_value(tr.header, self.ABSCISSA_KEY)
            amp = self._get_scaled_trace_data(tr)
            if plot_items['negative_fills']:
                _amp = np.clip(amp, -1.e999, 0.)
                _amp[[0, -1]] = 0
                x_neg += list(xplt + _amp) + [None] 
            if plot_items['positive_fills']:
                _amp = np.clip(amp, 0., 1.e999)
                _amp[[0, -1]] = 0
                x_pos += list(xplt + _amp) + [None] 
            if plot_items['wiggle_traces']:
                x_wig += list(xplt + amp) + [None]
        # Plot all traces together
        if plot_items['negative_fills']:
            self.ACTIVE_PATCHES['negative_fills'] =\
                self.ax.fill(x_neg, t, color=self.NEG_FILL_COLOR, lw=0)
        if plot_items['positive_fills']:
            self.ACTIVE_PATCHES['positive_fills'] =\
                self.ax.fill(x_pos, t, color=self.POS_FILL_COLOR, lw=0)
        if plot_items['wiggle_traces']:
            self.ACTIVE_LINES['wiggle_traces'] =\
                self.ax.plot(x_wig, t, color=self.WIGGLE_PEN_COLOR,
                             lw=self.WIGGLE_PEN_WIDTH)

    def _get_scaled_trace_data(self, tr):
        """
        Scale amplitudes according to plot parameters.

        :param tr: A single :class:`SEGYTrace` instance.
        """
        if(self.NORMALIZATION_METHOD == 'trace'):
            amp_max = tr.data.max() * 2./self.DX
        else:
            amp_max = self.AMP_MAX * 2./self.DX
        clip = self.DX * (self.CLIP/2.)
        xgain = abs(self.get_header_value(tr.header, 'offset'))\
                **self.OFFSET_GAIN_POWER
        amp = tr.data * float(self.GAIN) * xgain
        if(amp_max == 0):
            amp_max = 1
        return np.clip(amp/amp_max, -clip, clip)


class SEGYPickPlotter(SEGYPlotter):
    """
    Plot picks on SEG-Y data. 
    """
    def __init__(self, ax, segy, pickdb, 
                 trace_header_database=':memory:'):
        """
        :param ax: :class:`matplotlib.axes.Axes` instance to manage.
        :param segy: :class:`SEGYFile` with data to plot.
        :param pickdb: :class:`PickDatabaseConnection` with picks to plot.
        :param trace_header_database: Optional. Filename for the
            trace header attribute look-up table database.  Default                        is to create the database in memory.
        """
        SEGYPlotManager.__init__(self, ax, segy, pickdb=pickdb,
                                 trace_header_database=trace_header_database)

    def plot_picks(self, force_new=False, **kwargs):
        """
        Plot picks on top of SEG-Y data.

        :param force_new: Optional.  If ``True``, any existing picks are
            removed from the plot and (re)plotted.  Default is to look
            for existing picks in the layer manager and add them to the axes
            before plotting.
        :param **kwargs: Optional.  keyword=value arguments with values to 
            match when looking for picks to plot from the pick database.
            Default is to plot all picks.
        """
        # Get a list of events to plot
        if 'event' in kwargs:
            events = [kwargs.pop('event')]
        else:
            events = self.pickdb.events
        # Plot picks by event
        pick_keys = self.pickdb._get_primary_fields(
            self.pickdb.TRACE_TABLE)
        for event in events:
            logging.debug("plotting picks for event '%s'", event)
            key_values = []
            t = []
            for row in self.pickdb.get_picks(event=event, **kwargs):
                key_values.append(tuple([row[k] \
                                         for k in pick_keys]))
                t.append(row['time'])
            x = self._get_abscissa(pick_keys, key_values)
            symbol = row['plot_symbol']
            self._plot_picks(event, x, t, symbol, force_new=force_new)

    def _plot_picks(self, event, x, t, symbol, force_new=False):
        """
        Plot picks for a single event.
        """
        if force_new:
            self._delete_line(event)
        else:
            if event in self.ACTIVE_LINES:
                return
            elif event in self.INACTIVE_LINES:
                self._activate_line(event)
                return
        self.ACTIVE_LINES[event] = self.ax.plot(x, t, symbol)


class VMPlotter(object):
    """
    Convience class for plotting VM models, rays, and traveltimes. 
    """
    def __init__(self, vm=None, rays=None, fig=None):
        """
        :param vm: Optional :class:`rockfish.tomography.model.VM` instance to
            plot. Only plotted if given.
        :param rays: Optional. :class:`rockfish.tomography.rayfan.RayfanGroup`
            with raypaths and traveltimes to plot. Only plotted if given.
        :param fig: Optional. :class:`matplotlib.pyplot.figure` instance to 
            manage. Default is to create a new figure.
        """
        self.vm = vm
        self.rays = rays
        if fig is None:
            self.fig = plt.figure()
        else:
            self.fig = fig

    def plot2d(self, model=True, paths=True, traced=True, picked=True,
               residuals=True, colorbar=False, show=True, event_colors={},
               vmin=None, vmax=None):
        """
        Plot a 2D velocity model, rays, and/or travel-times.

        :param model: Optional. Determines whether or not to plot the velocity
            model, if one exists. Default is ``True``.
        :param paths: Optional. Determines whether or not to plot raypaths,
            if they exist. Default is ``True``.
        :param traced: Optional. Determines whether or not to plot raytraced 
            travel times, if they exist. Default is ``True``.
        :param picked: Optional. Determines whether or not to plot picked
            travel times, if they exist. Default is ``True``.
        :param residuals: Optional. Determines whether or not to residuals, if
            they exist. Default is ``True``.
        :param colorbar: Show a colorbar. Default is ``False``.
        :param event_colors: Optional. Dictionary of event names and colors
            to use for plotting raypaths and times for different events. If
            ``event_colors`` is not given, or if an event ID is not in
            ``event_colors``.  Default is to plot raypaths in grey and
            and times in black.
        :returns: ``list`` of :class:`matplotlib.pyplot.Axes` that were 
            created.
        """
        self.fig.clf
        rows = 0
        if (model and (self.vm is not None)) or \
           (paths and (self.rays is not None)):
            rows += 1
        if (traced or picked) and (self.rays is not None):
            rows += 1
        if residuals and (self.rays is not None):
            rows += 1
        ax = [self.fig.add_subplot(rows, 1, 1)]
        if model and (self.vm is not None):
            self.vm.plot(ax=ax[-1], vmin=vmin, vmax=vmax, colorbar=colorbar)
        if paths and (self.rays is not None):
            self.rays.plot_raypaths(ax=ax[-1], event_colors=event_colors)
        if (traced or picked) and (self.rays is not None):
            ax.append(self.fig.add_subplot(rows, 1, 2))
            self.rays.plot_time_vs_position(ax=ax[-1], traced=traced,
                                            picked=picked,
                                            event_colors=event_colors)
            ax[-1].set_xlim([self.vm.r1[0], self.vm.r2[0]])
        if residuals and (self.rays is not None):
            ax.append(self.fig.add_subplot(rows, 1, 3))
            self.rays.plot_residual_vs_position(ax=ax[-1],
                                                event_colors=event_colors)
            ax[-1].set_xlim([self.vm.r1[0], self.vm.r2[0]])
        if show:
            self.fig.show()
        return ax
