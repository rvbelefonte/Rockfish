"""
Utilities for tomography programs.
"""
import os
from scipy.io import netcdf_file as netcdf

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


def update_model_id(current_id, step=0, iterate=1):
    """
    Update a <step>.<iteration> formated model number.

    :param current_id: String with the current model id in the format
        <step_number>.<iteration_number>
    :param step: Scalar integer to advance the model step number by. Default
        is ``0``.
    :param iterate: Scalar integer to advance the model iteration number by.
        Default is ``1``.
    """
    path = os.path.dirname(current_id)
    parts = os.path.basename(current_id).split('.')
    assert len(parts) >= 2, 'Model ID must have the format <step>.<iteration>.'
    _step, _iter = [int(v) for v in parts[0:2]]
    _step += step
    _iter += iterate
    fmt = '{:0' + str(len(parts[0]))\
            + 'd}.{:0' + str(len(parts[1])) + 'd}'
    new_id = fmt.format(_step, _iter)
    if len(parts) > 2:
        new_id += '.'
        new_id += '.'.join(parts[2:])
    return os.path.join(path, new_id)


def cleanup_iterations(first_id, last_id=None):
    """
    Remove models and rayfans from the current directory.

    :param first_id: String for the id of the first iteration to remove. 
    :param last_id: String for the id of the last iteration to remove. 
    """
    current_id = first_id
    next_id = update_model_id(first_id)
    while os.path.isfile(current_id) and (next_id != last_id):
        os.remove(current_id)
        current_id = next_id
        next_id = update_model_id(current_id)
