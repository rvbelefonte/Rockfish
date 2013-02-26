"""
Wrappers for VM Tomography raytracing
"""
import os
import subprocess
import warnings
import time
from rockfish.tomography import readVM

RAYTR_PROGRAM = 'slim_rays'


def raytrace(vmfile, pickdb, rayfile, input_dir='forward', cleanup=True,
          grid_size=None, forward_star_size=[12, 12, 24], min_angle=0.5,
          min_velocity=1.4, max_node_size=620, top_layer=0, bottom_layer=None,
          stdout=None, stderr=None, verbose=True, **kwargs):
    """
    Wrapper for running the VM Tomography raytracer.

    Uses pick data in a
        :class:`rockfish.picking.database.PickDatabaseConnection` to build
        required input files on-the-fly and executes the tracer.

    :param vmfile: Filename of the VM Tomography slowness model to
        raytrace.
    :param rayfile: Filename of the output rayfan file.
    :param pickdbfile: Active
        :class:`rockfish.picking.database.PickDatabaseConnection` to get picks
        from.
    :param input_dir: Optional. Path for writing intermediate files that are
        used as input to the raytracing program. Default is to create a new
        directory named ``'forward'``, if it does not already exist.
    :param cleanup: Optional. Determines whether or not to remove intermediate
        files that are used as input to the raytracing program. Default is to
        remove these files.
    :param grid_size: Optional. ``(nx, ny, nz)`` tuple with dimensions for the
        graphing grid. Default is to match the graphing grid to the slowness
        model dimensions.
        for the forward star. Default is (12, 12, 24). If model is 2D (ny = 1),
        the y-dimension for the forward star is set to ``0``.
    :param min_angle: Optional. Minimum angle between search directions in
        forward star in degrees. Default is ``0.5``.
    :param min_velocity: Optional. Minimum velocity to trace rays through.
        Default is ``1.4``.
    :param max_node_size: Optional. Average number of nodes to allocate for
        each raypath. The raytracing program will adjust this size if needed.
        Default is ``620``.
    :param top_layer: Optional. The index of the top-most layer to trace rays
        through. Default is ``0`` (i.e., the top-most layer in the model).
    :param bottom_layer: Optional. The index of the bottom-most layer to trace
        rays through. Default is the index of the bottom-most layer in the
        model.
    :param stdout: Optional. Object to send standard out messages produced
        by the raytracing program to. Default is to send messages to the
        standard out.
    :param stderr: Optional. Object to send standard error messages produced
        by the raytracing program to. Default is to send messages to the
        standard error.
    :param verbose: Optional. Determines whether or not to print detailed
        information from the raytracer. Default is ``True``.
    :param **kwargs: keyword=value arguments used to select picks to output
    """
    # Make the input files
    instfile = 'inst.dat'
    pickfile = 'picks.dat'
    shotfile = 'shots.dat'
    if not os.path.isdir(input_dir):
        os.mkdir(input_dir)
    pickdb.write_vmtomo(instfile=instfile, pickfile=pickfile,
                        shotfile=shotfile, directory=input_dir, **kwargs)
    # ensure full path for vm programs
    vmfile = os.path.abspath(vmfile)
    rayfile = os.path.abspath(rayfile)
    # set grid size for shortest path algortithm
    vm = readVM(vmfile, head_only=True)
    if grid_size is None:
        grid_size = (vm.nx, vm.ny, vm.nz)
    # set forward star size for 2D cases
    if vm.nx == 1:
        forward_star_size[0] = 0
    elif vm.ny == 1:
        forward_star_size[1] = 0
    # Set bottom-most layer
    if bottom_layer is None:
        bottom_layer = vm.nr
    # Raytrace each instrument
    inst = pickdb.get_ensembles(**kwargs)
    ninst = len(inst)
    if ninst == 0:
        print "No picks found to raytrace that match the search citeria:"
        print kwargs
        return
    print 'Raytracing paths to {:} receiver(s)...'.format(ninst)
    if os.path.isfile(rayfile):
        os.remove(rayfile)
    start_all = time.clock()
    for i, _inst in enumerate(inst):
        # Set flag to leave rayfan file open for additional instruments
        if i == 0:
            irayfile_exists = 0
        else:
            irayfile_exists = 1
        recx, recy, recz = pickdb.get_vmtomo_instrument_position(_inst)
        # Build input
        print ' Tracing rays for receiver #{:} ({:} of {:})'\
                .format(_inst, i + 1, ninst)
        sh = '#!/bin/bash\n'
        sh += '#\n'
        sh += '{:} << eof\n'.format(RAYTR_PROGRAM)
        sh += '{:}\n'.format(vmfile)
        sh += '{:}\n'.format(_inst)
        sh += '{:},{:},{:}\n'.format(grid_size[0], grid_size[1], grid_size[2])
        sh += '{:}\n'.format(1. / min_velocity)
        sh += '{:}\n'.format(max_node_size)
        sh += '{:<10.5f} {:<10.5f} {:<10.5f}\n'.format(recx, recy, recz)
        sh += '{:},{:}\n'.format(top_layer, bottom_layer)
        sh += '{:},{:},{:}\n'.format(forward_star_size[0],
                                     forward_star_size[1],
                                     forward_star_size[2])
        sh += '{:}\n'.format(min_angle)
        sh += '{:}\n'.format(input_dir + '/' + shotfile)
        sh += '{:}\n'.format(input_dir + '/' + pickfile)
        sh += '{:}\n'.format(rayfile)
        sh += '{:}\n'.format(irayfile_exists)
        sh += '0.0\n'  # XXX seting instrument static to 0. here!
                       # TODO take as input
        sh += 'eof\n'

        start = time.clock()
        if os.path.isfile(rayfile):
            raysize0 = os.path.getsize(rayfile)
        else:
            raysize0 = 0
        if verbose:
            subprocess.call(sh, shell=True, stdout=stdout, stderr=stderr)
        else:
            with open(os.devnull, "w") as fnull:
                subprocess.call(sh, shell=True, stdout=fnull, stderr=stderr)
        elapsed = (time.clock() - start)
        if os.path.isfile(rayfile):
            raysize1 = os.path.getsize(rayfile)
        else:
            raysize1 = 0
        if raysize1 == raysize0:
            msg = 'Did not appear to trace rays for receiver #{:}'\
                    .format(_inst)
            warnings.warn(msg)
        print 'Completed raytracing for receiver #{:} in {:} seconds.'\
            .format(_inst, elapsed)
    print 'Completed raytracing for all recievers in {:} seconds.'\
            .format(time.clock() - start_all)
    if os.path.isfile(rayfile):
        print 'Output rayfile is: {:}'.format(rayfile)
    else:
        msg = 'Did not create a rayfile.'
        warnings.warn(msg)
    if cleanup:
        try:
            os.rmdir(input_dir)
        except:
            pass
