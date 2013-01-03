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

    >>> from rockfish.equations.anisotropy import transverse_p
    >>> transverse_p([0, 45, 90], 66.14, 3.66, 0.71)
    array([ 8.39702328,  8.08888126,  7.9492138 ])
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

    >>> from rockfish.equations.anisotropy import velocity2delay_time 
    >>> velocity2delay_time([7.5, 8.0, 8.5], 50., 7.5)
    array([ 0.        , -0.41666667, -0.78431373])
    """
    _vel = np.asarray(velocity)
    if reference_velocity is None:
        vel0 = _vel.mean()
    else:
        vel0 = reference_velocity
    return distance/_vel - distance/vel0

if __name__ == "__main__":
    import doctest
    doctest.testmod()
