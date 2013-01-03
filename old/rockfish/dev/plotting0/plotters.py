"""
Plotting methods.
"""
import os
import logging
import warnings
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from sympy.physics import units

from rockfish.plotting.layers import SEGYPlotLayerManager
from rockfish.picking.database import PickDatabaseConnection

class SEGYPlotterError(Exception):
    """
    Base segy.plotting exception class.
    """
    pass

class SEGYPlotterParameterError(SEGYPlotterError):
    """
    Raised if SEGYPlotter encounters an invalid parmeter value. 
    """
    pass

class SEGYPlotterConfig(object):
    """
    Convience class for handling plotter configuration.
    """

    def __init__(self):

        self.PARAM = {'gain': 5.0,
                      'clip': 3.0,
                      'normalization': 'global',
                      'offset_gain_power':1.8,
                      'wiggle_pen_color':'black',
                      'wiggle_pen_width':0.5,
                      'negative_fill_color':'red',
                      'positive_fill_color':'black',
                      'xplt_key':'trace',
                      'distance_units': 'km',
                      'time_units':'s',
                      'time_limits':None,
                      'idx':None}

        # Initialize plot configuration parameters
        self.PLOT_X = None
        self.PLOT_DX = None
        self.PLOT_T = None
        self.PLOT_XLIMITS = None
        self.PLOT_TLIMITS = None
        self.PLOT_AMP_MAX = None
        
        # Define units for header words
        self.SEGY_TIME_UNITS = {'time':'ms',
                                 'delay_recording_time':'ms',
                                 'sample_interval_in_ms_for_this_trace':'microseconds'}
        self.SEGY_DISTANCE_UNITS = {
                            'distance_from_center_of_the_source_point_to_'\
                            + 'the_center_of_the_receiver_group':'m'}

        # Define aliases for header words
        self.HEADER_ALIASES = {'shot':'original_field_record_number',
            'chan':'trace_number_within_the_original_field_record',
            'cdp':'ensemble_number',
            'cdptr':'trace_number_within_the_ensemble',
            'srcx':'source_coordinate_x',
            'srcy':'source_coordinate_y',
            'recx':'group_coordinate_x',
            'recy':'group_coordinate_y',
            'trace':'trace_sequence_number_within_segy_file',
            'offset':'distance_from_center_of_the_source_point_to_'\
                       + 'the_center_of_the_receiver_group'}

    def set(self,**kwargs):
        """
        Sets parameter values in ``SEGYPlotter.param``.

        :param **kwargs: keyword=value arguments.
        
        .. rubric:: Example:
        >>> splt = SEGYPlotter()
        >>> splt.set(gain=10,normalization='trace')
        >>> print splt.PARAM['gain'] 
        10
        >>> print splt.PARAM['normalization'] 
        trace
        """
        for key in kwargs:
            self.PARAM[key] = kwargs[key]


class SEGYPlotter(SEGYPlotterConfig):
    """
    Class for plotting SEG Y data.
    """

    def __init__(self, segy=None):
        """
        Set default plotting configuration

        :param segy: :class:`SEGYFile` instance with data to plot.
        """
        SEGYPlotterConfig.__init__(self)
        self.manager = SEGYPlotLayerManager()
        self.segy = segy

    def get_header_value(self,header,key,convert_units=True):
        """
        Gets a value from trace header.  
        
        This function ensures that unpacked values are read, in case they have
        been modified without updating the packed header.  Honors trace
        attribute alias.

        :param header: single ``SEGYTraceHeader`` object
        :param key: ``bool``, name of trace header attribute
        :param convert_units: ``bool``, convert units to plot units if true
        :returns: value of trace header attribute

        .. rubric:: Example:
        >>> from rockfish.segy.segy import readSEGY
        >>> from rockfish.core.util import get_example_file
        >>> segy = readSEGY(get_example_file('obs.segy'))
        >>> splt = SEGYPlotter()
        >>> n = splt.get_header_value(segy.traces[0].header,'ensemble_number')
        >>> print n
        1
        """
        key = self._get_header_alias(key)
        try:   
            # use the unpacked value
            value = header.__getattribute__(key)
        except AttributeError:
            value = header.__getattr__(key)

        if(convert_units):
            return self._convert_units(key,value)
        else:
            return value

    def get_time_array(self,header,convert_units=True):
        """
        Get an array of time for a single trace header.

        :param header: single ``SEGYTraceHeader`` instance
        :param convert_units: ``bool``, convert units to plot units if true
        :returns: ``numpy`` array of time values

        .. rubric:: Example:
        >>> from rockfish.segy.segy import readSEGY
        >>> from rockfish.core.util import get_example_file
        >>> segy = readSEGY(get_example_file('obs.segy'))
        >>> splt = SEGYPlotter()
        >>> t = splt.get_time_array(segy.traces[0].header,convert_units=False)
        >>> print t
        [      0    5000   10000 ..., 7990000 7995000 8000000]
        >>> t = splt.get_time_array(segy.traces[0].header,convert_units=True)
        >>> print t
        [  0.00000000e+00   5.00000000e-03   1.00000000e-02 ...,   7.99000000e+00
           7.99500000e+00   8.00000000e+00]

       """
        delay = self.get_header_value(header,'delay_recording_time',
                                      convert_units=convert_units)
        npts = self.get_header_value(header,'number_of_samples_in_this_trace',
                                      convert_units=convert_units)
        dt = self.get_header_value(header,
                                   'sample_interval_in_ms_for_this_trace',
                                      convert_units=convert_units)
        return  delay + np.asarray(range(0,npts)) * dt

    def get_units(self,key):
        """
        Get plot units of a SEGY header word.
        """
        key = self._get_header_alias(key)
        if key in self.SEGY_TIME_UNITS:
            return self.PARAM['time_units']
        elif key in self.SEGY_DISTANCE_UNITS:
            return self.PARAM['distance_units']
        else:
            return None

    def get_xplt(self,header):
        """
        Gets the plot x-coordinate value for the current trace.

        .. rubric:: Example:
        >>> from rockfish.segy.segy import readSEGY
        >>> from rockfish.core.util import get_example_file
        >>> segy = readSEGY(get_example_file('obs.segy'))
        >>> splt = SEGYPlotter()
        >>> splt.set(xplt_key='offset')
        >>> print splt.get_xplt(segy.traces[0].header)
        -75.637
        >>> splt.set(xplt_key='trace')
        >>> print splt.get_xplt(segy.traces[0].header)
        1
        """
        return self.get_header_value(header,[self.PARAM['xplt_key']][0])

    def init_xplt2trace(self,traces):
        """
        Creates the methods ``xplt2trace(xplt)`` and ``trace2xplt(idx)`` for converting
        an x-coordinate to a trace index and visa versa.
        
        :param traces: list of ``SEGYTrace`` objects
        """
        # Make sure we have an x-coordinate for every trace
        if(not self.PLOT_X):
            self.set_global_ranges(traces)

        # Build the interpolators
        self.trace2xplt = interp1d(range(0,len(traces)),self.PLOT_X,
                                    kind='nearest')
        self.xplt2trace = interp1d(self.PLOT_X,range(0,len(traces)),
                                    kind='nearest')

    def label_axes(self,ax):
        """
        Add labels to axes.
        """
        xunits = self.get_units(self.PARAM['xplt_key'])
        name = self._typeset(self.PARAM['xplt_key'])
        if xunits:
            plt.xlabel(name + " (" + str(xunits) +")")
        else:
            plt.xlabel(name)
        
        plt.ylabel( "Time (" + self.PARAM['time_units'] + ")")

    def plot(self,traces,axes=None,
                     xlim=None, tlim=None,
                     negative_fill=False, positive_fill=True,
                     wiggle_trace=False, pickdb=None,
                     label_axis=True,
                     use_manager=True,
                     replot=False,
                     events=':all:',
                     sphinx=False, **kwargs):
        """
        Plots negative fills, positive fills, traces, and/or picks.
        
        :param traces: Traces to plot.
        :param axes: Optional. :class:`matplotlib.axes.Axes` to plot into.  Default is to
            create and show a new plot.
        :param negative_fill: Optional. ``bool``.  If ``True``, draws negative wiggle
            fills.  Default is ``False``.
        :param positive_fill: Optional. ``bool``.  If ``True``, draws positive wiggle
            fills. Default is ``True``.
        :param wiggle_trace: Optional. ``bool``.  If ``True``, draws wiggle traces.
            Default is ``False``.
        :param pickdb: Optional. :mod:`rockfish.picking.picksegy.SEGYPickDatabase`
            instance with an active database connection.  If given, picks are
            plotted from this database.
        :param xlim: Optional.  If given, horizontal plot limits are set by
            passing ``xlim`` to :meth:`matplotlib.axes.Axes.set_xlim`
        :param tlim: Optional.  If given, vertical plot limits are set by
            passing ``tlim`` to :meth:`matplotlib.axes.Axes.set_ylim`
        :param label_axis: Optional.  If ``True``, labels plot axis with true
            units. 
        :param use_manager: Optional.  If ``True``, plotter interfaces with the
            layer manager.
        :param sphinx: Optional.  If ``True``, runs :meth:`matplotlib.pyplot.draw` so that a plot
            is generated for inclusion in the Sphinx documentation.  Default is
            ``False``.
        """
        self.set(**kwargs)

        # Get new axis if not given
        if axes:
            ax = axes
        else:
            fig = plt.figure()
            ax = fig.add_subplot(111)

        # Plot the data
        if negative_fill:
            self.mplot(ax,traces,'negfills',use_manager=use_manager,
                       replot=replot)
        if positive_fill:
            self.mplot(ax,traces,'posfills',use_manager=use_manager,
                       replot=replot)
        if wiggle_trace:
            self.mplot(ax,traces,'wiggles',use_manager=use_manager,
                       replot=replot)
        if pickdb:
            self.mplot(ax,traces,'picks',use_manager=use_manager,
                       pickdb=pickdb,events=events,replot=replot)

        # label axis with true units
        if label_axis:
            self.label_axes(ax)

        # set plot limits
        if not xlim or not tlim:
            self.set_global_ranges(traces)

        if xlim:
            ax.set_xlim(xlim)
        else:
            ax.set_xlim(self.PLOT_XLIMITS)
        
        if tlim:
            ax.set_ylim(tlim)
        else:
            ax.set_ylim(self.PLOT_TLIMITS)

        # create the interpolators
        self.init_xplt2trace(traces)

        # show the plot if this is a new axis, or we are not in sphinx
        if not sphinx or axes:
            plt.draw()
        else:
            plt.show()

    def mplot(self,ax,traces,plot_item,use_manager=True,pickdb=None,
              events=':all:', replot=False):
        """
        Plotting function that interaces with the plot item manger.
        """
        plot = False
        if self.manager and use_manager:
            if replot:
                self.manager.remove(plot_item, axes=ax)
            if self.manager.status(plot_item) == 'active':
                # Do not replot
                return
            elif self.manager.status(plot_item) == 'inactive':
                # Just re-add artists to the plot
                self.manager.toggle(plot_item,axis=ax)
                return
            else:
                plot = True
        else:
            plot = True

        if plot:
            artists = None
            # Draw the data
            if plot_item == 'negfills':
                artists = self._plot_wiggle_negative_fills(ax,traces)
            elif plot_item == 'posfills':
                artists = self._plot_wiggle_positive_fills(ax,traces)
            elif plot_item == 'wiggles':
                artists = self._plot_wiggle_traces(ax,traces)
            elif plot_item == 'picks' and pickdb:
                artists = self._plot_picks(ax,traces,pickdb,events=events)
            
            # Add new items to the plot manager
            if self.manager and use_manager and len(artists) > 0:
                for item in artists:
                    self.manager.add(item,plot_item)

    def _plot_wiggle_negative_fills(self,ax,traces):
        """
        Plots negative wiggle fills into an existing axis.

        :param ax: ``matplotlib`` axis
        :param traces: list of ``SEGYTrace`` objects

        .. rubric:: Example:
        >>> from rockfish.segy.segy import readSEGY
        >>> from rockfish.core.util import get_example_file
        >>> import matplotlib.pyplot as plt
        >>> splt = SEGYPlotter()
        >>> sgy = readSEGY(get_example_file('obs.segy'))
        >>> fig = plt.figure()
        >>> ax = fig.add_subplot(111)
        >>> trcs = sgy.traces[300:310]
        >>> splt.set_global_ranges(trcs)
        >>> negfills = splt._plot_wiggle_negative_fills(ax,trcs)
        >>> print negfills
        Poly((301, 0) ...)
        """
        if(not self.PLOT_DX or not self.PLOT_AMP_MAX):
            self.set_global_ranges(traces)

        # Collect data to plot
        x = []
        t = []
        for tr in traces:
            time = self.get_time_array(tr.header)
            xplt = self.get_xplt(tr.header)
            amp = np.clip(self.scale_data(tr),-1.e999,0.)
            amp[[0,-1]] = 0.
            x += list(xplt + amp) + [None]
            t += list(time) + [None]

        # Plot all the data at once into a single artist
        patches, = ax.fill(x,t,color=self.PARAM['negative_fill_color'],lw=0.)

        return [patches]

    def _plot_wiggle_positive_fills(self,ax,traces):
        """
        Plots positive wiggle fills into an existing axis.

        :param ax: ``matplotlib`` axis
        :param traces: list of ``SEGYTrace`` objects

        .. rubric:: Example:
        >>> from rockfish.segy.segy import readSEGY
        >>> from rockfish.core.util import get_example_file
        >>> import matplotlib.pyplot as plt
        >>> splt = SEGYPlotter()
        >>> segy = readSEGY(get_example_file('obs.segy'))
        >>> fig = plt.figure()
        >>> ax = fig.add_subplot(111)
        >>> splt.set_global_ranges(segy.traces[300:310])
        >>> posfills = splt._plot_wiggle_positive_fills(ax,segy.traces[300:310])
        >>> print posfills
        Poly((301, 0) ...)
        """
        if(not self.PLOT_DX or not self.PLOT_AMP_MAX):
            self.set_global_ranges(traces)

        # Collect data to plot
        x = []
        t = []
        for tr in traces:
            time = self.get_time_array(tr.header)
            xplt = self.get_xplt(tr.header)
            amp = np.clip(self.scale_data(tr),0.,1.e999)
            amp[[0,-1]] = 0.
            x += list(xplt + amp) + [None]
            t += list(time) + [None]

        # Plot all the data at once into a single artist
        patches, = ax.fill(x,t,color=self.PARAM['positive_fill_color'],lw=0.)
        
        return [patches]

    def _plot_wiggle_traces(self,ax,traces):
        """
        Plots wiggle traces into an existing axis.

        :param ax: ``matplotlib`` axis
        :param traces: list of ``SEGYTrace`` objects

        .. rubric:: Example:
        >>> from rockfish.segy.segy import readSEGY
        >>> from rockfish.core.util import get_example_file
        >>> import matplotlib.pyplot as plt
        >>> splt = SEGYPlotter()
        >>> segy = readSEGY(get_example_file('obs.segy'))
        >>> fig = plt.figure()
        >>> ax = fig.add_subplot(111)
        >>> splt.set_global_ranges(segy.traces[300:310])
        >>> wgls = splt._plot_wiggle_traces(ax,segy.traces[300:310])
        >>> print wgls
        Line2D(_line0)
        """
        if(not self.PLOT_DX or not self.PLOT_AMP_MAX):
            self.set_global_ranges(traces)

        # Collect data to plot
        x = []
        t = []
        for tr in traces:
            time = self.get_time_array(tr.header)
            xplt = self.get_xplt(tr.header)
            amp = self.scale_data(tr)
            x += list(xplt + amp) + [None]
            t += list(time) + [None]

        # Plot all the data at once into a single artist
        lines, = ax.plot(x,t,color=self.PARAM['wiggle_pen_color'],
                             lw=self.PARAM['wiggle_pen_width'])

        return [lines]

    def _plot_picks(self,ax,traces,pickdb,events=':all:'):
        """"
        Plot picks from a :class:`PickDatabseConnection`

        :param ax: ``matplotlib`` axes to plot into
        :param pickdb: :class:`PickDatabaseConnection` instance with an active
            database connection
        :param traces: list of ``SEGYTrace`` objects
        :param events: ``list`` of ``str`` event names to plot. Default is to plot
            all picks in the database.

        Picks are assigned to traces by matching the following fields:

        ============== ================================
        Database field Header attribute
        ============== ================================
        ensemble       ensemble_number 
        trace          trace_number_within_the_ensemble 
        ============== ================================

        """
        assert isinstance(pickdb,PickDatabaseConnection), \
                'pickdb must be a PickDatabaseConnection instance'

        if(not self.PLOT_DX or not self.PLOT_AMP_MAX):
            self.set_global_ranges(traces)

        if events == ':all:':
            events = pickdb.events
        else:
            events = self._iterable(events)

        if(not events):
            return

        new_lines = []
        # XXX this is dog slow, need a plot function that can handle plotting
        # single events
        # XXX\ do something like this:
        # loop over traces
        #   get xplt for trace
        #   loop over events
        #       picks = pickdb.get_picks(event=event)
        #       t = [row['time'] for row in picks]
        #       sym = picks[0]['plot_symbol']
        # XXX/
        for event in events:
            idx = -1
            x = []
            t = []
            plot_symbol = '.g'
            for tr in traces:
                idx += 1
                ensemble = self.get_header_value(tr.header,'ensemble_number')
                trace = self.get_header_value(tr.header,'trace_number_within_the_ensemble')
                picks = pickdb.get_picks(event=event, ensemble=ensemble,
                                         trace=trace)
                if len(picks) > 0:
                    plot_symbol = picks[0]['plot_symbol']
                    t += [picks[0]['time']]
                    try: 
                        x += [float(self.trace2xplt(idx))] # numpy array to list
                    except ValueError:
                        msg = """
                              Warning: ignoring pick from outside of data
                              range (ensemble=%s, trace=%s).
                              """ % (ensemble, trace)
                        warnings.warn(msg.strip())

            if len(x) > 0:
                lines, = ax.plot(x, t, plot_symbol)
                new_lines.append(lines)

        if len(new_lines) > 0:
            return new_lines
        else:
            return None


    def scale_data(self,trace):
        """
        Scale amplitudes according to plot parameters.

        .. rubric:: Example:
        >>> from rockfish.segy.segy import readSEGY
        >>> from rockfish.core.util import get_example_file
        >>> splt = SEGYPlotter()
        >>> segy = readSEGY(get_example_file('obs.segy'))
        >>> print segy.traces[0].data
        [ 724666.75        907527.75        933675.6875     ...,   -1236.4921875
           48141.76171875   82538.515625  ]
        >>> splt.set_global_ranges(segy.traces)
        >>> print splt.scale_data(segy.traces[0])
        [ 1.5         1.5         1.5        ..., -0.01637624  0.637595    1.09314942]

        """
        if(self.PARAM['normalization'] == 'trace'):
            amp_max = trace.data.max() * 2./self.PLOT_DX
        else:
            amp_max = self.PLOT_AMP_MAX * 2./self.PLOT_DX

        clip = self.PLOT_DX * (self.PARAM['clip']/2.)
        xgain = abs(self.get_header_value(trace.header,
                                self._get_header_alias('offset')))\
                **self.PARAM['offset_gain_power']
        amp = trace.data * float(self.PARAM['gain']) * xgain

        if(amp_max == 0):
            amp_max = 1

        return np.clip(amp/amp_max,-clip,clip)

    def set_global_ranges(self,traces):
        """
        Set parameters based on the global range of all traces.

        :param traces: list of ``SEGYTrace`` objects

        .. warning:: Assumes that traces are sorted as they will be plotted.

        .. rubric:: Sets the following values:

        ============ ========= ================================================
        Parameter    Type      Description
        ============ ========= ================================================
        PLOT_X        ``list``  List of plot-space x-coordinates for all traces.
        PLOT_DX       ``float`` Average spacing between traces.
        PLOT_T        ``list``  List of t-values for the first trace.
        PLOT_XLIMITS  ``list``  List of min,max plot-space x-coordinates.
        PLOT_TLIMITS  ``list``  List of min,max time values. 
        PLOT_AMP_MAX  ``float`` Maximum amplitude from all traces. 
        ============ ========= ================================================
        """
        traces = self._iterable(traces)

        # Get plot x-coordinate for every trace
        self.PLOT_X = []
        for tr in traces:
            self.PLOT_X.append(self.get_header_value(tr.header,
                                     self._get_header_alias(self.PARAM['xplt_key'])))

        # Set the average trace spacing in the plot
        self.PLOT_DX = abs(np.mean(np.diff(self.PLOT_X)))

        # Set time range from the 1st trace
        self.PLOT_T = self.get_time_array(traces[0].header)

        # Set limits
        self.PLOT_XLIMITS = [min(self.PLOT_X),max(self.PLOT_X)]
        self.PLOT_TLIMITS = [min(self.PLOT_T),max(self.PLOT_T)]

        # Set global max amplitude
        self.PLOT_AMP_MAX = np.max([tr.data for tr in traces])

        # Build plot-space x-coord. to trace index (and visa versa)
        # interpolators
        self.init_xplt2trace(traces)

    def set_limits(self,ax):
        """
        Set axis limits to match data limits.
        """
        ax.set_ylim(self.PLOT_TLIMITS)
        ax.set_xlim(self.PLOT_XLIMITS)

    def toggle_plot_item(self,artist_name,traces=None,pickdb=None):
        """
        Draws/replaces or removes an artist from the plot.
        
        :param artist_name: Name of an artist to toggle.
        :param traces: list of ``SEGYTrace`` objects to potentially plot
        :param pickdb: :mod:`rockfish.picking.picksegy.SEGYPickDatabase` instance with an active
            database connection
        """

        pass 

    #------------------------------------------------
    # Private methods
    #------------------------------------------------
    
    def _convert_units(self,key,value):
        """
        Convert SEGY units to plot units.

        :Uses: ``sympy.physics.units``

        """
        if key in self.SEGY_TIME_UNITS:
            scl = float(units.__getattribute__(self.SEGY_TIME_UNITS[key])/\
                        units.__getattribute__(self.PARAM['time_units']))
        elif key in self.SEGY_DISTANCE_UNITS:
            scl = float(units.__getattribute__(self.SEGY_DISTANCE_UNITS[key])/\
                        units.__getattribute__(self.PARAM['distance_units']))
        else:
            scl = 1

        return value * scl

    def _get_header_alias(self,key):
        """
        Finds the header attribute name for an alias.  If none exists, returns
        input ``key``.

        :param key: keyword ``str`` in ``HEADER_ALIASES``
        """
        try:
            return self.HEADER_ALIASES[key.lower()]
        except KeyError:
            return key

    def _iterable(self,values):
        """
        Ensures that a variable is iterable.
        """
        try:
            any_item = iter(values)
            return values
        except TypeError:
            return [values]

    def _typeset(self,string):
        """
        Typesets header attribute names for use in labels.
        """
        return (string[0].upper() + string[1:]).replace('_',' ')


class SEGYPlotItems():
    """
    Conveince class for managing plot items (artists).
    """
    # XXX depreciated

    def __init__(self):
        """
        Initializes all plot item members to None.
        """
        self.wiggle_traces = None
        self.wiggle_positive_fills = None
        self.wiggle_negative_fills = None
        self.picks = None

 
if __name__ == "__main__":
    import doctest
    doctest.testmod()

