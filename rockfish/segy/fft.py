"""
Wrappers for calculating FFTs and IFFTs of SEG-Y data.
"""

import matplotlib.pyplot as plt
import numpy as np
from rockfish.segy.util import SEGYUtils

class SEGYFFT(SEGYUtils):
    """
    Conveince class for calculating FFT of data in :class:`SEGYFile` objects.
    """
    def fft(self, traces=None, inplace=True):
        """
        Discrete Fourier transform of the data in time.

        :param traces: Optional. List of ``SEGYTrace`` objects with data to
            transform. Default is transform all traces.
        :param inplace: Optional.  Determines if the data are transformed in
            place or if the transformed data are returned.  Default is to
            transform the data inplace.
        """
        if not traces:
            traces = self.traces
        F = np.fft.fft(self.traces2grid(traces))
        if inplace:
            self.grid2traces(F, traces=traces)
        else:
            return F

    def fft2(self, traces=None, inplace=True):
        """
        Discrete Fourier transform of the data in two dimensions.

        :param traces: Optional. List of ``SEGYTrace`` objects with data to
            transform. Default is transform all traces.
        :param inplace: Optional.  Determines if the data are transformed in
            place or if the transformed data are returned.  Default is to
            transform the data inplace.
        """
        if not traces:
            traces = self.traces
        F = np.fft.fft2(self.traces2grid(traces))
        if inplace:
            self.grid2traces(F)
        else:
            return F

    def ifft2(self, traces=None, inplace=True):
        """
        Inverse discrete Fourier transform of the data in two dimensions.

        :param traces: Optional. List of ``SEGYTrace`` objects with data to
            transform. Default is transform all traces.
        :param inplace: Optional.  Determines if the data are transformed in
            place or if the transformed data are returned.  Default is to
            transform the data inplace.
        """
        if not traces:
            traces = self.traces
        f = np.fft.ifft2(self.traces2grid(traces))
        if inplace:
            self.grid2traces(np.abs(f))
        else:
            return f

    def fftfreq(self):
        """
        Return the sample frequencies for the Discrete Fourier Transform of the
        data in time.
        """
        dt_sec = self.binary_file_header.sample_interval_in_microseconds \
                 * 1.e-6
        npts = self.binary_file_header.number_of_samples_per_data_trace
        return np.fft.fftfreq(npts, d=dt_sec)

