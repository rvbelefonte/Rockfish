"""
Utilities for converting model data to Genneric Mapping Tools formats.
"""
import os
import subprocess
import numpy as np
from scipy.io import netcdf_file as netcdf
from sympy.physics import units as sunits

def interface2netcdf(vm, iref, filename, units='km', elevation=False):
    """
    Write interface depths to a netcdf file.

    Parameters
    ----------
    vm : :class:`rockfish.tomography.model.VM`
        VM model to extract an interface from.
    iref : int
        Index of interface to extract.
    filename: str
        Name of the netcdf file to write the interface to.
    units : 'str', optional
        Name of distance units in the output file. Must be a unit name
        understood by :class:`sympy.physics.units`. Distance units in the
        model are assumed to be 'km'.
    elevation : bool, optional
        If ``True``, flip the sign of interface depths.
    """
    # Unit scaling
    scl = sunits.kilometers / sunits.__getattribute__(units)
    if elevation:
        zscl = scl * -1.
    else:
        zscl = scl
    # Open file
    f = netcdf(filename, 'w')
    f.title = 'Interface {:} from VM model.'.format(iref) 
    f.source = 'Created by rockfish.tomography.vm2gmt.surface2netcdf'
    # x-dimension
    f.createDimension('x', vm.ny)
    x = f.createVariable('x', 'f', ('x',))
    x[:] = vm.y * scl
    x.units = units
    # y-dimension
    f.createDimension('y', vm.nx)
    y = f.createVariable('y', 'f', ('y',))
    y[:] = vm.x * scl
    y.units = units
    # depths (z)
    z = f.createVariable('z', 'f', ('x', 'y'))
    z[:, :] = vm.rf[iref].transpose() * zscl
    z.units = units
    z.scale_factor = 1.
    z.add_offset = 0.
    # depth range
    f.createDimension('side', 2)
    z_range = f.createVariable('z_range', 'f', ('side',))
    z_range[0] = np.min(vm.rf[0]) * zscl
    z_range[1] = np.min(vm.rf[1]) * zscl
    f.sync()
    f.close()

def interface2grd(vm, iref, filename, **kwargs):
    """
    Write surface depths to a GMT-compatible netcdf file.

    .. note:: In general, netcdf files produced by :meth:`surface2netcdf`
        are compatible with GMT. However, zmin and zmax are not set correctly,
        causing issues with other programs such as Fledermaus. 
        :meth:`surface2grd` is a kludge that uses GMT's grd2xyz and then
        xyz2grd to create a fully GMT-compatible netcdf file. 
        
    .. todo:: Replace with a fully functioning version of 
        :meth:`surface2netcdf`.

    Parameters
    ----------
    vm : :class:`rockfish.tomography.model.VM`
        VM model to extract an interface from.
    iref : int
        Index of interface to extract.
    filename: str
        Name of the grd file to write the interface to.
    kwargs :
        Arguments for :meth:`surface2netcdf`.
    """
    ncdf = 'temp.netcdf'
    interface2netcdf(vm, iref, ncdf, **kwargs)
    grd = netcdf(ncdf)
    y = grd.variables['x'][:]
    x = grd.variables['y'][:]
    region = '{:}/{:}/{:}/{:}'.format(min(x), max(x), min(y), max(y))
    spacing = '{:}/{:}'.format(np.diff(x[0:2])[0], np.diff(y[0:2])[0])
    tmp = 'temp.xyz'
    gmt = "grd2xyz {:} > {:}\n".format(ncdf, tmp)
    gmt += 'xyz2grd {:} -G{:} -R{:} -I{:}'\
            .format(tmp, filename, region, spacing)
    subprocess.call(gmt, shell=True)
    os.remove(tmp)
    os.remove(ncdf)
