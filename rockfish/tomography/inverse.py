"""
Wrappers for VM Tomography inversion
"""
import os
import subprocess
import warnings
import time
from utils import python2fortran_bool, bool2int
from model import readVM

INVERSION_PROGRAM = 'vm_tomo'

# Fixed parameters
PRINT_FORTRAN_DEBUG = False
USE_NEW_FRECHET_DERIVATIVE_CALCULATION = True
USE_HEADWAVES_IN_FRECHET_DERIVATIVES = True
USE_COMBINATION_SMOOTHNESS = True

def invert(input_vmfile, rayfile, output_vmfile,
           target_chi_squared=1.0, damping=0.1,
           first_derivative_smoothing=0.1, second_derivative_smoothing=0.5,
           ngrid=None, dz0=None, zuniform=None,
           slowness_scale=0.02, slowness_jump_scale=0.005,
           reflector_depth_scale=2.0,
           top_layer=0, bottom_layer=None,
           station_correction=True,
           station_correction_scale=0.04, station_correction_weight=0.0,
           station_correction_file='station_statics.dat',
           headwaves=True, strict_layers=True, extrapolate_grid=True,
           ray_skip_interval=1, horizontal_ray_extension=20,
           vertical_ray_extension=5, slowness_reference_scale=0.2,
           vscale_pow=2, matrix_terms=2, penalty_terms=2,
           reflector_depth_weight=0.5, slowness_jump_weight=10,
           aspect_ratio=1.0,
           diagnostic_directory='inverse'):
    """
    Wrapper for running the VM Tomography inversion program.

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
    :param ngrid: Optional. Tuple with grid sizes ``(nx, ny, nz)`` for the
        inversion grid. Default is to use the model grid sizes.
    :param dz0: Optional. Vertical grid spacing at the top of the inversion
        grid. Default is to use the model grid spacing.
    :param zuniform: Optional. Depth below which the inversion grid spacing
        increases linearly. Default is set this depth to the maximum depth
        in the input model (i.e., inversion grid spacing is constant).
    :param slowness_scale: Optional. Scale factor for slowness (1/velocity)
        changes. Default is ``0.02``.
    :param slowness_jump_scale: Optional. Scale factor for slowness jump
        changes. Default is ``0.005``.
    :param reflector_depth_scale: Optional. Scale factor for changes to
        reflector depths. Default is ``2.0``.
    :param top_layer: Optional. The index of the top-most layer to include in
        the inversion. Default is ``0`` (i.e., the top-most layer in the
        model).
    :param bottom_layer: Optional. The index of the bottom-most layer to
        include in the model. Default is the index of the bottom-most layer
        in the model.
    :param station_correction: Optional. Determines whether or not to include
        station static corrections in the inversion. Default is True.
    :param station_correction_scale: Optional. Scale factor for station
        static corrections. Default is 0.04.
    :param station_correction_weight: Optional. Weight for station correction
        terms. A value of zero forces station corrections to be enforced.
        Default is ``0.0``.
    :param station_correction_file: Optional. Filename for output file with
        station static corrections. Default is ``station_statics.dat``.
    :param headwaves: Optional. Determines whether or not to include
        include headwaves in the calculation of Frechet derivatives. Default
        is True.
    :param strict_layers: Optional. Default is True.
    :param extrapolate_grid: Optional. Default is True.
    :param ray_skip_interval: Optional. Skip interval for raypaths to include in
        the inversion. 1=use all rays, n=use every n-th ray. Default is 1.
    :param horizontal_ray_extension: Optional. Horizontal distance over which to
        extend model sensitivity. Units are the same as the model's distance
        units. Default is ``20.``.
    :param vertical_ray_extension: Optional. Vertical distance over which to
        extend model sensitivity. Units are the same as the model's distance
        units. Default is ``5.``.
    :param slowness_reference_scale: Optional. Scaling factor for the reference
        slowness model. Default is ``0.2``.
    :param vscale_pow: Optional. ????. Default is ``2``.
    :param matrix_terms: Optional. ????. Default is ``2``.
    :param penalty_terms: Optional. ????. Default is ``2``.
    :param reflector_depth_weight: Optional. Relative strength regularization of
        interface depths. Default is ``0.5``.
    :param aspect_ratio: Optional. Aspect ratio of smoothing constraints (i.e, 
        amplification of horizontal versus vertical derivatives constraints).
        Default is ``1.0`` (i.e., no bias).
    :param slowness_jump_weight: Optional. Relative strength regularization of
        slowness jumps. Default is ``10.0``.
    :param diagnostic_directory: Optional. Directory to store diagnositic files
        in. Default is to create a new directory ``'inverse'`` within the current
        working directory, if it does not already exist.
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
    # Diagnostic files
    if not os.path.isdir(diagnostic_directory):
        os.mkdir(diagnostic_directory)
    frechet_matrix = diagnostic_directory + os.path.sep \
            + 'frechet_matrix.bin'
    sl1_file = diagnostic_directory + os.path.sep + 'sl.dat'
    sl2_file = diagnostic_directory + os.path.sep + 'sl.ext.dat'
    rf1_file = diagnostic_directory + os.path.sep + 'rf.dat'
    rf2_file = diagnostic_directory + os.path.sep + 'rf.ext.dat'
    jp1_file = diagnostic_directory + os.path.sep + 'jp.dat'
    jp2_file = diagnostic_directory + os.path.sep + 'jp.ext.dat'
    dws_sl_file = diagnostic_directory + os.path.sep + 'dws.sl.dat'
    dws_rf_file = diagnostic_directory + os.path.sep + 'dws.rf.dat'
    dws_jp_file = diagnostic_directory + os.path.sep + 'dws.jp.dat'
    nlr_file = diagnostic_directory + os.path.sep + 'nlr.dat'
    inz_file = diagnostic_directory + os.path.sep + 'inz.dat'
    anz_file = diagnostic_directory + os.path.sep + 'anz.dat'
    sol_file = diagnostic_directory + os.path.sep + 'sol.dat'
    # Build run script
    sh = '#!/bin/bash\n'
    sh += '#\n'
    sh += '{:} << eof\n'.format(INVERSION_PROGRAM)
    sh += '{:} {:} {:} {:}\n'\
        .format(python2fortran_bool(USE_NEW_FRECHET_DERIVATIVE_CALCULATION),
        python2fortran_bool(USE_COMBINATION_SMOOTHNESS), 
        python2fortran_bool(station_correction),
        bool2int(PRINT_FORTRAN_DEBUG))
    sh += '{:}\n'.format(python2fortran_bool(headwaves))
    sh += '{:} {:}\n'.format(python2fortran_bool(strict_layers),
                             python2fortran_bool(extrapolate_grid))
    sh += '{:}\n'.format(input_vmfile)
    sh += '{:} {:} {:}\n'.format(ngrid[0], ngrid[1], ngrid[2])
    sh += '{:} {:}\n'.format(dz0, zuniform)
    sh += '{:} {:}\n'.format(top_layer, bottom_layer)
    sh += '{:}\n'.format(rayfile)
    sh += '{:}\n'.format(frechet_matrix)
    sh += '{:}\n'.format(ray_skip_interval)
    sh += '{:} {:}\n'.format(horizontal_ray_extension, vertical_ray_extension)
    sh += '{:}\n'.format(sl1_file)
    sh += '{:}\n'.format(sl2_file)
    sh += '{:}\n'.format(rf1_file)
    sh += '{:}\n'.format(rf2_file)
    sh += '{:}\n'.format(jp1_file)
    sh += '{:}\n'.format(jp2_file)
    sh += '{:} {:} {:}\n'.format(damping, first_derivative_smoothing,
                                 second_derivative_smoothing)
    sh += '{:}\n'.format(station_correction_weight)
    sh += '{:} {:} {:} {:}\n'.format(slowness_scale, slowness_jump_scale,
        reflector_depth_scale, station_correction_scale)
    sh += '{:} {:} {:} {:}\n'.format(slowness_reference_scale,
        vscale_pow, matrix_terms, penalty_terms)
    sh += '{:} {:}\n'.format(reflector_depth_weight, slowness_jump_weight)
    sh += '{:}\n'.format(aspect_ratio)
    sh += '{:}\n'.format(dws_sl_file)
    sh += '{:}\n'.format(dws_rf_file)
    sh += '{:}\n'.format(dws_jp_file)
    sh += '{:}\n'.format(nlr_file)
    sh += '{:}\n'.format(inz_file)
    sh += '{:}\n'.format(anz_file)
    sh += '{:}\n'.format(sol_file)
    sh += '{:}\n'.format(target_chi_squared)
    sh += '{:}\n'.format(station_correction_file)
    sh += '{:}\n'.format(output_vmfile)
    sh += 'eof'
    # Run the script
    subprocess.call(sh, shell=True)

def plot_grid_dws(dwsfile):
    """
    Plot the derivative-weight sum (DWS) for the model slowness grid.

    :param dwsfile: ASCII file with the collums x, y, z, dws.
    """


