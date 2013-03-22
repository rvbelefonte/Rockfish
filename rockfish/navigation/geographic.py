"""
Utilities for working with geographic coordinates
"""
import numpy as np
from pyproj import Geod


def divide_line(pts, spacing=6.25, runin=0.,
                ellps='WGS84', isegment0=0):
    """
    Divide a line into equally spaced segments.

    Parameters
    ----------
    pts : list of tuples 
        List of point coordinates in longitude and latitude that define the
        line.  Format is: ``[(lon_0, lat_0), (lon_1, lat_1), ...,
        (lon_n, lat_n)]``.
    spacing : float, optional
        Spacing between line segments in meters.
    runin : float, optional
        Length of a "run-in" segment prepended to the line.
    ellps : str, optional
        Name of the ellipse to use in geodetic calculations. Must be
        recognized by :class:`pyproj.Geod`.
    isegment0 : int, optional
        Sequence number of the first bin.

    Returns
    -------
    bins : list
        List of (lon, lat, offset, sequence) tuples.
    """
    gd = Geod(ellps=ellps)
    x = -runin
    _x = -runin
    ibin = isegment0
    bins = []
    for i in range(0, len(pts) - 1):
        _x0 = _x
        lon0, lat0 = pts[i]
        lon1, lat1 = pts[i + 1]
        faz, baz, dist = gd.inv(lon0, lat0, lon1, lat1)
        while _x <= dist:
            lon, lat, _ = gd.fwd(lon0, lat0, faz, _x)
            bins += [(lon, lat, x, ibin)]
            _x += spacing
            x += spacing
            ibin += 1
        _x -= dist
        x -= _x
        if _x > 0:
            x += _x
            bins += [(lon1, lat1, x, ibin - 1)]
    return bins


def build_bins(pts, spacing=6.25, width=50, runin=0,
               isequence0=1000, ellps='WGS84'):
    """
    Build bins along a line of points.
    """
    gd = Geod(ellps=ellps)
    div_pts = divide_line(pts, spacing=spacing,
                          runin=runin, ellps=ellps)
    bins = []
    ndiv = len(div_pts)
    ibin = isequence0
    align_to_last_bin = False
    for i in range(0, ndiv - 1):
        lon0, lat0, x0, i0 = div_pts[i]
        lon1, lat1, x1, i1 = div_pts[i + 1]
        faz, baz, dist = gd.inv(lon0, lat0, lon1, lat1)
        # bin corners
        _bin = _build_bin(lon0, lat0, lon1, lat1, width, gd)
        # bin center
        _center = _calculate_center(_bin)
        # put it all together
        bins.append([ibin, None, _center, _bin])
        # handle bends in the line
        if align_to_last_bin:
            # align bins
            bins[-1][3][0] = bins[-2][3][1]
            bins[-1][3][3] = bins[-2][3][2]
            # recalculate center and offset
            bins[-1][2] = _calculate_center(bins[-1][3])
            align_to_last_bin = False
        if i0 == i1:
            ibin -= 1
            i += 1
            _bin = bins[-1]
            del bins[-1]
            align_to_last_bin = True
        # distance on line and line azimuth
        if i == 0:
            bins[-1][1] = div_pts[0][2]
            bins[-1] += [None]
        else:
            az, _, dx = gd.inv(bins[-1][2][0], bins[-1][2][1],
                              bins[-2][2][0], bins[-2][2][1])
            bins[-1][1] = bins[-2][1] + dx
            bins[-1] += [az]
        # increment bin number
        ibin += 1
    # assume first azimuth is the same as 2nd azimuth
    bins[0][4] = [bins[1][4]]
    return bins


def _calculate_center(pts):
    """
    Return coordinates of the center of a polygon.
    """
    return (np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts]))


def _build_bin(lon0, lat0, lon1, lat1, width, gd):
    """
    Build a single bin from segment end points.
    """
    faz, baz, dist = gd.inv(lon0, lat0, lon1, lat1)
    _lon, _lat, _ = gd.fwd(lon0, lat0, faz + 90., width / 2.)
    _bin = []
    # 1st bin corner
    _lon, _lat, _ = gd.fwd(lon0, lat0, faz + 90., width / 2.)
    _bin.append((_lon, _lat))
    # 2nd bin corner
    _lon, _lat, _ = gd.fwd(lon1, lat1, faz + 90., width / 2.)
    _bin.append((_lon, _lat))
    # 3rd bin corner
    _lon, _lat, _ = gd.fwd(lon1, lat1, faz - 90., width / 2.)
    _bin.append((_lon, _lat))
    # 4th bin corner
    _lon, _lat, _ = gd.fwd(lon0, lat0, faz - 90., width / 2.)
    _bin.append((_lon, _lat))
    return _bin
