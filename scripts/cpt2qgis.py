#!/usr/bin/env python
"""
Utility to convert a GMT *.cpt file into a QGIS color map.

From https://raw.github.com/pism/pypismtools/master/scripts/qgis-colorramp.py
"""
import numpy as np
import pylab as plt
import matplotlib as mpl
from argparse import ArgumentParser


def gmtColormap(fileName, log_color=False, reverse=False, scale=1.0):
    '''
    Import a CPT colormap from GMT.

    Parameters
    ----------
    fileName : a cpt file.

    Example
    -------
    >>> cdict = gmtColormap("mycolormap.cpt")
    >>> gmt_colormap = colors.LinearSegmentedColormap("my_colormap", cdict)

    Notes
    -----
    This code snipplet modified after
    http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg09547.html
    '''
    import colorsys

    try:
        f = open(fileName)
    except:
        print "file ", fileName, "not found"
        return None

    lines = f.readlines()
    f.close()

    x = []
    r = []
    g = []
    b = []
    colorModel = "RGB"
    for l in lines:
        ls = l.split()
        if l[0] == "#":
            if ls[-1] == "HSV":
                colorModel = "HSV"
                continue
            else:
                continue
        if ls[0] == "B" or ls[0] == "F" or ls[0] == "N":
            pass
        else:
            x.append(float(ls[0]))
            r.append(float(ls[1]))
            g.append(float(ls[2]))
            b.append(float(ls[3]))
            xtemp = float(ls[4])
            rtemp = float(ls[5])
            gtemp = float(ls[6])
            btemp = float(ls[7])

    x.append(xtemp)
    r.append(rtemp)
    g.append(gtemp)
    b.append(btemp)

    if reverse:
        r.reverse()
        g.reverse()
        b.reverse()

    x = np.array(x, np.float32)

    print x.min(), x.max()

    if scale:
        print   '  scaling data values by {:} ...'.format(scale)
        x *= scale
    
    print x.min(), x.max()

    r = np.array(r, np.float32)
    g = np.array(g, np.float32)
    b = np.array(b, np.float32)
    if colorModel == "HSV":
        for i in range(r.shape[0]):
            rr, gg, bb = colorsys.hsv_to_rgb(r[i] / 360., g[i], b[i])
            r[i] = rr
            g[i] = gg
            b[i] = bb
    if colorModel == "HSV":
        for i in range(r.shape[0]):
            rr, gg, bb = colorsys.hsv_to_rgb(r[i] / 360., g[i], b[i])
            r[i] = rr
            g[i] = gg
            b[i] = bb
    if colorModel == "RGB":
        r = r / 255.
        g = g / 255.
        b = b / 255.
        
    if log_color:
        xNorm = np.zeros((len(x), ))
        xNorm[1::] = np.logspace(-1,0,len(x) - 1)
        xNorm[1::-2] /= 4
    else:
        xNorm = (x - x[0]) / (x[-1] - x[0])

    red = []
    blue = []
    green = []
    for i in range(len(x)):
        red.append([xNorm[i], r[i], r[i]])
        green.append([xNorm[i], g[i], g[i]])
        blue.append([xNorm[i], b[i], b[i]])
    colorDict = {'red': red, 'green': green, 'blue': blue}
    return (colorDict)


def cmap_map(function, cmap):
    """
    Applies function (which should operate on vectors of shape 3:
    [r, g, b], on colormap cmap. This routine will break any discontinuous points
    in a colormap.

    Adapted from http://www.scipy.org/Cookbook/Matplotlib/ColormapTransformations
    """
    cdict = cmap._segmentdata
    step_dict = {}
    # First get the list of points where the segments start or end
    for key in ('red' ,'green' ,'blue'):
	    step_dict[key] = map(lambda x: x[0], cdict[key])
    step_list = sum(step_dict.values(), [])
    step_list = np.array(list(set(step_list)))
    # Then compute the LUT, and apply the function to the LUT
    reduced_cmap = lambda step : np.array(cmap(step)[0:3])
    old_LUT = np.array(map(reduced_cmap, step_list))
    new_LUT = np.array(map(function, old_LUT))
    # Now try to make a minimal segment definition of the new LUT
    cdict = {}
    for i, key in enumerate(('red', 'green', 'blue')):
        this_cdict = {}
        for j, step in enumerate(step_list):
            if step in step_dict[key]:
                this_cdict[step] = new_LUT[j, i]
            elif new_LUT[j,i]!=old_LUT[j,i]:
                this_cdict[step] = new_LUT[j, i]
        colorvector=  map(lambda x: x + (x[1], ), this_cdict.items())
        colorvector.sort()
        cdict[key] = colorvector

    return mpl.colors.LinearSegmentedColormap('colormap', cdict, 1024)


if __name__ == "__main__":

    # Set up the option parser
    parser = ArgumentParser()
    parser.description = """
    A script to convert a GMT (*.cpt) colormap or matplotlib colormap into QGIS-readable color ramp.
    """
    parser.add_argument("FILE", nargs='*')
    parser.add_argument("--log",dest="log", action="store_true",
                      help="make a log-normalized color scale", default=False)
    parser.add_argument("--scale",dest="scale", type=float,
                      help="scale values in output colormap", default=1.0)
    parser.add_argument("--joughin_speed", dest="joughin_speed", action="store_true",
                      help='''
                      Joughin-style log''', default=False)
    parser.add_argument("--habermann_tauc", dest="habermann_tauc", action="store_true",
                      help='''
                      log tauc scaling from Habermann et al (2013)''', default=False)
    parser.add_argument("--colorbar_label", dest="colorbar_label",
                      help='''Label for colorbar.''', default=None)
    parser.add_argument("-a", "--a_log", dest="a", type=float,
                      help='''
                      a * logspace(vmin, vmax, N)''', default=1)
    parser.add_argument("--vmin", dest="vmin", type=float,
                      help='''
                      a * logspace(vmin, vmax, N)''', default=-1)
    parser.add_argument("--vmax", dest="vmax", type=float,
                      help='''
                      a * logspace(vmin, vmax, N)''', default=3)
    parser.add_argument("--extend", dest="extend", nargs=2, type=float,
                      help='''
                      appends color ramp by repeating first and last color for value''',
                        default=None)
    parser.add_argument("--N", dest="N", type=int,
                      help='''
                      a * logspace(vmin, vmax, N''', default=1022)
    parser.add_argument("-r", "--reverse",dest="reverse", action="store_true",
                      help="reverse color scale", default=False)

    options = parser.parse_args()
    args = options.FILE
    joughin_speed = options.joughin_speed
    habermann_tauc = options.habermann_tauc
    a = options.a
    log = options.log
    extend = options.extend
    N = options.N
    vmin = options.vmin
    vmax = options.vmax
    reverse = options.reverse
    scale = options.scale
    colorbar_label = options.colorbar_label
    # experimental
    log_color = False

    # read in CPT colormap
    for k in range(len(args)):

        cmap_file = args[k]
        print cmap_file
        try:
                cdict = plt.cm.datad[cmap_file]
                prefix = cmap_file
        except:
                # import and convert colormap
                cdict = gmtColormap(cmap_file, log_color=log_color, reverse=reverse, scale=scale)
                prefix = '.'.join(cmap_file.split('.')[0:-1])
                suffix = cmap_file.split('.')[-1]


        # either log scaling or linear scaling (default)
        if joughin_speed:
                # This is a little duck-punching to get a QGIS colormap
                # similar to Joughin (2010)
                vmin = 0
                vmax = 4
                a = 3
                data_values = np.logspace(vmin, vmax, N)[0:889]
                data_values[-1] = 3000
                N = len(data_values)
                norm = mpl.colors.LogNorm(vmin=1, vmax = 3000)
                ticks = np.hstack((np.logspace(vmin, vmax, vmax - vmin + 1), a * (10 ** vmax)))
                ticks = [1, 3, 10, 30, 100, 1000, 3000]
                format = '%i'
                cb_extend = 'both'
                colorbar_label = 'm a$^{-1}$'
        elif habermann_tauc:
                # This is a little duck-punching to get a QGIS colormap
                # similar to Joughin (2010)
                vmin = 1e4
                vmax = 3e5
                data_values = np.logspace(np.log10(vmin), np.log10(vmax), N)
                norm = mpl.colors.LogNorm(vmin=vmin, vmax = vmax)
                ticks = [vmin, vmax]
                format = '%i'
                cb_extend = 'both'
        elif log:
            data_values = a * np.logspace(vmin, vmax, N)
            norm = mpl.colors.LogNorm(vmin=(10 ** vmin), vmax = a * (10 ** vmax))
            ticks = np.hstack((np.logspace(vmin, vmax, vmax - vmin + 1), a * (10 ** vmax)))
            ticks = [1, 3, 10, 30, 100, 1000, 3000]
            format = '%i'
            cb_extend = 'both'
        elif log_color:
            data_values = a * np.logspace(vmin, vmax, N)
            norm = mpl.colors.LogNorm(vmin= (10 ** vmin) - 0.01, vmax = a * (10 ** vmax))
            ticks = [1, 3, 10, 30, 100, 1000, 3000]
            format = '%i'
            cb_extend = 'both'
        else:
            data_values = a * np.linspace(vmin, vmax, N)
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
            ticks = None
            format = None
            cb_extend = 'both'

        cmap = mpl.colors.LinearSegmentedColormap('my_colormap', cdict, N)

        # you could apply a function to the colormap, e.g. to desaturate the colormap:
        # cmap = cmap_map(lambda x: x/2+0.5, cmap)

        # create the colorbar
        fig = plt.figure()
        ax1 = fig.add_axes([0.05, 0.65, 0.9, 0.05])
        cb1 = mpl.colorbar.ColorbarBase(ax1,
                                        cmap=cmap,
                                        norm = norm,
                                        ticks=ticks,
                                        format=format,
                                        extend=cb_extend,
                                        spacing='proportional',
                                        orientation='horizontal')

        if colorbar_label:
                cb1.set_label(colorbar_label)

        # save high-res colorbar as png
        out_file = '.'.join([prefix, 'png'])
        print("  writing colorbar %s ..." % out_file)
        fig.savefig(out_file, bbox_inches='tight', dpi=1200)


        # convert to RGBA array
        rgba = cb1.to_rgba(data_values, alpha=None)
        # QGIS wants 0..255
        rgba *= 255

        # create an output array combining data values and rgb values
        if extend:
                qgis_array = np.zeros((N + 2, 5))
                for k in range(0, N):
                        qgis_array[k+1, 0] = data_values[k]
                        qgis_array[k+1, 1:4] = rgba[k, 0:3]
                        qgis_array[k+1, 4] = 255
                # repeat first color
                qgis_array[0, 0] = extend[0]
                qgis_array[0, 1:4] = rgba[0, 0:3]
                qgis_array[0, 4] = 255
                # repeat last color
                qgis_array[-1, 0] = extend[1]
                qgis_array[-1, 1:4] = rgba[-1, 0:3]
                qgis_array[-1, 4] = 255
        else:
                qgis_array = np.zeros((N, 5))
                for k in range(N):
                        qgis_array[k, 0] = data_values[k]
                        qgis_array[k, 1:4] = rgba[k, 0:3]
                        qgis_array[k, 4] = 255

        # save as ascii file
        out_file = '.'.join([prefix, 'txt'])
        print("  writing colorramp %s ..." % out_file)
        np.savetxt(out_file, qgis_array, delimiter=',', fmt=['%10.5f', '%i', '%i', '%i', '%i,'])

