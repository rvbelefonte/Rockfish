"""
Utilities for converting model data to Genneric Mapping Tools formats.
"""
import numpy as np
from scipy.io import netcdf_file as netcdf
from sympy.physics import units as sunits

def surface2netcdf(vm, iref, filename, units='m'):
    """
    Write surface depths to a netcdf file, which can be read by GMT.

    :param vm: :class:`rockfish.tomography.model.VM` instance
    :param iref: index of the interface to write out
    :param filename: Filename of the output netcdf file 
    :param units: string name of output units
    """
    # Unit scaling
    scl = sunits.kilometers / sunits.__getattribute__(units)
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
    z[:, :] = vm.rf[iref].transpose() * scl
    z.units = units
    z.scale_factor = 1.
    z.add_offset = 0.
    # depth range
    f.createDimension('side', 2)
    z_range = f.createVariable('z_range', 'f', ('side',))
    z_range[0] = np.min(vm.rf[0]) * scl
    z_range[1] = np.min(vm.rf[1]) * scl
    # close
    f.sync()
    f.close()
