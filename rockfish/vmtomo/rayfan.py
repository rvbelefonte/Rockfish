"""
Support for working with VM Tomography binary rayfan files.
"""
import os
from struct import unpack
import logging
import numpy as np

DEFAULT_RAYFAN_VERSION = 2

class RayfanError(Exception):
    """
    Base exception class for the Rayfan class. 
    """
    pass

class RayfanReadingError(RayfanError):
    """
    Raised if there is a problem reading a rayfan from the disk.
    """
    pass

class RayfanNotFoundError(RayfanError):
    """
    Raised if a rayfan is not found in the ray file.
    """
    pass

class RayfanFile(object):
    """
    Class for working with VM Tomography rayfan files.
    """
    def __init__(self, file=None, endian='@'):
        """
        Class for working with VM Tomography rayfan files.

        :param file: An open file-like object or a string which is
            assumed to be a filename.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        """
        if file is not None:
            self.read(file, endian=endian)
        else:
            self.file = None
            self.rayfans = []

    def read(self, file, endian='@'):
        """
        Read rayfan data from a rayfan file.

        :param file: An open file-like object or a string which is
            assumed to be a filename.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        """
        if not hasattr(file, 'read') or not hasattr(file, 'tell') or not \
            hasattr(file, 'seek'):
            file = open(file, 'rb')
        else:
            file.seek(0)
        self.file = file
        self._read(file, endian=endian)

    def _read(self, file, endian='@'):
        """
        Read rayfan data from a rayfan file.

        :param file: An open file-like object with the file pointer set at the
            beginning of a rayfan file. 
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        """
        # Read file header
        fmt = '{:}i'.format(endian)
        nrayfans = unpack(fmt, file.read(4))[0]
        if nrayfans < 0:
            rayfan_version = -nrayfans
            nrayfans = unpack(fmt, file.read(4))[0]
        else:
            rayfan_version = 1
        # Read the individual rayfans
        self.rayfans = []
        for i in range(0, 1): #nrayfans):
            self.rayfans.append(Rayfan(file, endian=endian,
                                       rayfan_version=rayfan_version))
        
class Rayfan(object):
    """
    Class for working with a single rayfan.
    """
    def __init__(self, file, endian='@', rayfan_version=DEFAULT_RAYFAN_VERSION):
        """
        Class for handling an individual rayfan.

        :param file: An open file-like object with the file pointer set at the
            beginning of a rayfan file. 
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        :param rayfan_version: Optional. Sets the version number of the
            rayfan file format. Default is version 2.
        """
        self.read(file, endian=endian, rayfan_version=rayfan_version)

    def read(self, file, endian='@', rayfan_version=DEFAULT_RAYFAN_VERSION):
        """
        Read data for a single rayfan.

        :param file: An open file-like object with the file pointer set at the
            beginning of a rayfan file. 
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        :param rayfan_version: Optional. Sets the version number of the
            rayfan file format. Default is version 2.
        """
        filesize = os.fstat(file.fileno()).st_size
        # read the rayfan header information
        fmt = '{:}i'.format(endian)
        self.start_point_id = unpack(fmt, file.read(4))[0]
        nrays = unpack(fmt, file.read(4))[0]
        nsize = unpack(fmt, file.read(4))[0]
        # make sure the expected amount of data exist
        pos = file.tell()
        data_left = filesize - pos
        data_needed = 7*nrays + 3*nsize
        print filesize, pos, nrays, nsize, data_left, data_needed
        if data_needed > data_left or data_needed < 0:
            msg = '''
                  Too little data in the file left to unpack. This is most
                  likely caused by an incorrect size in the rayfan header.
                  '''.strip()
            raise RayfanReadingError(msg)
        # Static correction
        if rayfan_version > 1:
            fmt = '{:}f'.format(endian)
            self.static_correction = unpack(fmt, file.read(4))[0]
        else:
            self.static_correction = 0.
        # ID arrays and sizes
        fmt = '{:}'.format(endian) + 'i'*nrays
        self.end_point_ids = unpack(fmt, file.read(4*nrays))
        self.event_ids = unpack(fmt, file.read(4*nrays))
        self.event_subids = unpack(fmt, file.read(4*nrays))
        lens = unpack(fmt, file.read(4*nrays)) # raypath length
        # Picks, travel-times, and errors
        fmt = '{:}'.format(endian) + 'f'*nrays
        self.pick_times = unpack(fmt, file.read(4*nrays))
        self.travel_times = unpack(fmt, file.read(4*nrays))
        self.pick_errors = unpack(fmt, file.read(4*nrays))
        # Actual ray path coordinates
        self.paths = [] 
        for i in range(0, nrays):
            fmt = '{:}'.format(endian) + 'f'*3*lens[i]
            self.paths.append(np.reshape(
                unpack(fmt,file.read(4*3*lens[i])),
                (lens[i],3)))
        # Endpoint coordinates
        self.endpoints = []
        for path in self.paths:
            if len(path) > 0:
                self.endpoints.append(path[0])
            else:
                self.endpoints.append([None, None, None])
