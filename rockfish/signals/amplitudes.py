"""
Compute amplitude statistics
"""

def rms(data):
    """
    Computes the RMS amplitude of data.

    :param data: ``list`` of data values to compute rms for.
    :return: RMS value 
    
    >>> import numpy as np
    >>> a = np.array([1,2,3,4,5])
    >>> print rms(a)
    7.4161984871
    """
    return np.sqrt(np.sum(np.power(data, 2)))

def windowed_rms(data, window_size):
    """
    Computes the moving-window RMS amplitude of data.

    :param data: ``list`` of data values to compute rms for.
    :param window_size: Length of window to compute rms for in number of
        samples.
    :return: ``numpy.nparray`` with ``len(data)`` RMS values

    >>> import numpy as np
    >>> a = np.array([1,2,3,4,5])
    >>> print windowed_rms(a,2)
    [ 1.          1.58113883  2.54950976  3.53553391  4.52769257]
    """
    data2 = np.power(data,2)
    return np.sqrt(_moving_average(data2,window_size))

def moving_average(data, window_size):
    """
    Computes the windowed mean amplitude of data.
    
    :param data: ``list`` of data values to compute windowed mean for.
    :param window_size: Length of window to compute mean for.
    :return: ``numpy.nparray`` with ``len(data)`` moving-average values

    >>> import numpy as np
    >>> a = np.array([2,2,4,4])
    >>> print moving_average(a,2)
    [ 2.  2.  3.  4.]
    >>> print moving_average(a,3)
    [ 2.          2.          2.66666667  3.33333333]
    """
    extended_data = np.hstack([[data[0]] * (window_size - 1), data])
    window = np.repeat(1.0, window_size) / window_size
    return np.convolve(extended_data, window)[window_size-1:-(window_size-1)]

def signal_to_noise(data, i0=None, i1=None, window_size=10):
    """
    Compute signal-to-noise ratio.

    :param data: ``list`` of data values to compute rms for.
    :param window_size: Optional. Length of window to for computing rms in
        number of samples.  Default is ``10``.
    :param i1: Optional. Index of sample to compute SNR for. Default is to
        compute SNR at each sample.
    :param i0: Optional. Index of the center of the reference window. Default
        is to use the 
    """
    # TODO
    raise NotImplementedError
