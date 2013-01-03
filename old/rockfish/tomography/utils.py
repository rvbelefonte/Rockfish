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

def update_model_id(current_id, step=0, iterate=1):
    """
    Update a <step>.<iter> formated model number.

    :param current_id: String with the current model id in the format
        <step_number>.<iteration_number>
    :param step: Scalar integer to advance the model step number by. Default
        is ``0``.
    :param iterate: Scalar integer to advance the model iteration number by.
        Default is ``1``.
    """
    parts = current_id.split('.')
    _step, _iter = [int(v) for v in parts[0:2]]
    _step += step
    _iter += iterate
    new_id = '{:02d}.{:02d}'.format(_step, _iter)
    if len(parts) > 2:
        new_id += '.'
        new_id += '.'.join(parts[2:])
    return new_id

