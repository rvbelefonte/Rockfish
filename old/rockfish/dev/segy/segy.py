"""
Internal handling of SEG-Y data.
"""

import copy
from obspy.segy.segy import SEGYTrace,\
                            SEGYError, SEGYTraceHeaderTooSmallError,\
                            SEGYTraceReadingError, SEGYWritingError
from obspy.segy.segy import SEGYFile as obspySEGYFile

from obspy.segy.header import ENDIAN, DATA_SAMPLE_FORMAT_UNPACK_FUNCTIONS, \
    BINARY_FILE_HEADER_FORMAT, DATA_SAMPLE_FORMAT_PACK_FUNCTIONS, \
    TRACE_HEADER_FORMAT, DATA_SAMPLE_FORMAT_SAMPLE_SIZE, TRACE_HEADER_KEYS
from rockfish.signals import gains
from rockfish.segy.fft import SEGYFFT
from rockfish.segy.timeshifts import SEGYTimeshifts

from rockfish.plotting.plotters import SEGYPlotter
from rockfish.signals.filters import SEGYFilters
from rockfish.sorting.trace_sorting import SEGYSorting
import matplotlib.pyplot as plt
import numpy as np

class SEGYGainRemoveError(SEGYError):
    """
    Raised if attempting to remove non-existant gain function.
    """
    pass

class SEGYTraceHeaderScalingError(SEGYError):
    """
    Raised if attempting to scale/unscale already scaled/unscaled attributes.
    """
    pass

class SEGYTraceHeaderDatetimeError(SEGYError):
    """
    Raised if building a ``datetime`` object from header shot time fails.
    """
    pass

class SEGYFile(obspySEGYFile, SEGYFilters, SEGYFFT, SEGYTimeshifts, SEGYSorting):
    """
    Class that handles reading, writing, plotting, and processing of SEG-Y data.

    .. note:: This class is an extended version of
        :class:`obspy.segy.segy.SEGYFile`. 
    """
    def __init__(self, file=None, endian=None, textual_header_encoding=None,
                 unpack_headers=False, headonly=False, unpack_data=False, 
                 scale_headers=True, computed_headers=True): 
        """
        Class that internally handles SEG Y files.

        :param file: A file like object with the file pointer set at the
            beginning of the SEG Y file. If file is None, an empty SEGYFile
            object will be initialized.
        :param endian: The endianness of the file. If None, autodetection will
            be used.
        :param textual_header_encoding: The encoding of the textual header.
            Either 'EBCDIC', 'ASCII' or None. If it is None, autodetection will
            be attempted. If it is None and file is also None, it will default
            to 'ASCII'.
        :param unpack_headers: Bool. Determines whether or not all headers will
            be unpacked during reading the file. Has a huge impact on the
            memory usage and the performance. They can be unpacked on-the-fly
            after being read. Defaults to False.
        :param headonly: Bool. Determines whether or not the actual data
            records will be read and unpacked. Has a huge impact on memory
            usage. Data can be read and unpacked on-the-fly after reading the
            file. Defaults to False.
        :param unpack_data: Bool. Determines whether or not the actual data
            records will be read, unpacked, and loaded into memory. Has a 
            huge impact on memory usage. Data can be read and unpacked 
            on-the-fly after reading the file. Defaults to False.
        :param scale_headers: Bool.  Determines whether or not to create
            real-valued coordinate and elevation trace-header attributes.
            Defaults to True.
        :param computed_headers: Bool. Determines whether or not to create
            computed header properties for commonly-calculated values.  
            Default is True.
        """
        if isinstance(file, SEGYFile):
            # Create a new copy of a SEGYFile instance
            self._createEmptySEGYFileObject()
            self.copy(file, headonly=headonly)
        else:
            # Open a new file or create an empty SEGYFile instance
            obspySEGYFile.__init__(self,file,endian=endian,
                    textual_header_encoding=textual_header_encoding,
                    unpack_headers=unpack_headers, headonly=headonly,
                    unpack_data=unpack_data, scale_headers=scale_headers,
                    computed_headers=computed_headers)
                                    
        # Connect to pick database
        # TODO do we want this here for convience?

    def copy(self, sgy, headonly=False):
        """
        Copies a ``SEGYFile`` object.

        :param sgy: ``SEGYFile`` to copy headers and data from.
        :param headonly: If ``True``, only copies the binary and textural
            file headers, ignoring traces.
        """

        self.textual_file_header = copy.copy(sgy.textual_file_header)
        self.binary_file_header = copy.deepcopy(sgy.binary_file_header)
        self.endian = copy.copy(sgy.endian)
        self.textual_header_encoding = copy.copy(sgy.textual_header_encoding)
         
        if(not headonly):
            self.traces = copy.deepcopy(sgy.traces)
        else:
            self.traces = []

    def gain(self, apply=True, type=None,
             method=None, window_size=None, window_length=None,
             desired_rms=1):
        """
        Calculates and applies gains to the data.
        """
        if apply:
            if type is 'agc':
                self._agc(method, window_size=window_size,
                          window_length=window_length, 
                          desired_rms=desired_rms)
            elif type is 'balance':
                self._balance(window_size)
            else:
                raise ValueError("Invalid gain type '%s'" %type)
        else:
            if not type:
                self._remove_gain('all')
            else:
                self._remove_gain(type)

    def plot_wiggles(self, sphinx=None, negative_fills=False,
                     positive_fills=True, wiggle_traces=False):
        """
        Plot trace wiggles.
        
        :param negative_fills: Optional. ``bool``.  If ``True``, draws
            negtive wiggle fills.  Default is ``False``.
        :param positive_fills: Optional. ``bool``.  If ``True``, draws
            positive wiggle fills.  Default is ``True``.
        :param wiggle_traces: Optional. ``bool``.  If ``True``, draws wiggle
            traces.  Default is ``False``.
        :param sphinx: ``bool``.  If ``True``, runs
            :meth:`matplotlib.pyplot.draw` so that a plot is generated for 
            inclusion in the Sphinx documentation.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        splt = SEGYPlotter(ax, self)
        splt.plot_wiggles(negative_fills=negative_fills,
                          positive_fills=positive_fills,
                          wiggle_traces=wiggle_traces)
        if sphinx:
            plt.draw()
        else:
            plt.show()

    def plot_fk_spectrum(self, traces=None, axes=None, log10=True, shift=True,
                         sphinx=False):
        """
        Plot the frequency-wavenumber (f-k) spectrum of data.

        :param traces: Traces to plot f-k spectrum for.  Default is to plot
            spectrum for all traces.
        :param axes: :class:`matplotlib.axes.Axes` to plot into.  Default is to
            create and show a new plot.
        :param shift: ``bool``. If ``True``, runs :meth:`numpy.fft.fftshift` on
            the transformed data before plotting.  This places low-valued
            frequencies in the center of the plot.  Default is ``True``.
        :param log10: ``bool``. If ``True``, takes :meth:`numpy.log10` of 
            transformed data before plotting.  Default is ``True``.
        :param sphinx: ``bool``.  If ``True``, runs
            :meth:`matplotlib.pyplot.draw` so that a plot is generated for 
            inclusion in the Sphinx documentation.
        """

        if axes:
            ax = axes
        else:
            fig = plt.figure()
            ax = fig.add_subplot(111)

        if not traces:
            traces = self.traces

        F = np.abs(self.fft2(traces=traces,inplace=False))**2
        if shift:
            F = np.fft.fftshift(F)
        if log10:
            F = np.log10(F)

        ax.imshow(F.transpose())

        # show the plot if this is a new axis
        if sphinx or axes:
            plt.draw()
        else:
            plt.show()

    # Private methods
    def _agc(self, method=None, window_length=None, window_size=None,
             desired_rms=None):
        """
        Calculates and applies agc to the data.
        """
        for tr in self.traces:
            if not hasattr(tr,'GAINS'):
                tr.GAINS = {}
            if window_length and not window_size:
                dt = tr.header.sample_interval_in_ms_for_this_trace
                window_size = window_length/dt
                assert window_size > 0, 'window_size must be greater than 0 '\
                                        + '(window_size = window_length/dt ='\
                                        + ' %s/%s = %s)' % (window_length,
                                                            dt,window_size)
            assert window_size > 0, 'window_size must be greater than 0'
            if window_size > len(tr.data):
                window_size = len(tr.data)

            tr.GAINS['agc'] = gains.agc(tr.data,method=method,
                                    window_size=window_size,
                                    desired_rms=desired_rms)
            tr.data = tr.GAINS['agc'] * tr.data

    def _balance(self, window_size):
        """
        Calculates and applies a trace balance to the data.
        """
        if not hassattr(self,'data'):
            self.grid_data()

    def _remove_gain(self,type):
        """
        Removes a previously applied gain from the data.

        :parameter type: Name of gain to remove.
        """
        for tr in self.traces:
            if not hasattr(tr,'GAINS'):
                raise SEGYGainRemoveError('No gains exist for trace.')
            if type == 'all':
                types = [k for k in tr.GAINS]
            else:
                types = [type]
            for k in types:
                try:
                    tr.data = tr.data/tr.GAINS.pop(k)
                except KeyError:
                    msg = "No '%s' gain exists for trace." % k
                    raise KeyError(msg)

def readSEGY(file, endian=None, textual_header_encoding=None,
             unpack_headers=False, headonly=False, unpack_data=False,
             scale_headers=True, computed_headers=True):
    """
    Reads a SEG Y file and returns a SEGYFile object.

    :param file: Open file like object or a string which will be assumed to be
        a filename.
    :param endian: String that determines the endianness of the file. Either
        '>' for big endian or '<' for little endian. If it is None, obspy.segy
        will try to autodetect the endianness. The endianness is always valid
        for the whole file.
    :param textual_header_encoding: The encoding of the textual header.
        Either 'EBCDIC', 'ASCII' or None. If it is None, autodetection will
        be attempted.
    :param unpack_headers: Bool. Determines whether or not all headers will be
        unpacked during reading the file. Has a huge impact on the memory usage
        and the performance. They can be unpacked on-the-fly after being read.
        Defaults to False.
    :param headonly: Bool. Determines whether or not the actual data
        records will be read. Useful if one is just interested in the
        headers. Overrides unpack_data. Defaults to False.
    :param unpack_data: Bool. Determines whether or not the actual data
        records will be read, unpacked, and loaded into memory. Has a 
        huge impact on memory usage. Data can be read and unpacked 
        on-the-fly after reading the file. Defaults to True.
    :param scale_headers: Bool.  Determines whether or not to create
        real-valued coordinate and elevation trace-header attributes.
        Defaults to True.
    :param computed_headers: Bool. Determines whether or not to create
        computed header properties for commonly-calculated values.  
        Defaults to True.
    """
    # Open the file if it is not a file like object.
    if not hasattr(file, 'read') or not hasattr(file, 'tell') or not \
        hasattr(file, 'seek'):
        with open(file, 'rb') as open_file:
            return _readSEGY(open_file, endian=endian,
                             textual_header_encoding=textual_header_encoding,
                             unpack_headers=unpack_headers, headonly=headonly,
                             unpack_data=unpack_data,
                             scale_headers=scale_headers,
                             computed_headers=computed_headers)
    # Otherwise just read it.
    return _readSEGY(file, endian=endian,
                     textual_header_encoding=textual_header_encoding,
                     unpack_headers=unpack_headers, headonly=headonly,
                     unpack_data=unpack_data, scale_headers=scale_headers,
                     computed_headers=computed_headers)

def _readSEGY(file, endian=None, textual_header_encoding=None,
              unpack_headers=False, headonly=False,
              unpack_data=False, scale_headers=True, computed_headers=True):
    """
    Reads on open file object and returns a SEGYFile object.

    :param file: Open file like object.
    :param endian: String that determines the endianness of the file. Either
        '>' for big endian or '<' for little endian. If it is None, obspy.segy
        will try to autodetect the endianness. The endianness is always valid
        for the whole file.
    :param textual_header_encoding: The encoding of the textual header.
        Either 'EBCDIC', 'ASCII' or None. If it is None, autodetection will
        be attempted.
    :param unpack_headers: Bool. Determines whether or not all headers will be
        unpacked during reading the file. Has a huge impact on the memory usage
        and the performance. They can be unpacked on-the-fly after being read.
        Defaults to False.
    :param headonly: Bool. Determines whether or not the actual data
        records will be read. Useful if one is just interested in the
        headers. Overrides unpack_data. Defaults to False.
    :param unpack_data: Bool. Determines whether or not the actual data
        records will be read, unpacked, and loaded into memory. Has a 
        huge impact on memory usage. Data can be read and unpacked 
        on-the-fly after reading the file. Defaults to True.
    :param scale_headers: Bool.  Determines whether or not to create
        real-valued coordinate and elevation trace-header attributes.
        Defaults to False.
    :param computed_headers: Bool. Determines whether or not to create
        computed header properties for commonly-calculated values.  
        Defaults to True.
    """
    return SEGYFile(file, endian=endian,
                    textual_header_encoding=textual_header_encoding,
                    unpack_headers=unpack_headers, headonly=headonly,
                    unpack_data=unpack_data,
                    scale_headers=scale_headers,
                    computed_headers=computed_headers)


