"""
Wrappers for working with the VM Tomography raytracing program.
"""
import os
import subprocess
import time
from rockfish.vmtomo.vm import VM

RAYTR_PROG = 'slim_rays'

def trace(vmfile, pickdb, rayfile, input_dir=None, cleanup=True, 
          grid_size=None, forward_star_size=[6, 6, 12], min_angle=0.5,
          min_velocity=1.4, max_node_size=620, top_layer=1, bottom_layer=None,
          **kwargs):
    """
    :param vmfile: Filename of the VM Tomography slowness model to
        raytrace.
    :param rayfile: Filename of the output rayfan file.
    :param pickdbfile: Active 
        :class:`rockfish.picking.database.PickDatabaseConnection` to get picks
        from.
    :param input_dir: Optional. Path for writing intermediate files that are
        used as input to the raytracing program. Default is to put these files
        in the current working directory.
    :param cleanup: Optional. Determines whether or not to remove intermediate
        files that are used as input to the raytracing program. Default is to
        remove these files.
    :param grid_size: Optional. ``(nx, ny, nz)`` tuple with dimensions for the 
        graphing grid. Default is to match the graphing grid to the slowness
        model dimensions.
        for the forward star. Default is (6, 6, 12). If model is 2D (ny = 1),
        the y-dimension for the forward star is set to ``0``.
    :param min_angle: Optional. Minimum angle between search directions in
        forward star in degrees. Default is ``0.5``.
    :param min_velocity: Optional. Minimum velocity to trace rays through. 
        Default is ``1.4``.
    :param max_node_size: Optional. Average number of nodes to allocate for
        each raypath. The raytracing program will adjust this size if needed.
        Default is ``620``.
    :param top_layer: Optional. The index of the top-most layer to trace rays
        through. Default is ``1`` (i.e., the top-most layer in the model).
    :param bottom_layer: Optional. The index of the bottom-most layer to trace
        rays through. Default is the index of the bottom-most layer in the
        model.
    :param **kwargs: keyword=value arguments used to select picks to output
    """
    # Make the input files
    instfile = 'inst.dat'
    pickfile = 'picks.dat'
    shotfile = 'shots.dat'
    if input_dir is not None:
        if not os.path.isdir(input_dir):
            os.mkdir(input_dir)
    else:
        input_dir = '.'
    pickdb.write_vmtomo(instfile=instfile, pickfile=pickfile, 
                        shotfile=shotfile, directory=input_dir, **kwargs)
    # set grid size for shortest path algortithm
    vm = VM(vmfile, head_only=True)
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
    inst = pickdb.ensembles
    ninst = len(inst)
    if os.path.isfile(rayfile):
        os.remove(rayfile)
    for i,_inst in enumerate(inst):
        # Set flag to leave rayfan file open for additional instruments
        if i == ninst - 1:
            iheader = 0
        else:
            iheader = 1
        recx, recy, recz = pickdb.get_vmtomo_instrument_position(_inst)
        # Build input
        print '='*80
        print ' Tracing rays for receiver #{:} ({:} of {:})'\
                .format(_inst, i+1, ninst)
        print '='*80
        sh = '#!/bin/bash\n'
        sh += '#\n'
        sh += '{:} << eof\n'.format(RAYTR_PROG)
        sh += '{:}\n'.format(vmfile)
        sh += '{:}\n'.format(_inst)
        sh += '{:},{:},{:}\n'.format(grid_size[0], grid_size[1], grid_size[2])
        sh += '{:}\n'.format(1./min_velocity)
        sh += '{:}\n'.format(max_node_size)
        sh += '{:},{:},{:}\n'.format(recx, recy, recz)
        sh += '{:},{:}\n'.format(top_layer, bottom_layer)
        sh += '{:},{:},{:}\n'.format(forward_star_size[0], 
                                     forward_star_size[1],
                                     forward_star_size[2])
        sh += '{:}\n'.format(min_angle)
        sh += '{:}\n'.format(input_dir + '/' + shotfile)
        sh += '{:}\n'.format(input_dir + '/' + pickfile)
        sh += '{:}\n'.format(rayfile)
        sh += '{:}\n'.format(iheader)
        sh += '0.0\n' #XXX seting instrument static to 0. here! 
                      #TODO take as input
        sh += 'eof\n'

        print sh
        start = time.clock()
        subprocess.call(sh, shell=True)
        elapsed = (time.clock() - start)
        print '*'*80
        print ' Completed raytracing for receiver #{:} in {:} seconds.'\
                .format(_inst, elapsed)
        print '*'*80
