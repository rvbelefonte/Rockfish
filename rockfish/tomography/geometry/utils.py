"""
Geometry utilities
"""
import numpy as np

def line_plane_isect(p1, p2, p3, l1, l2):

    a = [[    1,     1,     1,     1],
         [p1[0], p2[0], p3[0], l1[0]],
         [p1[1], p2[1], p3[1], l1[1]],
         [p1[2], p2[2], p3[2], l1[2]]]
    b = [[    1,     1,     1,     0],
         [p1[0], p2[0], p3[0], l2[0] - l1[0]],
         [p1[1], p2[1], p3[1], l2[1] - l1[1]],
         [p1[2], p2[2], p3[2], l2[2] - l1[2]]]

    t = - np.linalg.det(a)/np.linalg.det(b)

    x = l1[0] + (l2[0] - l1[0]) * t
    y = l1[1] + (l2[1] - l1[1]) * t
    z = l1[2] + (l2[2] - l1[2]) * t

    return x, y, z

def sign(p1, p2, p3):

    return (p1[0] - p3[0]) * (p2[1] - p3[1])\
            - (p2[0] - p3[0]) * (p1[1] - p3[1])

def point_in_poly(p1, p2, p3, x, y, z):

    b1 = sign([x, y], p1, p2) < 0.0
    b2 = sign([x, y], p2, p3) < 0.0
    b3 = sign([x, y], p3, p1) < 0.0

    return ((b1 == b2) and (b2 == b3))
