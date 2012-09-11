
import matplotlib.pyplot as plt
import numpy as np

class SEGYFFT():

    def fft(self,traces=None):
        """
        Discrete Fourier transform of the data in time.

        :param traces: List of ``SEGYTrace`` objects with data to transform.
            Default is transform all traces.
        """
        if not traces:
            traces = self.traces
        return np.fft.fft(self.traces2grid(traces))

    def fft2(self,traces=None,inplace=True):
        """
        Discrete Fourier transform of the data in two dimensions.

        :param traces: List of ``SEGYTrace`` objects with data to transform.
            Default is transform all traces.
        """
        if not traces:
            traces = self.traces
        F = np.fft.fft2(self.traces2grid(traces))
        if inplace:
            self.grid2traces(F)
        else:
            return F

    def ifft2(self,traces=None,inplace=True):
        """
        Inverse discrete Fourier transform of the data in two dimensions.

        :param traces: List of ``SEGYTrace`` objects with data to transform.
            Default is transform all traces.
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
        return np.fft.fftfreq(npts,d=dt_sec)

    def traces2grid(self,traces=None):
        """
        Creates a 2-dimensional numpy array of the data in ``traces.data``.

        .. warning:: Assumes that traces are all of a uniform length.
        
        :param traces: List of ``SEGYTrace`` objects with data to include in the
            array.
        """
        if not traces:
            traces = self.traces
        ntrc = len(traces)
        ntime = len(traces[0].data)
        data = np.empty([ntrc,ntime])
        for i,tr in enumerate(traces):
            data[i] = tr.data

        return data

    def grid2traces(self,data,traces=None):
        """
        Transfers a 2-dimensional numpy array of the data to ``traces.data``.

        :param traces: List of ``SEGYTrace`` objects with data to include in
            the array.
        """
        if not traces:
            traces = self.traces
        for i,tr in enumerate(traces):
            self.traces[i].data = data[i]

    def timeshift(self, dtimes, traces=None):
        """
        Timeshift data by phase shifting in the frequency domain.

        :param dtimes: List of the values for the timeshift in milliseconds 
            for each trace.
        :param traces: List of ``SEGYTrace`` objects with data to timeshift.
        """
        for i,tr in enumerate(traces):
            if len(dtimes)==1:
                dt = dtimes[0]
            else:
                dt = dtimes[i]
            F = np.fft.fft(tr.data) * np.exp(-1j*np.pi*f)
            tr.data = np.real(np.fft.ifft(F))

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
