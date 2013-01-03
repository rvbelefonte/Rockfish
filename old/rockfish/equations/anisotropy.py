"""
Anisotropy equations.
"""
import numpy as np

def transverse_p(theta, A, B, C):
    """
    Calculate seismic p wavespeeds in transversely isotropic media.

    :param theta: Angle with respect to fast direction in degrees.
    :param A,B,C: P-wave moduli in km^2/s^2.
    :returns: list of p-wavespeeds
    """
    _theta = np.deg2rad(theta)
    return np.sqrt(A+B*np.cos(2*_theta) + C*np.cos(4*_theta))

def velocity2delay_time(velocity, distance, reference_velocity=None):
    """
    Calculate relative travel times for a set of velocities.

    :param vel: List of velocities.
    :param offset: Distance to calculate traveltimes for.
    :param reference_velocity: Velocity to use in calculating a reference
        travel time. Default is to use the mean velocity.
    :returns: List of delay times.
    """
    _vel = np.asarray(velocity)
    if reference_velocity is None:
        vel0 = _vel.mean()
    else:
        vel0 = reference_velocity
    return distance/velocity - distance/vel0
