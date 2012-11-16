"""
Utilities for tomography programs.
"""
def python2fortran_bool(py):
    """
    Converts a python bool to single-letter string input for fortran.
    """
    if py is True:
        return 'T'
    else:
        return 'F'

def bool2int(var):
    """
    Converts a boolean variable to a 0 (false) or 1 (true).
    """
    if var is True:
        return 1
    else:
        return 0
