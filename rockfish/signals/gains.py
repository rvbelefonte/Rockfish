"""
Routines to compute gain functions.
"""
import numpy as np
from rockfish.signals.amplitudes import rms, windowed_rms, moving_average

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


    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
