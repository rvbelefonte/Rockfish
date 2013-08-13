"""
Test suite for the amplitudes module.
"""
import os
import unittest
import numpy as np
from rockfish.signals import amplitudes


class amplitudesTestCase(unittest.TestCase):
    """
    Test cases for the amplitudes module.
    """
    def test_moving_average(self):
        """
        Should return the moving average of data.
        """
        a = [2, 2, 4, 4]
        m0 =  [ 2.,  2.,  3.,  4.]
        m1 = amplitudes.moving_average(a, 2)
        for i in range(0, len(m0)):
            self.assertEqual(m0[i], m1[i])

    def test_rms(self):
        """
        Should return the RMS value of a list of values.
        """
        rms0 = 3.31662479036 
        # should work on a list
        a = [1, 2, 3, 4, 5]
        self.assertAlmostEqual(rms0, amplitudes.rms(a), 10)
        # should work on a numpy.ndarray
        a = np.asarray(a)
        self.assertAlmostEqual(rms0, amplitudes.rms(a), 10)

    def test_windowed_rms(self):
        """
        Should return the windowed RMS of a data array.
        """
        rms0 = [ 1.0000000, 1.58113883, 2.54950976,  3.53553391,  4.52769257]
        # should work on a list
        a = [1, 2, 3, 4, 5]
        rms1 = amplitudes.windowed_rms(a, 2)
        for i in range(0, len(a)): 
            self.assertAlmostEqual(rms0[i], rms1[i])
        # should work on a numpy.ndarray
        a = np.asarray(a) 
        rms1 = amplitudes.windowed_rms(a, 2)
        for i in range(0, len(a)): 
            self.assertAlmostEqual(rms0[i], rms1[i])
        # rms of homogenous data should be the same
        a0 = 20.32411
        a = a0 * np.ones((100))
        for w in [1, 10, 100]:
            rms = amplitudes.windowed_rms(a, w)
            for _rms in rms:
                self.assertEqual(a0, _rms)

    def test_get_window_idx(self):
        """
        Should return indices for a window.
        """
        # Should raise a value error for unknown alignment directives
        with self.assertRaises(ValueError):
            amplitudes.get_window_idx(5, 2, align='bogus')
        # Should center window for align='center' and an odd window
        i = [4, 5, 6]
        j = amplitudes.get_window_idx(5, 3, align='center')
        for m, k in zip(i, j):
            self.assertEqual(m, k)
        # Should bump window to left for align='center' and an even window
        i = [5, 6]
        j = amplitudes.get_window_idx(5, 2, align='center')
        for m, k in zip(i, j):
            self.assertEqual(m, k)
        # Should left align window for align='left'
        i = [5, 6, 7]
        j = amplitudes.get_window_idx(5, 3, align='left')
        for m, k in zip(i, j):
            self.assertEqual(m, k)
        # Should right align window for align='right'
        i = [3, 4, 5]
        j = amplitudes.get_window_idx(5, 3, align='right')
        for m, k in zip(i, j):
            self.assertEqual(m, k)

    def test_snr(self):
        """
        Should return signal-to-noise ratios of data.
        """
        # Should return one for all data when amplitudes are identical
        a0 = 20.
        a = a0 * np.ones((100))
        snr = amplitudes.snr(a)
        for _snr in snr:
            self.assertEqual(1., _snr)
        # Should return one for all window sizes when amplitudes are identical
        i0 = 50
        for w in [1, 10, 20]:
            self.assertEqual(1., amplitudes.snr(a, i=i0, window_size=w))


def suite():
    return unittest.makeSuite(amplitudesTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
