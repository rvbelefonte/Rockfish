
from rockfish.core.messaging import ProgressPercentTicker
from obspy.signal import filter
import numpy as np

class SEGYFilters():

    def bandpass(self, freqmin, freqmax, corners=4, zerophase=False, traces=None):
        """
        Butterworth-Bandpass Filter of the data.

        Filter data from ``freqmin`` to ``freqmax`` using ``corners`` corners.

        :param freqmin: Pass band low corner frequency in Hz.
        :param freqmax: Pass band high corner frequency in Hz.
        :param corners: Filter corners. Note: This is twice the value of PITSA's
            filter sections
        :param zerophase: If True, apply filter once forwards and once backwards.
            This results in twice the number of corners but zero phase shift in
            the resulting filtered trace.
        :param traces: List of ``SEGYTrace`` objects with data to operate on.
            Default is to operate on all traces.
        """
        if not traces:
            traces = self.traces
        pb = ProgressPercentTicker("Bandpass filtering %i traces..." \
                                   % len(traces), len(traces))
        for i,tr in enumerate(traces):
            df = 1./(tr.header.sample_interval_in_ms_for_this_trace/1.e6)
            tr.data = filter.bandpass(tr.data, freqmin, freqmax, df, 
                                      corners=corners, zerophase=zerophase)
            pb.update(i)
        pb.finish()


    def bandstop(self, freqmin, freqmax, corners=4, zerophase=False, traces=None):
        """
        Butterworth-Bandstop Filter of the data.

        Filter data removing data between frequencies ``freqmin`` and ``freqmax``
        using ``corners`` corners.

        :param freqmin: Stop band low corner frequency in Hz.
        :param freqmax: Stop band high corner frequency in Hz.
        :param corners: Filter corners. Note: This is twice the value of PITSA's
            filter sections
        :param zerophase: If True, apply filter once forwards and once backwards.
            This results in twice the number of corners but zero phase shift in
            the resulting filtered trace.
        :param traces: List of ``SEGYTrace`` objects with data to operate on.
            Default is to operate on all traces.
        """
        if not traces:
            traces = self.traces
        for tr in traces:
            df = 1./(tr.header.sample_interval_in_ms_for_this_trace/1.e6)
            tr.data = filter.bandstop(tr.data, freqmin, freqmax, df, 
                                      corners=corners, zerophase=zerophase)

    def lowpass(self, freq, corners=4, zerophase=False, traces=None):
        """
        Butterworth-Lowpass Filter of the data.

        Filter data removing data over certain frequency ``freq`` using ``corners``
        corners.

        :param freq: Filter corner frequency in Hz.
        :param corners: Filter corners. Note: This is twice the value of PITSA's
            filter sections
        :param zerophase: If True, apply filter once forwards and once backwards.
            This results in twice the number of corners but zero phase shift in
            the resulting filtered trace.
        :param traces: List of ``SEGYTrace`` objects with data to operate on.
            Default is to operate on all traces.
        """
        if not traces:
            traces = self.traces
        for tr in traces:
            df = 1./(tr.header.sample_interval_in_ms_for_this_trace/1.e6)
            tr.data = filter.lowpass(tr.data, freq, df, 
                                      corners=corners, zerophase=zerophase)

    def highpass(self, freq, corners=4, zerophase=False, traces=None):
        """
        Butterworth-Highpass Filter of the data.

        Filter data removing data below certain frequency ``freq`` using
        ``corners`` corners.

        :param freq: Filter corner frequency in Hz.
        :param corners: Filter corners. Note: This is twice the value of PITSA's
            filter sections
        :param zerophase: If True, apply filter once forwards and once backwards.
            This results in twice the number of corners but zero phase shift in
            the resulting filtered trace.
        :param traces: List of ``SEGYTrace`` objects with data to operate on.
            Default is to operate on all traces.
        """
        if not traces:
            traces = self.traces
        for tr in traces:
            df = 1./(tr.header.sample_interval_in_ms_for_this_trace/1.e6)
            tr.data = filter.highpass(tr.data, freq, df, 
                                      corners=corners, zerophase=zerophase)

    def envelope(self, traces=None):
        """
        Take the envelope of the data.
        
        :param traces: List of ``SEGYTrace`` objects with data to operate on.
            Default is to operate on all traces.

        Computes the envelope of the given function. The envelope is determined by
        adding the squared amplitudes of the function and it's Hilbert-Transform
        and then taking the square-root. (See [Kanasewich1981]_)
        The envelope at the start/end should not be taken too seriously.
        """
        if not traces:
            traces = self.traces
        for tr in traces:
            tr.data = filter.envelope(tr.data)

