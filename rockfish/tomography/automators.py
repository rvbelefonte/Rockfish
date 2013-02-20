"""
Automators for raytracing and inversion.
"""
import os
from rockfish.utils.string_tools import pad_string
from rockfish.tomography import raytrace, invert, readRayfanGroup
from rockfish.tomography.utils import update_model_id


class AutomatorError(Exception):
    """
    Base class for automator exceptions.
    """
    pass


def chi2_reduce(input_vmfile, pickdb, pick_keys={}, inversion_params={},
                final_chi2=1, chi2_reduction_per_step=0.1,
                log_file=None, relax=False):
    """
    Reduce Chi^2 slowly by alternating between raytracing and inversion.

    :param input_vmfile: Filename of the VM-format slowness model to use as
        the starting model for the inversion.
    :param pickdb: :class:`rockfish.picking.database.PickDatabaseConnection`
        to get picks from for raytracing.
    :param pick_keys: ``dict`` of keys and values to use for selecting
        picks from ``pickdb``.
    :param inversion_params: ``dict`` of parameters and values that are passed
        as keyword arguments to :method:`rockfish.tomography.inverse.invert`.
    :param final_chi2: Target value for the final chi^2.
    :param chi2_reduction_per_step: Fractional reduction of chi^2 for each
        step.
    :param log_file: Name of a file to write model name, chi^2, mean RMS, etc.
        for each time step to. Default is not to write a log file.
    :param relax: ``bool`` that determines whether or not to relax smoothing
        and regularization parameters. Only applies to parameters that are
        included in ``inversion_params``. Default is False.
    :param min_delta_chi2: Minimal fractional change in chi^2 for relaxing
        smoothing and regularization parameters. If ``relax`` is True and
        the fractional change in chi^2 over an inversion step is less than
        ``min_delta_chi2``, the smoothing and regularization parameters
        are relaxed by ``relaxation_per_step``. Default is ``0.01``.
    :param relaxation_per_step: Fractional change in smoothing and
        regularization parameters over a single step. Only used if
        ``relax`` is True. Default is ``0.1``.
    """
    # Set up log file
    if log_file is not None:
        log = open(log_file, 'w')
        log.write('# Log file for {:}\n'.format(__name__))
        log.write('# model chi2 rms inversion_params\n')
    # Loop over raytracing and inversion
    chi2_0 = 1e9999
    vmfile0 = input_vmfile
    istep = 0
    while chi2_0 > final_chi2:
        # Raytrace and get current chi^2
        rayfile = '.'.join(vmfile0.split('.vm')[0:-1]) + '.ray'
        raytrace(vmfile0, pickdb, rayfile, **pick_keys)
        rays = readRayfanGroup(rayfile)
        chi2_0 = rays.chi2
        # Update user
        msg = pad_string('Step {:d}'.format(istep), char='*')
        print msg
        print rays
        print '*' * len(msg)
        # Invert
        target_chi2 = chi2_0 - chi2_0 * chi2_reduction_per_step
        vmfile1 = update_model_id(vmfile0)
        invert(vmfile0, rayfile, vmfile1, target_chi_squared=target_chi2,
               **inversion_params)
        # Check for inversion output
        if not os.path.isfile(vmfile1):
            msg = 'Inversion of model {:} failed to produce an updated model.'\
                    .format(vmfile0)
            raise AutomatorError(msg)
        # Step model name
        vmfile0 = vmfile1
        istep += 1
    if log_file is not None:
        log.close()
    return vmfile1
