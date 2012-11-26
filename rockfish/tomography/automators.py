"""
Automators for raytracing and inversion.
"""
from rockfish.tomography import raytrace, invert
from rockfish.tomography.utils import update_model_id

def chi2_reduce(input_vmfile, pickdb, inversion_params={}, 
                raytracing_params={}, max_chi2_reduction=1):
    """
    Reduce Chi squared slowly by alternating between raytracing and inversion.

    :param input_vmfile: Filename of the VM-format slowness model to use as
        the starting model for the inversion.
    """
    # Raytrace the initial model
    rayfile = input_vmfile.split('.vm')[0:-1] + '.ray'
    raytrace(vmfile, pickdb, rayfile, input_dir=input_dir,
      cleanup=False, **pick_keys)
    rays = readRayfanGroup(rayfile)
    current_chisq = rays.chi2


