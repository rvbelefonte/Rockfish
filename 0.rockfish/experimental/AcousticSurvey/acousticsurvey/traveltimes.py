"""
Methods for calculating travel times.
"""
import numpy as np

def slant_time(sx, sy, sz, rx, ry, rz, v, crs={'epsg':4326}):
    """
    Calculate travel time between a source and receiver.

    :param sx, sy, sz: Cartesian coordinates for the 
        source position.
    :param rx, ry, rz: Cartesian coordinates for the receiver position.
    :param v: Velocity.
    :param crs: Optional. Dictionary of values for the coordinate
        reference system. Default is a geographic using the WGS84 
        ellipsoid and vertical datum (EPSG 4326).
    :returns: Travel-time between the source and receiver
    """
    # TODO project to get horizontal distance!
    return v*np.sqrt((rx-sx)**2+(ry-sy)**2+(rz-sz)**2)
