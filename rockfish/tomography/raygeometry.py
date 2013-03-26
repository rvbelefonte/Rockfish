"""
Tools for working with raypath geometry.
"""

def assign_points_to_layers(vm, x, y, z, layers=None)
    """
    Find the portion of a path that is within a layer.
    
    Parameters
    ----------
    vm : rockfish.tomography.model.VM
        Velocity model.
    x, y, z : array_like
        Arrays of x, y, z coordinates to find layers for.  Must all be the same
        size.

    Returns
    -------
    layer_indices : numpy.ndarray
        Layer index for each point.
    """
    # get indices for each point
    ix = vm.x2i(x)
    iy = vm.y2i(y)
    iz = vm.z2i(z)
    
    # return layer indices for each point
    if layers is None:
        return vm.layers[ix, iy, iz]
    else:
        return layers[ix, iy, iz]


def get_piercing_points(vm, iref, path, layers=None):
    """
    Find where paths cross a surface.

    Parameters
    ----------

    """
    il = assign_points_to_layers(vm, path[:, 0], path[:, 1], path[:, 2],
                                 layers=layers)
    # indices for points near crossing points
    i0 = np.nonzero(np.diff(il) > 0)[0]     # above
    i1 = i0 + 1                             # below
    # indices for points near crossing point on interface of interest
    j0 = i0[np.nonzero(il[i0] == iref)]
    j1 = i1[np.nonzero(il[i1] == iref + 1)]

    # interpolate for crossing points



