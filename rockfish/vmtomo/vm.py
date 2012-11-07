"""
Utilities for working with velocity models.
"""
import numpy as np
from scipy.interpolate import interp1d

class VM(object):
    """
    Class for working with VM Tomography velocity models.
    """
    def __init__(self, r1=(0, 0, 0), r2=(250, 0, 30),
                         dx=0.5, dy=1, dz=0.1, nr=0):
        """
        Create a new model instance.

        :param r1: Optional. Minimum values for grid dimensions given as the 
            tuple ``(xmin, ymin, zmin)``. Default is ``(0,0,0)``.
        :param r2: Optional. Maximum values for grid dimensions given as the 
            tuple ``(xmax, ymax, zmax)``. Default is ``(250,0,30)``.
        :param dx: Optional. Spacing between x-nodes. Default is ``0.5``.
        :param dy: Optional. Spacing between y-nodes. Default is ``1``.
        :param dz: Optional. Spacing between z-nodes. Default is ``0.1``.
        :param nr: Optional. Number of interfaces in the model. Used to 
            define the size of the interface arrays. Default is ``0``.
        """
        self.init_model(r1, r2, dx, dy, dz, nr)

    def __str__(self, extended=False):
        """
        Print an overview of the VM model.
        """
        banner = self._pad_line('VM Model', char='=') 
        sng = banner + '\n'
        sng += self._print_header()
        sng += banner
        if not extended:
            sng += '\n[Use "print VM.__str__(extended=True)" for'
            sng += ' more detailed information]'
        return sng

    def define_layer_velocities(self, idx, vel, kind='linear'):
        """
        Define velocities within a layer by stretching a velocity function.

        At each x,y position in the model grid, the list of given velocities
        are first distributed proportionally across the height of the layer.
        Then, this z,v function is used to interpolate velocities for each
        depth node in the layer.
        
        :param idx: Index of layer to work on. 
        :param vel: ``list`` of layer velocities.
        :param kind: str or int, optional.  Specifies the kind of
            interpolation as a string ('linear','nearest', 'zero',
            'slinear', 'quadratic, 'cubic') or as an integer 
            specifying the order of the spline interpolator to use.
            Default is 'linear'.
        """
        nvel = len(vel)
        for ix,x in enumerate(self.x):
            for iy,y in enumerate(self.y):
                if idx == 0:
                    ztop = self.r1[2]
                else:
                    ztop = self.get_reflector_depth(idx-1, x, y)
                if idx == self.nr:
                    zbot = self.r2[2]
                else:
                    zbot = self.get_reflector_depth(idx, x, y)
                zi = ztop + (zbot-ztop)*np.arange(0., nvel)/(nvel-1)
                iztop = self.z2i(ztop)
                izbot = self.z2i(zbot)
                zv = interp1d(zi, vel, kind=kind)
                z = self.z[iztop:izbot]
                self.sl[ix, iy, iztop:izbot] = zv(z)
    
    def init_model(self, r1, r2, dx, dy, dz, nr):
        """
        Initialize a new model.

        :param r1: Minimum values for grid dimensions given as the 
            tuple ``(xmin, ymin, zmin)``.
        :param r2: Maximum values for grid dimensions given as the 
            tuple ``(xmax, ymax, zmax)``.
        :param dx: Spacing between x-nodes.
        :param dy: Spacing between y-nodes.
        :param dz: Spacing between z-nodes.
        :param nr: Number of interfaces in the model. Used to define the
            the size of the interface arrays.
        """
        # Calculate grid sizes
        nx = (r2[0] - r1[0])/dx + 1
        ny = (r2[1] - r1[1])/dy + 1
        nz = (r2[2] - r1[2])/dz + 1
        # Copy variables
        self.r1 = r1
        self.r2 = r2 
        self.dx = dx 
        self.dy = dy 
        self.dz = dz
        # Initialize arrays to all zeros
        self.sl = np.zeros((nx, ny, nz)) 
        self.rf = np.zeros((nr, nx, ny))
        self.jp = np.zeros((nr, nx, ny))
        self.ir = np.zeros((nr, nx, ny))
        self.ij = np.zeros((nr, nx, ny))

    def x2i(self, x):
        """
        Find an x index for an x coordinate.

        :param x: x coordinate in the model 
        :returns: nearest x index for the given coordinate
        """
        return int((x-self.r1[0])/self.dx)

    def y2i(self, y):
        """
        Find a y index for a y coordinate.

        :param y: y coordinate in the model 
        :returns: nearest y index for the given coordinate
        """
        return int((y-self.r1[1])/self.dy)

    def z2i(self, z):
        """
        Find a z index for a z coordinate.

        :param z: z coordinate in the model 
        :returns: nearest z index for the given coordinate
        """
        return int((z-self.r1[2])/self.dz)

    # Private methods
    def _pad_line(self, msg, char=' ', width=78):
        """
        Center a string in a fixed-width line.

        :param char: Optional. Character to fill the pad with. Default is 
            ``' '``.
        :param width: Optional.  Width of the line. Default is 78.
        """
        npad = (width - len(msg))/2
        return char*npad + msg + char*npad

    def _print_header(self):
        """
        Format header values as plain-text.
        """
        sng = 'Grid Dimensions:\n'
        sng += ' xmin = {:7.3f}'.format(self.r1[0])
        sng += ', xmax = {:7.3f}'.format(self.r2[0])
        sng += ', dx = {:7.3f}'.format(self.dx)
        sng += ', nx = {:5d}\n'.format(self.nx)
        sng += ' ymin = {:7.3f}'.format(self.r1[1])
        sng += ', ymax = {:7.3f}'.format(self.r2[1])
        sng += ', dy = {:7.3f}'.format(self.dy)
        sng += ', ny = {:5d}\n'.format(self.ny)
        sng += ' zmin = {:7.3f}'.format(self.r1[2])
        sng += ', zmax = {:7.3f}'.format(self.r2[2])
        sng += ', dz = {:7.3f}'.format(self.dz)
        sng += ', nz = {:5d}\n'.format(self.nz)
        sng += 'Interfaces:'
        sng += ' nr = {:d}\n'.format(self.nr)
        return sng

    def _print_layer_info(self, idx):
        """
        Print details about a layer.

        :param idx: Index of layer to get information for.
        """
        raise NotImplementedError

    # Properties
    def _get_nr(self):
        """
        Returns the number of reflectors in the model.
        """
        return self.rf.shape[0]
    nr = property(fget=_get_nr)

    def _get_nx(self):
        """
        Returns the number of x-nodes in the model grid.
        """
        return self.sl.shape[0]
    nx = property(fget=_get_nx)

    def _get_ny(self):
        """
        Returns the number of y-nodes in the model grid.
        """
        return self.sl.shape[1]
    ny = property(fget=_get_ny)

    def _get_nz(self):
        """
        Returns the number of z-nodes in the model grid.
        """
        return self.sl.shape[2]
    nz = property(fget=_get_nz)

    def _get_x(self):
        """
        Returns an array of x-axis coordinates.
        """
        return np.asarray(range(0, self.nx))*self.dx
    x = property(fget=_get_x)

    def _get_y(self):
        """
        Returns an array of y-axis coordinates.
        """
        return np.asarray(range(0, self.ny))*self.dy
    y = property(fget=_get_y)
    
    def _get_z(self):
        """
        Returns an array of z-axis coordinates.
        """
        return np.asarray(range(0, self.nz))*self.dz
    z = property(fget=_get_z)


