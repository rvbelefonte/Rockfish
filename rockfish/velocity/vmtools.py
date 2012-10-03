"""
Routines for working with VM Tomography models.
"""
from struct import pack, unpack

class VM(object):
    """
    Class for working with VM Tomography models.
    """
    def __init__(self, file=None, endian='@'):
        """
        Class for working with VM Tomography models.

        :param file: Optional. An open file-like object or a string which is
            assumed to be a filename. Default is to create an empty instance of
            the VM class.
        :param endian: Optional. The endianness of the file. Default is
            to use machine's native byte order. 
        """
        self.ENDIAN = endian
        if file is not None:
            self.read(file)

    def read(self, file, endian='@'):
        """
        Read a VM model from a file on the disk or a file-like object.

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
        self._read(file, endian)
        self.file = file
        self.file.close()

    def _read(self, file, endian):
        """
        Read a VM model from a file-like object.

        :param file: A file-like object with the file pointer set at the
            beginning of a VM binary file.
        """
        # Header information
        fmt = '{:}iiii'.format(endian)
        self.nx, self.ny, self.nz, self.nr = unpack(fmt, file.read(4*4))
        fmt = '{:}fff'.format(endian)
        self.r1 = unpack(fmt, file.read(4*3))
        self.r2 = unpack(fmt, file.read(4*3))
        fmt = '{:}fff'.format(endian)
        self.dx, self.dy, self.dz = unpack(fmt, file.read(4*3))
        # TODO read slowness grid, etc
        # self.sl = [[nx],[ny],[nz]]? or  [[nz],[ny],[nx]] (as in vm_read.m)


        # TODO
        # Rgrid
        # TODO
        # Slowness grid
        # TODO



        print self.r1, self.r2
        print self.dx, self.dy, self.dz
        print self.nx, self.ny, self.nz, self.nr

        #raise NotImplementedError('No _read() yet')



