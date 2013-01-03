"""
Read/write data in OpendTect formats.
"""
import numpy as np


# XXX in development!
def read_2dh(filename):
    """
    Read data from a binary *.2dh file.

    :param filename: String filename of a 2D horizon file.
    """
    file = open(filename)
    # Skip the header
    for i in range(0,11):
        file.readline()
    # Read the data
    dat = file.readline()[1:-2]
    print dat

    # XXX test unpack
    print len(dat)
    _dat = np.fromstring(dat, dtype='float16')
    print _dat
    print _dat.byteswap()


