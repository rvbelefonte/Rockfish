"""
Wrappers for VM Tomography inversion
"""
import os
import subprocess
import warnings
import time
from utils import python2fortran_bool
from model import readVM

INVERSION_PROGRAM = 'vm_tomo'

# Print debugging information from the Fortran programs
FORTRAN_DEBUG = False

            
def inverse(input_vmfile, rayfile, output_vmfile,
            target_chi_squared=1.0, damping=0.1,
            first_derivative_smoothing=0.1, second_derivative_smoothing=0.5,
            slowness_scale=0.02, slowness_jump_scale=0.005,
            reflector_depth_scale=2.0,
            ngrid=(None, None, None), dz0=None, zuniform=None,
            top_layer=0, bottom_layer=None,
            logfile='inverse.log', new_frechet=True,
            combo_smooth=True, station_correction=True,
            station_correction_scale=0.04,
            headwaves=True, strict_layers=True, extrapolate_grid=True,
            unsmoothed_output_vmfile=None,

           )
    """
    Wrapper for running the VM Tomography inversion program.

    .. todo:: Clarify function of optional parameters.

    :param input_vmfile: Filename of the VM-format slowness model to use as
        the starting model for the inversion.
    :param rayfile: Filename of the rayfan file with rays traced through
        ``vmfile``.
    :param output_vmfile: Filename of the VM-format slowness model to write
        the inversion result to.
    :param target_chi_squared: Optional. Target chi^2 value, a value that 
        measures how well the inversion result fits the data. Default is 
        ``1.0`` (i.e., the best fit that can be achieved within error).
    :param damping: Optional. Weight for model perturbation damping. A
        negative value causes damping to be turned off. Default is ``0.1``.
    :param first_derivative_smoothing: Optional. Weight for the penalty on 
        first derivative model smoothness. A negative value causes this term
        to be ignored. Default is ``0.1``.
    :param second_derivative_smoothing: Optional. Weight for the penalty on 
        second derivative model smoothness. A negative value causes this term
        to be ignored. Default is ``0.5``.
    :param slowness_scale: Optional. Scale factor for slowness (1/velocity)
        changes. Default is ``0.02``.
    :param slowness_jump_scale: Optional. Scale factor for slowness jump
        changes. Default is ``0.005``.
    :param reflector_depth_scale: Optional. Scale factor for changes to
        reflector depths. Default is ``2.0``.
    :param ngrid: Optional. Tuple with grid sizes ``(nx, ny, nz)`` for the
        inversion grid. Default is to use the model grid sizes.
    :param dz0: Optional. Vertical grid spacing at the top of the inversion
        grid. Default is to use the model grid spacing.
    :param zuniform: Optional. Depth below which the inversion grid spacing
        increases linearly. Default is set this depth to the maximum depth
        in the input model (i.e., inversion grid spacing is constant).
    :param top_layer: Optional. The index of the top-most layer to include in
        the inversion. Default is ``0`` (i.e., the top-most layer in the
        model).
    :param bottom_layer: Optional. The index of the bottom-most layer to
        include in the model. Default is the index of the bottom-most layer
        in the model.
    :param logfile: Optional. Filename for the inversion log file. Default is
        ``'inverse.log'``.
    :param new_frechet: Optional. Determines whether or not to use the newer
        Frechet derivative calculation method. Default is True.
    :param combo_smooth: Optional. Determines whether or not to run smoothing
        on total slowness. Default is True.
    :param station_correction: Optional. Determines whether or not to include
        station static corrections in the inversion. Default is True.
    :param station_correction_scale: Optional. Scale factor for station
        static corrections. Default is 0.04.
    :param headwaves: Optional. Determines whether or not to include
        include headwaves in the calculation of Frechet derivatives. Default
        is True.
    :param strict_layers: Optional. Default is True.
    :param extrapolate_grid: Optional. Default is True.
    :param unsmoothed_output_vmfile: Optional. Filename of an unsmoothed
        output velocity model. Default is to remove this file after the
        inversion run.
    """
    # Set default inversion grid parameters 
    if None in [ngrid, dz0, zuniform, bottom_layer]:
        vm = readVM(input_vmfile)
    if ngrid is None:
        ngrid = (vm.nx, vm.ny, vm.nz)
    if dz0 is None:
        dz0 = vm.dz
    if zuniform is None:
        zuniform = vm.r2[2]
    if bottom_layer is None:
        bottom_layer = vm.nr
    # Other default parameters
    if unsmoothed_output_vmfile is None:
        unsmoothed_output_vmfile = 'temp.rough.vm'
        remove_unsmoothed_vmfile = True
    else:
        remove_unsmoothed_vmfile = False 
    # Build run script
    sh = '#!/bin/bash\n'
    sh += '#\n'
    sh += '{:} << eof\n'.format(INVERSION_PROGRAM)
    sh += '{:}\n'.format(logfile)
    sh += '{:} {:} {:} {:}\n'.format(python2fortran_bool(new_frechet),
        python2fortran_bool(combo_smooth), 
        python2fortran_bool(station_correction),
        python2fortran_bool(FORTRAN_DEBUG))
    sh += '{:}\n'.format(python2fortran_bool(headwaves))
    sh += '{:} {:}\n'.format(python2fortran_bool(strict_layers),
                             python2fortran_bool(extrapolate_grid))
    sh += '{:}\n'.format(input_vmfile)
    sh += '{:} {:} {:}\n'.format(ngrid[0], ngrid[1], ngrid[2])
    sh += '{:} {:}\n'.format(dz0, zuniform)
    sh += '{:} {:}\n'.format(top_layer, bottom_layer)
    sh += '{:}\n'.format(rayfile)





    # Smoothing
    sh += '{:}\n'.format(unsmoothed_output_vmfile)
    sh += '{:} {:}\n'.format(top_layer, bottom_layer)
    sh += '{:} {:} {:}\n'.format(damping, first_derivative_smoothing,
                                 second_derivative_smoothing)
    sh += '{:} {:} {:}\n'.format(slowness_scale, slowness_jump_scale,
                                 reflector_depth_scale)


                                 


    # Cleanup
    if remove_unsmoothed_vmfile and os.path.isfile(remove_unsmoothed_vmfile):
        os.remove(remove_unsmoothed_vmfile)










