"""
Compute amplitude statistics
"""
import numpy as np

def rms(data):
    """
    Computes the RMS amplitude of data.

    :param data: ``list`` of data values to compute rms for.
    :return: RMS value 
    
    >>> import numpy as np
    >>> a = np.array([1,2,3,4,5])
    >>> print rms(a)
    3.31662479036
    """
    return np.sqrt(np.mean(np.power(data, 2)))

def windowed_rms(data, window_size):
    """
    Computes the moving-window RMS amplitude of data.

    :param data: ``list`` of data values to compute rms for.
    :param window_size: Length of window to compute rms for in number of
        samples.
    :return: ``numpy.nparray`` with ``len(data)`` RMS values

    >>> import numpy as np
    >>> a = np.array([1, 2, 3, 4, 5])
    >>> print windowed_rms(a, 2)
    [ 1.          1.58113883  2.54950976  3.53553391  4.52769257]
    """
    data2 = np.power(data,2)
    return np.sqrt(moving_average(data2, window_size))

def moving_average(data, window_size):
    """
    Computes the windowed mean amplitude of data.
    
    :param data: ``list`` of data values to compute windowed mean for.
    :param window_size: Length of window to compute mean for.
    :return: ``numpy.nparray`` with ``len(data)`` moving-average values

    >>> import numpy as np
    >>> a = np.array([2, 2, 4, 4])
    >>> print moving_average(a, 2)
    [ 2.  2.  3.  4.]
    >>> print moving_average(a, 3)
    [ 2.          2.          2.66666667  3.33333333]
    """
    extended_data = np.hstack([[data[0]] * (window_size - 1), data])
    window = np.repeat(1.0, window_size) / window_size
    return np.convolve(extended_data, window)\
            [window_size - 1: - (window_size - 1)]

def get_window_idx(i0, width, align='center'):
    """
    Returns a set of indices for a window.

    :param i0: Index of the window center/left/right.
    :param width: Width of the window.
    :param align: Optional. Alignment of the window. Options are: 'center',
        'left', or 'right'. Default is 'center'.
    """
    if align == 'center':
        d = np.floor_divide(width, 2.)
        j = np.arange(int(i0 - d), int(i0 + d + 1))
        if np.mod(width, 2.) == 0:
            j = j[1:]
    elif align == 'left':
        j = np.arange(i0, i0 + width + 1)
    elif align == 'right':
        j = np.arange(i0 - width + 1, i0 + 1)
    else:
        raise ValueError("Unknown value align='{:}'.".format(align))
    return j

def snr(data, i=None, iref=None, window_size=10, 
                    ref_window_size=None, align='center'):
    """
    Compute signal-to-noise ratio (SNR).

    :param data: ``list`` of data values to compute RMS for.
    :param window_size: Optional. Length of window to for computing RMS in
        number of samples.  Default is ``10``.
    :param i: Optional. Index of sample to compute SNR for. Default is to
        compute SNR at each sample.
    :param iref: Optional. Index of sample to compute reference RMS for.
        Default is to use the RMS of all the data.
    :param ref_window_size: Optional. Window size for computing the reference
        RMS value if iref is given. Default is to use the size set by
        ``window_size``.
    :param align: Optional. Alignment of the fixed windows. Options are:
        'center', 'left', or 'right'. Default is 'center'.
    """
    # Calculate reference RMS
    if iref is None:
        # take rms of all data
        rms0 = rms(data)
    else:
        # take RMS within a window
        if ref_window_size is None:
            ref_window_size = window_size
        j = get_window_idx(iref, ref_window_size, align=align)
        rms0 = rms(data[j])
    # Calculate RMS
    if i is None:
        # Calculate RMS in moving windows at each data point
        rms1 = windowed_rms(data, window_size)
    else:
        # Calculate RMS in a single window
        j = get_window_idx(i, window_size, align=align)
        rms1 = rms(data[j])
    # Return SNR
    return rms1 / rms0

if __name__ == "__main__":
    import doctest
    doctest.testmod()
