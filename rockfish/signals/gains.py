"""
Routines to compute gain functions.
"""

import numpy as np

def agc(data,method='rms',window_size=10,desired_rms=1):
    """
    Computes Automatic Gain Control (AGC) values.

    :param data: ``numpy.nparray`` of data to calculate gain for
    :param method: ``'rms'`` or ``'instantaneous'``
    :param window_size: Length of window in number of samples.  Default is
        ``10``.
    :param desired_rms: Root-mean-squared value of ``data * agc(data)``.
        Default is ``1``.
    :return: ``numpy.nparray`` of gain values
   
    >>> import numpy as np
    >>> a = np.array([1,2,3,4,5])
    >>> print agc(a,method='rms',window_size=2,desired_rms=2000)
    [ 2000.          1264.91106407   784.46454055   565.68542495   441.7261043 ]
    >>> print agc(a,method='instantaneous',window_size=2,desired_rms=2000)
    [ 2000.          1333.33333333   800.           571.42857143   444.44444444]
    """
    if method is 'rms':
        return _agc_rms(data,window_size,desired_rms)
    elif method is 'instantaneous':
        return _agc_instantaneous(data,window_size,desired_rms)
    else:
        raise ValueError("Invalid agc method '%s'" %method)

def _agc_rms(data,window_size,desired_rms):
    """
    Computes the RMS-amplitude AGC for data.
    
    :param data: ``list`` of data values to compute rms for.
    :param window_size: Length of window in number of samples.
    :param desired_rms: Root-mean-squared value of ``data * _agc_rms(data)``.
    :return: ``numpy.nparray`` with ``len(data)`` AGC values
    """
    return float(desired_rms)/_windowed_rms(data,window_size)

def _agc_instantaneous(data,window_size,desired_rms):
    """
    Computes the instantaneous-amplitude AGC for data.
    
    :param data: ``list`` of data values to compute rms for.
    :param window_size: Length of window in number of samples.
    :param desired_rms: Root-mean-squared value of ``data * 
        _agc_instantaneous(data)``.
    :return: ``numpy.nparray`` with ``len(data)`` AGC values
    """
    return float(desired_rms)/_moving_average(np.abs(data),window_size)

def _rms(data):
    """
    Computes the RMS amplitude of data.

    :param data: ``list`` of data values to compute rms for.
    :return: RMS value 
    
    >>> import numpy as np
    >>> a = np.array([1,2,3,4,5])
    >>> print _rms(a)
    7.4161984871
    """
    return np.sqrt(np.sum(np.power(data,2)))

def _windowed_rms(data,window_size):
    """
    Computes the moving-window RMS amplitude of data.

    :param data: ``list`` of data values to compute rms for.
    :param window_size: Length of window to compute rms for in number of
        samples.
    :return: ``numpy.nparray`` with ``len(data)`` RMS values

    >>> import numpy as np
    >>> a = np.array([1,2,3,4,5])
    >>> print _windowed_rms(a,2)
    [ 1.          1.58113883  2.54950976  3.53553391  4.52769257]
    """
    data2 = np.power(data,2)
    return np.sqrt(_moving_average(data2,window_size))

def _moving_average(data,window_size):
    """
    Computes the windowed mean amplitude of data.
    
    :param data: ``list`` of data values to compute windowed mean for.
    :param window_size: Length of window to compute mean for.
    :return: ``numpy.nparray`` with ``len(data)`` moving-average values

    >>> import numpy as np
    >>> a = np.array([2,2,4,4])
    >>> print _moving_average(a,2)
    [ 2.  2.  3.  4.]
    >>> print _moving_average(a,3)
    [ 2.          2.          2.66666667  3.33333333]
    """
    extended_data = np.hstack([[data[0]] * (window_size - 1), data])
    window = np.repeat(1.0, window_size) / window_size
    return np.convolve(extended_data, window)[window_size-1:-(window_size-1)]
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
