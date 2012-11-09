"""
Plotting support for VM Tomography models and rays.
"""
from vm import VM
import numpy as np
from rockfish import __version__
import matplotlib.pyplot as plt

class VMPlotter(VM):
    """
    Class that adds plotting support to the base VM model class.
    """
    def plot(self, x=None, y=None, z=None, velocity=True, ax=None):
        """
        Plot a slice from a VM slowness model.
        
        :param x,y,z: Optional. Coordinate value of slice to plot. Give one of
            the three. Default is to plot the first x-z plane (y=ymin) in the
            model.
        :param velocity: Optional. Determines whether to grid values in units
            of velocity or slowness. Default is to plot velocity.
        :param ax: Optional.  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create and show a new figure.
        """
        # Determine slice coordinates
        if False not in [v is None for v in [x,y,z]]:
            # Plot the 1st x-z plane
            y = self.r1[1]
        # Extract grid slice to plot
        sl, bounds, _extents, labels = self._slice_for_plot(
            x=x, y=y, z=z)
        extents = (_extents[0], _extents[1], _extents[3], _extents[2])
        if velocity is True:
            sl = 1./sl
        # Plot figure
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        ax.imshow(sl.transpose(), extent=extents)
        ax.plot(bounds[0], bounds[1], '-k')
        plt.xlabel(labels[0])
        plt.ylabel(labels[1])
        plt.xlim(self.r1[0], self.r2[0])
        # Show (TODO save, draw) plot
        if show:
            plt.show()
        else:
            plt.draw()

    def plot_profile(self, x=None, y=None, z=None, velocity=True,
                     ax=None):
        """
        Plot a 1D profile from the model grid.

        :param x,y,z: Optional. Coordinate value of profile to plot. Give two of
            the three. Default is to plot the first collumn in the model.
        :param velocity: Optional. Determines whether to grid values in units
            of velocity or slowness. Default is to plot velocity.
        :param ax: Optional.  A :class:`matplotlib.Axes.axes` object to plot
            into. Default is to create and show a new figure.
        """
        if False not in [v is None for v in [x,y,z]]:
            x = self.r1[0]
            y = self.r1[1]
            z = None
        if (x is not None) and (y is not None) and (z is None):
            # Plot z vs. v
            ix, = self.x2i([x])
            iy, = self.y2i([y])
            xval = self.sl[ix,iy,:]
            yval = self.z
            ylabel = 'Depth (km)'
            title = 'x = {:}, y = {:} (km)'.format(x,y)
            reverse = True
        elif (x is not None) and (y is None) and (z is not None):
            # Plot v vs. y
            xval = self.y
            ix, = self.x2i([x])
            iz, = self.z2i([z])
            yval = self.sl[ix, :, iz]
            xlabel = 'x-offset (km)'
            title = 'x = {:}, z = {:} (km)'.format(x,z)
            reverse = False
        elif (x is None) and (y is not None) and (z is not None):
            # Plot v vs. x
            xval = self.x
            iy, = self.y2i([x])
            iz, = self.z2i([z])
            yval = self.sl[:, ix, iz]
            xlabel = 'y-offset (km)'
            title = 'y = {:}, z = {:} (km)'.format(y,z)
            reverse = False
        else:
            msg = 'Must specify two of: x, y, z.'
            raise ValueError(msg)
        if velocity:
            if reverse:
                xval = 1./xval
                xlabel = 'Velocity (km/s)'
            else:
                yval = 1./yval
                ylabel = 'Velocity (km/s)'
        else:
            if reverse:
                xlabel = 'Slowness (s/km)'
            else:
                ylabel = 'Slowness (s/km)'
        # Make a new figure
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            show = True
        else:
            show = False
        # Plot
        ax.plot(xval, yval)
        if reverse:
            ax.set_ylim(ax.get_ylim()[::-1])
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        # Show (TODO save, draw) plot
        if show:
            plt.show()
        else:
            plt.draw()

    def _slice_for_plot(self, x=None, y=None, z=None):
        """
        Extract a slice from the 3D VM model slowness grid for plotting.
        
        :param x,y,z: Coordinate value of orthogonal slice to extract. Give
            one of the three.  
        :param plot_info: Optional. If True, also returns plot extents and axis
            labels. Default is False.
        :returns sl: Slice as a 2D stack of numpy arrays.
        :returns bounds: Interface depths
        :returns extents: Extents of the 2D slice as a tuple.
        :returns labels: Slice axis labels returned as a tuple.
        """
        # Prevent dividing by zero for 2d models
        if self.dx == 0:
            dx = 1
        else:
            dx = self.dx
        if self.dy == 0:
            dy = 1
        else:
            dy = self.dy
        if self.dz == 0:
            dz = 1
        else:
            dz = self.dz
        # Extract the grid slice
        if (x is not None) and (y is None) and (z is None):
            # Take a slice in the y-z plane
            ix = int((x - self.r1[0])/dx)
            sl = self.sl[ix]
            _x = list(np.linspace(self.r1[1],self.r2[1],self.ny))
            x = []; y = []
            for iref in range(0, self.nr):
                x += _x
                x += [None]
                y += [v for v in self.rf[iref][ix]]
                y += [None]
            dims = (1, 2)
            labels = ('y-offset (km)', 'Depth (km)')
        elif (x is None) and (y is not None) and (z is None):
            # Take a slice in the x-z plane
            iy = int((y - self.r1[1])/dy)
            sl = np.asarray([d[iy] for d in self.sl])
            _x = list(np.linspace(self.r1[0], self.r2[0], self.nx))
            x = []; y = []
            for iref in range(0, self.nr):
                x += _x
                x += [None]
                y += [v[iy] for v in self.rf[iref]]
                y += [None]
            dims = (0, 2)
            labels = ('x-offset (km)', 'Depth (km)')
        elif (x is None) and (y is None) and (z is not None):
            # Take a slice in the x-y plane
            iz = int((z - self.r1[2])/dz)
            sl = self.sl.transpose()[iz]
            x = [None]
            y = [None]
            dims = (0, 1)
            labels = ('x-offset (km)', 'y-offset (km)')
        else:
            msg = 'Specify one (and only one) of: x, y, z'
            raise ValueError(msg)
        bounds = [x, y]
        extents = (self.r1[dims[0]], self.r2[dims[0]],
                   self.r1[dims[1]], self.r2[dims[1]])
        return sl, bounds, extents, labels
