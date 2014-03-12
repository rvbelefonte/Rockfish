"""
Anisotropy equations
"""
from numpy import sin, cos, deg2rad

# Anisotropy parameters
e12 = lambda a11, a12, a22, a66: 2 * (a12 + 2 * a66) - (a11 + a22)
e13 = lambda a11, a13, a33, a55: 2 * (a13 + 2 * a55) - (a11 + a33)
e23 = lambda a22, a23, a33, a44: 2 * (a23 + 2 * a44) - (a22 + a33)

# Azimuth and dip dependence
# TODO n_rad = lambda theta, phi: sin(theta) * cos(phi) 

# Group slowness
# TODO ug2 = 


