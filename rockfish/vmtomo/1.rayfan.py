"""
Support for working with VM Tomography binary rayfan files.
"""
import os
from struct import unpack
import logging

DEFAULT_RAYFAN_VERSION = 2
logging.debug('Set DEFAULT_RAYFAN_VERSION=%i', DEFAULT_RAYFAN_VERSION)

# XXX 
logging.basicConfig(level=logging.DEBUG)

class RayfanError(Exception):
    """
    Raised if there is a problem working with rayfan(s). 
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

class Rayfan(object):
    """
    Class for working with a single rayfan.
    
    A rayfan is a group of rays with a common start_point_id (i.e., source
    or receiver).
    """
    def __init__(self, file=None, start_point_id=None, endian='@',
                 rayfan_version=None):
        if file is not None:
            # Read data from file
            self.read(file=file, start_point_id=start_point_id, endian=endian)
        else:
            # Create empty instance
            self.start_point_id = None
            self.nrays = 0
            self.static_correction = 0.
            self.end_point_ids = []
            self.event_ids = []
            self.event_subids = []
            self.travel_times = []
            self.pick_times = []
            self.pick_errors = []
            self.raypaths = []

    def read(self, file, start_point_id=None, endian='@'): 
        """
        Read data for a single rayfan.

        :param file:  A file-like object with the file pointer set at the
            begining of a rayfan within the ray file.
        :param start_point_id: Optional.  If given, search the file for a
            specific rayfan, returning ``None`` if the rayfan is not found.
            Default is to read the next rayfan in the file.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        """
        # Make sure there is an open file-like object
        if not hasattr(file, 'read') or not hasattr(file, 'tell') or not \
            hasattr(file, 'seek'):
            msg = 'file={:} is not a file-like object'.format(type(file))
            raise TypeError(msg)
        # Get the total filesize
        filesize = os.fstat(file.fileno()).st_size
        # Get the number of rayfans and the format version number
        pos = file.tell()
        file.seek(0)
        fmt = '{:}i'.format(endian)
        nrayfans = unpack(fmt, file.read(4))
        offset = 4
        if nrayfans < 1:
            # this is a version number, keep going
            rayfan_version = -nrayfans
            nrayfans = unpack(fmt, file.read(4))
            offset += 4
        else:
            rayfan_version = 1
        # Position the file to the begining of the first rayfan to read
        if start_point_id is None:
            file.seek(pos+offset)
        else:
            file.seek(offset)
        # Read the data
        self._read_rayfan(file, nrayfans, rayfan_version, filesize, 
                          start_point_id=start_point_id, endian=endian)

    def _read_rayfan(self, file, nrayfans, rayfan_version, filesize,
                     start_point_id=None, endian='@'):
        """
        Read data for a single rayfan.

        :param file:  A file-like object with the file pointer set at the
            begining of a rayfan within the ray file.
        :param nrayfans: The total number of rayfans in the file.
            is to the read the number of rayfans from the begining of the file.
        :param rayfan_version: Optional. Sets the version number of the
            rayfan file format. Default is to determine the version from
            the file.
        :param filesize: The total filesize of the file. Default is
            to find the filesize.
        :param start_point_id: Optional.  If given, search the file for a
            specific rayfan. Raises a :class:``RayfanNotFoundError`` if the rayfan
            is not found. Default is to read the next rayfan in the file.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order.
        """
        # Read header for an indiviudal rayfan
        fmt = '{:}i'.format(endian)
        _start_point_id = unpack(fmt, file.read(4))[0]
        nrays = unpack(fmt, file.read(4))[0]
        nsize = unpack(fmt, file.read(4))[0]
        print 'At rayfan for start_point_id = %i' %_start_point_id
        # Make sure there is enough data left to read
        pos = file.tell()
        data_left = filesize - pos
        data_needed = 7*nrays + 3*nsize
        if data_needed > data_left or data_needed < 0:
            msg = '''
                  Too little data in the file left to unpack. This is most
                  likely caused by an incorrect size in the rayfan header.
                  '''.strip()
            raise RayfanReadingError(msg)
        # Advance the file and try to read the next rayfan
        # if we are searching for a specific rayfan
        if start_point_id is not None and \
            _start_point_id is not start_point_id:
            file.seek(data_needed, 1)
            try:
                # read recursively
                self._read_rayfan(file, nrayfans, rayfan_version, filesize, 
                    start_point_id=start_point_id, endian=endian)
            except RayfanReadingError:
                msg = 'Could not find a rayfan with start_point_id = {:}'\
                        .format(start_point_id)
                raise RayfanNotFoundError(msg)
        self.start_point_id = _start_point_id
        # Read rayfan data
        # Static correction
        if rayfan_version > 1:
            fmt = '{:}f'.format(endian)
            self.static_correction = unpack(fmt, file.read(4))
        else:
            self.static_correction = 0.
        # ID arrays and sizes
        fmt = '{:}'.format(endian) + 'i'*nrays
        self.end_point_ids = unpack(fmt, file.read(4*nrays))
        self.event_ids = unpack(fmt, file.read(4*nrays))
        self.event_subids = unpack(fmt, file.read(4*nrays))
        _ = unpack(fmt, file.read(4*nrays)) # raypath length
        # Picks, travel-times, and errors
        fmt = '{:}'.format(endian) + 'f'*nrays
        self.pick_times = unpack(fmt, file.read(4*nrays))
        self.travel_times = unpack(fmt, file.read(4*nrays))
        self.pick_errors = unpack(fmt, file.read(4*nrays))
        # Actual ray path coordinates
        fmt = '{:}'.format(endian) + 'f'*3*nsize
        self.raypaths = unpack(fmt, file.read(4*3*nsize))

