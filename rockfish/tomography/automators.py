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
                final_chi_squared=1, chi2_reduction_per_step=0.1):
    """
    Reduce Chi^2 slowly by alternating between raytracing and inversion.

    :param input_vmfile: Filename of the VM-format slowness model to use as
        the starting model for the inversion.
    """
    # Loop over raytracing and inversion
    chi2_0 = 1e9999
    vmfile0 = input_vmfile
    istep = 0
    while chi2_0 > final_chi_squared:
        # Raytrace and get current chi^2
        rayfile = '.'.join(vmfile0.split('.vm')[0:-1]) + '.ray'
        raytrace(vmfile0, pickdb, rayfile, **pick_keys)
        rays = readRayfanGroup(rayfile)
        chi2_0 = rays.chi2
        # Update user
        msg = pad_string('Step {:d}'.format(istep), char='*')
        print msg
        print rays
        print '*'*len(msg)
        # Invert
        target_chi2 = chi2_0 - chi2_0*chi2_reduction_per_step
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

