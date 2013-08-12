"""
Tools for locating sources and receivers in velocity models.
"""
import copy
import numpy as np
import warnings
import subprocess
import matplotlib.pyplot as plt
from rockfish.tomography.model import readVM
from rockfish.tomography.forward import raytrace
from rockfish.tomography.rayfan import readRayfanGroup
from rockfish.picking.database import PickDatabaseConnection


def locate_on_surface(vmfile, pickdb, iref, pick_keys={}, x0=None, y0=None,
                      dx=None, dy=None, plot=False):
    """
    Locate a receiver on a surface.

    :param vmfile: Filename of the VM Tomography slowness model to
        raytrace.
    :param pickdb: :class:`rockfish.picking.database.PickDatabaseConnection`
        to get picks from for raytracing.
    :param iref: index of the surface to move the receiver on
    :param pick_keys: Optional. ``dict`` of keys and values to use for
        selecting picks from ``pickdb``.  Default is to use all picks.
    :param x0, y0: Optional. Initial guess at x and y locations. Default is
        center of the model.
    :param dx, dy: Optional. Distance in x and y to search from ``x0, y0``.
        Default is to search the entire model.
    :param plot: Optional. Plot results of the location. Default is false.
    """
    # Load model
    print "Loading VM model..."
    vm = readVM(vmfile)
    # Setup search domain
    print "Setting up search domain..."
    if x0 is None:
        x0 = np.mean(vm.x)
    if y0 is None:
        y0 = np.mean(vm.y)
    if dx is None:
        xsearch = vm.x
    else:
        ix = vm.xrange2i(max(vm.r1[0], x0 - dx), min(vm.r2[0], x0 + dx))
        xsearch = vm.x[ix]
    if dy is None:
        ysearch = vm.y
    else:
        iy = vm.yrange2i(max(vm.r1[1], y0 - dy), min(vm.r2[1], y0 + dy))
        ysearch = vm.y[iy]
    # trace each point in the search region
    print "Building traveltime database for {:}x{:} search grid..."\
            .format(len(xsearch), len(ysearch))
    zz = vm.rf[iref]
    ipop = -1
    population = []
    db = PickDatabaseConnection(':memory:')
    for x in xsearch:
        for y in ysearch:
            z = zz[vm.x2i([x])[0], vm.y2i([y])[0]]
            ipop += 1
            for _p in pickdb.get_picks(**pick_keys):
                p = dict(_p)
                p['ensemble'] = ipop 
                p['receiver_x'] = x
                p['receiver_y'] = y
                p['receiver_z'] = z
                db.add_pick(**p)
            population.append((x, y, z))
    print "Raytracing..."
    rayfile = '.locate.ray'
    raytrace(vmfile, db, rayfile, stderr=subprocess.STDOUT,
             stdout=subprocess.PIPE)
    rays = readRayfanGroup(rayfile)
    imin = np.argmin([rfn.rms for rfn in rays.rayfans]) 
    ipop = [rfn.start_point_id for rfn in rays.rayfans][imin]
    rms = [rfn.rms for rfn in rays.rayfans][imin]
#    # warn if fit point is on edge of search domain
#    if (vm.ny > 1) and ((yfit == ysearch[0]) or (yfit == ysearch[-1])):
#        on_edge = True
#    elif (xfit == xsearch[0]) or (xfit == xsearch[-1]):
#        on_edge = True
#    else:
#        on_edge = False
#    if on_edge:
#        msg = 'Best-fit location ({:},{:}) is on edge of model domain:'\
#                .format(xfit, yfit)
#        msg += ' x=[{:},{:}], y=[{:},{:}].'.format(xsearch[0], xsearch[-1],
#                                                   ysearch[0], ysearch[-1])
#        msg += ' Try using a larger search region.'
#        warnings.warn(msg)
    # plot
    if plot:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        if vm.ny == 1:
            ax.plot([p[0] for p in population], 
                    [rfn.rms for rfn in rays.rayfans], '.k')
            ax.plot(population[ipop][0], rms, '*r')
            plt.xlabel('x (km)')
            plt.ylabel('RMS error (s)')
        else:
            ax.plot([p[0] for p in population], [p[1] for p in population],
                    '.k')
            ax.plot(population[ipop][0], population[ipop][1], '*r')
            ax.plot(x0, y0, 'og')
            plt.xlabel('x (km)')
            plt.xlabel('y (km)')
        plt.title('Results of locate_on_surface()')
        plt.show()
    return population[ipop][0], population[ipop][1], population[ipop][2], rms
