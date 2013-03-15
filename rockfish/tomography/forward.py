"""
Wrappers for VM Tomography raytracing
"""
import os
import subprocess
import warnings
import time
from rockfish.tomography import readVM

RAYTR_PROGRAM = 'slim_rays'

def raytrace_from_ascii(vmfile, rayfile, instfile='inst.dat',
                        shotfile='pick.dat', pickfile='shots.dat',
                        grid_size=None, forward_star_size=[12, 12, 24],
                        min_angle=0.5, min_velocity=1.4, max_node_size=620,
                        top_layer=0, bottom_layer=None, stdout=None,
                        stderr=None, verbose=True):
    """
    Wrapper for running the VM Tomography raytracer using a ASCII input files.

    Parameters
    ----------
    vmfile : str
        Filename of the VM Tomography slowness model to raytrace.
    rayfile : str
        Filename of the output VM Tomography rayfan file.
    instfile : str
        Filename of the ASCII-formatted instrument location file with 
        the four columns: ``inst_id, x, y, z``.
    shotfile : str
        Filename of the ASCII-formatted shot location file with 
        the four columns: ``shot_id, x, y, z``.
    pickfile : str
        Filename of the ASCII-formatted pick time file with 
        the seven columns: ``inst_id, shot_id, branch, subbranch_id, range,
        pick_time, pick_error``.
    grid_size : (int, int, int), optional
        Tuple of ``(nx, ny, nz)`` dimensions for the graphing grid. Default is        to match the graphing grid to the slowness model dimensions.
    min_angle : float, optional
        Minimum angle between search directions in forward star in degrees.
    min_velocity : float, optional
        Minimum velocity to trace rays through.
    max_node_size : int, optional
        Average number of nodes to allocate for each raypath. The raytracing
        program will adjust this size if needed.
    top_layer : int, optional
        The index of the top-most layer to trace rays through.
    bottom_layer : int, optional
        The index of the bottom-most layer to trace rays through. Default is
        the index of the bottom-most layer in the model.
    stdout, stderr : {'PIPE', int, file, None}, optional
        stdout and stderr specify the raytracing program's standard
        output and standard error file handles, respectively. Valid values
        are ``'PIPE'``, an existing file descriptor (a positive
        integer), an existing file object, and ``None``. See :mod:`subprocess`        for more information.
    verbose : {bool, int}, optional
        Determines whether or not to print information from the
        raytracing program.  Valid values are ``True``, ``False``, or numeric
        level.
    """
    # set numeric verbosity level
    if verbose and (type(verbose) == bool):
        verbose = 4
    #XXX # ensure full path for vm programs
    #vmfile = os.path.abspath(vmfile)
    #rayfile = os.path.abspath(rayfile)
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
    # Get instrument locations
    finst = open(instfile, 'rb')
    inst = {}
    for row in finst:
        dat = row.split()
        inst[int(dat[0])] = [float(d) for d in dat[1:4]]
    finst.close()
    # Raytrace each instrument
    ninst = len(inst)
    if verbose >= 2:
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
        recx, recy, recz = inst[_inst]
        # Build input
        if verbose >= 3:
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
        sh += '{:}\n'.format(shotfile)
        sh += '{:}\n'.format(pickfile)
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
        if verbose >= 4:
            subprocess.call(sh, shell=True, stdout=stdout,
                                         stderr=stderr)
        else:
            with open(os.devnull, "w") as fnull:
                subprocess.call(sh, shell=True, stdout=fnull,
                                stderr=stderr)
        elapsed = (time.clock() - start)
        if os.path.isfile(rayfile):
            raysize1 = os.path.getsize(rayfile)
        else:
            raysize1 = 0
        if (raysize1 == raysize0) and verbose >= 1:
            msg = 'Did not appear to trace rays for receiver #{:}'\
                    .format(_inst)
            warnings.warn(msg)
        if verbose >= 3:
            print 'Completed raytracing for receiver #{:} in {:} seconds.'\
                .format(_inst, elapsed)
    if verbose >= 2:
        print 'Completed raytracing for all recievers in {:} seconds.'\
                .format(time.clock() - start_all)
    if os.path.isfile(rayfile) and verbose > 1:
        print 'Output rayfile is: {:}'.format(rayfile)
    elif not os.path.isfile(rayfile) and (verbose >= 1):
        msg = 'Did not create a rayfile.'
        warnings.warn(msg)



def raytrace(vmfile, pickdb, rayfile, pick_keys={}, input_dir='forward',
             cleanup=True, grid_size=None, forward_star_size=[12, 12, 24],
             min_angle=0.5, min_velocity=1.4, max_node_size=620,
             top_layer=0, bottom_layer=None, stdout=None, stderr=None,
             verbose=True, step=1, **kwargs):
    """
    Wrapper for running the VM Tomography raytracer using a pick database.

    Uses pick data in a
        :class:`rockfish.picking.database.PickDatabaseConnection` to build
        required input files on-the-fly and executes the tracer.

    Parameters
    ----------
    vmfile : str
        Filename of the VM Tomography slowness model to raytrace.
    rayfile : str
        Filename of the output VM Tomography rayfan file.
    pickdbfile : :class:`rockfish.picking.database.PickDatabaseConnection`
        Database connection to get shot locations, instrument locations, 
        and pick times from.
    input_dir : str, optional
        Path for writing ASCII data files that are used as input to the 
        raytracing program. 
    cleanup : bool, optional
        Determines whether or not to remove the files that are created for
        input to the raytracing program.
    grid_size : (int, int, int), optional
        Tuple of ``(nx, ny, nz)`` dimensions for the graphing grid. Default is        to match the graphing grid to the slowness model dimensions.
    min_angle : float, optional
        Minimum angle between search directions in forward star in degrees.
    min_velocity : float, optional
        Minimum velocity to trace rays through.
    max_node_size : int, optional
        Average number of nodes to allocate for each raypath. The raytracing
        program will adjust this size if needed.
    top_layer : int, optional
        The index of the top-most layer to trace rays through.
    bottom_layer : int, optional
        The index of the bottom-most layer to trace rays through. Default is
        the index of the bottom-most layer in the model.
    stdout, stderr : {'PIPE', int, file, None}, optional
        stdout and stderr specify the raytracing program's standard
        output and standard error file handles, respectively. Valid values
        are ``'PIPE'``, an existing file descriptor (a positive
        integer), an existing file object, and ``None``. See :mod:`subprocess`        for more information.
    verbose : bool, optional
        Determines whether or not to print detailed information from the
        raytracing program.
    step : int
        Specifies the increment of picks in the database to raytrace. Useful
        for raytracing a subset of the picks.
    **kwargs : keyword=value arguments, optional
        Field values to use when selecting picks from the database to
        raytrace.
    """
    # Make the input files
    instfile = 'inst.dat'
    pickfile = 'picks.dat'
    shotfile = 'shots.dat'
    if not os.path.isdir(input_dir):
        new_dir = True
        os.mkdir(input_dir)
    else:
        new_dir = False
    pickdb.write_vmtomo(instfile=instfile, pickfile=pickfile,
                        shotfile=shotfile, directory=input_dir, 
                        step=step, **kwargs)
    # Run the raytracer
    raytrace_from_ascii(vmfile, rayfile, 
                        instfile=os.path.join(input_dir, instfile),
                        shotfile=os.path.join(input_dir, shotfile),
                        pickfile=os.path.join(input_dir, pickfile),
                        grid_size=grid_size,
                        forward_star_size=forward_star_size,
                        min_angle=min_angle, min_velocity=min_velocity,
                        max_node_size=max_node_size, top_layer=top_layer,
                        bottom_layer=bottom_layer, stdout=stdout,
                        stderr=stderr, verbose=verbose)
    # Remove the input files
    if cleanup:
        for f in [instfile, pickfile, shotfile]:
            _f = os.path.join(input_dir, f)
            if os.path.isfile(_f):
                os.remove(_f)
        if new_dir:
            os.rmdir(input_dir)
