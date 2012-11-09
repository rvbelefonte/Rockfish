"""
Support for working with velocity models.
"""
import numpy as np
from scipy.interpolate import interp1d
from rockfish import __version__

class VM(object):
    """
    Base class for working with VM Tomography velocity models.
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

    def __str__(self, extended=False, title='Velocity Model'):
        """
        Print an overview of the VM model.

        :param extended: Optional. Determines whether or not to print detailed
            information about each layer. Default is to print an overview.
        :param title: Optional. Sets the title in the banner. Default is
            'Velocity Model'.
        """
        banner = self._pad_line(title, char='=') 
        sng = banner + '\n'
        sng += self._print_header()
        sng += banner
        #if not extended:
        #    sng += '\n[Use "print VM.__str__(extended=True)" for'
        #    sng += ' more detailed information]'
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
        # Get layer boundary depths
        z0, z1 = get_layer_bounds(idx)
        # Define velocity function at each x,y point
        vel = np.asarray(vel)
        nvel = len(vel)
        for ix,x in enumerate(self.x):
            for iy,y in enumerate(self.y):
                zi = z0[ix,iy] + (z1[ix,iy] - z0[ix,iy])\
                        *np.arange(0., nvel)/(nvel - 1)
                iz0, iz1 = self.z2i((z0[ix,iy], z1[ix,iy]))
                z = self.z[iz0:iz1]
                if len(z) == 0:
                    # in pinchout, nothing to do
                    continue
                # Pad interpolates for rounding to grid coordinates
                vi = np.copy(vel)
                if z[0] < zi[0]:
                    zi = np.insert(zi, 0, z[0])
                    vi = np.insert(vi, 0, vel[0])
                if z[-1] > zi[-1]:
                    zi = np.append(zi, z[-1])
                    vi = np.append(vi, vel[-1])
                # Interpolate velocities
                zv = interp1d(zi, vi, kind=kind)
                self.sl[ix, iy, iz0:iz1] = 1./zv(z)

    def define_layer_gradient(self, idx, dvdz, v0=None):
        """
        Replace velocities within a layer by defining a gradient.

        :param idx: Index of layer to work on.
        :param dvdz: Velocity gradient.
        :param v0: Optional. Velocity at top of layer. Default is to use the
            value at the base of the overlying layer.
        """
        z0, z1 = self.get_layer_bounds(idx)
        for ix,x in enumerate(self.x):
            for iy,y in enumerate(self.y):
                iz0, iz1 = self.z2i((z0[ix,iy], z1[ix,iy]))
                z = self.z[iz0:iz1] - self.z[iz0]
                if v0 is None:
                    if iz0 == 0:
                        _v0 = 0.
                    else:
                        _v0 = 1./self.sl[ix, iy, iz0-1]
                else:
                    _v0 = v0
                self.sl[ix, iy, iz0:iz1] = 1./(_v0 + z*dvdz)

    def get_layer_bounds(self, idx):
        """
        Get surfaces bounding a layer.
        
        :param idx: Index of layer of interest.
        :returns: z0, z1 arrays of top, bottom interface depths.
        """
        if idx == 0:
            z0 = np.ones((self.nx, self.ny))*self.r1[2]
        else:
            z0 = self.rf[idx-1]
        if idx > self.nr:
            z0 = np.ones((self.nx, self.ny))*self.r2[2]
        else:
            z1 = self.rf[idx]
        return z0, z1
    
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

    def init_empty_model(self):
        """
        Initialize a new empty model.
        """
        self.r1 = (None, None, None)
        self.r2 = (None, None, None)
        self.dx = None
        self.dy = None
        self.dz = None
        self.sl = np.empty_like(0) 
        self.rf = np.empty_like(0) 
        self.jp = np.empty_like(0)
        self.ir = np.empty_like(0)
        self.ij = np.empty_like(0)

    def x2i(self, x):
        """
        Find an x index for an x coordinate.

        :param x: list of x coordinates in the model 
        :returns: list of nearest x index for the given coordinates
        """
        return [int((_x-self.r1[2])/self.dx) for _x in x]

    def y2i(self, y):
        """
        Find a y index for a y coordinate.

        :param y: list of y coordinates in the model 
        :returns: list of nearest y index for the given coordinates
        """
        return [int((_y-self.r1[2])/self.dy) for _y in y]

    def z2i(self, z):
        """
        Find a z index for a z coordinate.

        :param z: list of z coordinates in the model 
        :returns: list of nearest z index for the given coordinates
        """
        return [int((_z-self.r1[2])/self.dz) for _z in z]

    def gridpoint2position(self, ix, iy, iz):
        """
        Returns the x,y,z coordinates coresponding to a set of model indices.
        
        :param ix: x-coordinate index
        :param iy: y-coordinate index
        :param iz: z-coordinate index
        :returns: x, y, z 
        """
        x = ix*self.dx + self.r1[0]
        y = iy*self.dy + self.r1[1]
        z = iz*self.dz + self.r1[2]
        return x,y,z

    def slice_along_xy_line(self, x, y, dx=None, nx=None):
        """
        Extract a vertical slice along a line.

        :param x,y: Lists of coordinates to take slice along.
        :returns: VM model along the specified line
        """
        assert len(x) == len(y), 'x and y must be the same length'
        assert max(x) <= self.r2[0], 'x coordinates exceed model domain'
        assert min(x) >= self.r1[0], 'x coordinates exceed model domain'
        assert max(y) <= self.r2[1], 'y coordinates exceed model domain'
        assert min(y) > self.r1[1], 'y coordinates exceed model domain'
        # Calculate distance along line
        _xline = [0]
        for i in range(1,len(x)):
            x0 = x[i-1]
            y0 = y[i-1]
            x1 = x[i]
            y1 = y[i]
            deltx = np.sqrt((x1-x0)**2 + (y1-y0)**2)
            _xline.append(_xline[i-1] + deltx)
        # Setup new model
        vm = VM()
        vm.r1 = (min(_xline), 0, self.r1[2])
        vm.r2 = (max(_xline), 0, self.r2[2])
        if dx is None:
            vm.dx = self.dx
        else:
            vm.dx = dx
        vm.nx = int(np.floor((max(_xline) - min(_xline))/vm.dx))
        xline = np.linspace(min(_xline), max(_xline), vm.nx)
        vm.dy = 1
        vm.dz = self.dz
        vm.ny = 1
        vm.nz = self.nz
        vm.nr = self.nr
        # Pull slowness grid and interface values along line
        interp_y = interp1d(x, y)
        interp_x = interp1d(_xline, x)
        for iref in range(0, self.nr):
            vm.rf.append([])
            vm.jp.append([])
            vm.ir.append([])
            vm.ij.append([])
        for _xl in xline:
            # get coordinates of position on line
            _x = interp_x(_xl)
            _y = interp_y(_x)
            # get indices in 3D model
            ix = self._x2i(_x)
            iy = self._y2i(_y)
            # get slowness collumn
            vm.sl.append([self.sl[ix][iy]])
            # get interfaces
            for iref in range(0, self.nr):
                vm.rf[iref].append([self.rf[iref][ix][iy]])
                vm.jp[iref].append([self.jp[iref][ix][iy]])
                vm.ir[iref].append([self.ir[iref][ix][iy]])
                vm.ij[iref].append([self.ij[iref][ix][iy]])
        vm.rf = np.asarray(vm.rf)
        vm.jp = np.asarray(vm.jp)
        vm.ir = np.asarray(vm.ir)
        vm.ij = np.asarray(vm.ij)
        return vm

    def remove_interface(self, index):
        """
        Remove an interface from the model.
        
        :param index: Index of the interface to remove.
        """
        self.rf = np.delete(self.rf, index, 0)
        self.jp = np.delete(self.rf, index, 0)
        self.ir = np.delete(self.rf, index, 0)
        self.ij = np.delete(self.rf, index, 0)

    def insert_interface(self, rf, jp=None, ir=None, ij=None):
        """
        Insert an interface.

        :param rf: Interface depths given as a Numpy array_like object with
            shape ``(nx, ny)``.
        :param jp: Optional. Slowness jumps given as a Numpy array_like object
            with shape ``(nx, ny)``. Default is to set the slowness jump for all
            nodes on the new interface to zero.
        :param ir: Optional. Indices of the interfaces to use in the inversion
            for interface depths, given as a Numpy array_like object
            with shape ``(nx, ny)``. A ``-1`` value indicates that a node should
            not be used in the inversion. Default is to assign all nodes to the
            index of the new interface.
        :param ij: Optional. Indices of the interfaces to use in the inversion
            for slowness jumps, given as a Numpy array_like object
            with shape ``(nx, ny)``. A ``-1`` value indicates that a node should
            not be used in the inversion. Default is to assign all nodes to the
            index of the new interface.
        """
        # Determine index for new interface
        iref = 0
        for _iref in range(0, self.nr):
            if rf.max() >= self.rf[_iref].max():
                iref += 1
        # Create default arrays if not given
        if jp is None:
            jp = np.zeros((self.nx, self.ny))
        if ir is None:
            ir = iref * np.ones((self.nx, self.ny))
        if ij is None:
            ij = iref * np.ones((self.nx, self.ny))
        # Insert arrays for new interface
        self.rf = np.insert(self.rf, iref, rf, 0)
        self.jp = np.insert(self.jp, iref, jp, 0)
        self.ir = np.insert(self.ir, iref, ir, 0)
        self.ij = np.insert(self.ij, iref, ij, 0)
        print "Added interface with index {:}.".format(iref)

# XXX leave this here until we decide if we need it
#    def get_layer_designations(self):
#        """
#        Finds the layer designation for each node in the slowness grid.
#        """
#        flag = -999
#        self.layer = np.ones(self.sl.shape)*flag
#
#        #XXX in progress...
#        
#        nmissed = (self.layer==flag).sum()
#        if nmissed > 0:
#            msg = '{:} of {:} grid nodes not assigned to a layer'\
#                    .format(nmissed, self.sl.size)
#            warnings.warn(msg)
#        # XXX dev!
#        raise NotImplementedError

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
        return self.r1[0] + np.asarray(range(0, self.nx))*self.dx
    x = property(fget=_get_x)

    def _get_y(self):
        """
        Returns an array of y-axis coordinates.
        """
        return self.r1[1] + np.asarray(range(0, self.ny))*self.dy
    y = property(fget=_get_y)
    
    def _get_z(self):
        """
        Returns an array of z-axis coordinates.
        """
        return self.r1[2] + np.asarray(range(0, self.nz))*self.dz
    z = property(fget=_get_z)
