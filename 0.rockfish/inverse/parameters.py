"""
Utilites for handling parameter ranges
"""
import numpy as np


def meshgrid_from_ranges(aranges, method=np.linspace, indexing='xy'):
    """
    Build a N-D matrix from a set of value ranges.

    Parameters
    ----------
    aranges: list
        Arguments to the callable function given by ``method`` that are
        used to construct the vectors `a1`, `a2`,..., 'an'.
    method: callable function, optional
        A callable function that takes the elements of ``aranges`` as
        arguments. Default is :meth:`numpy.linspace`.
    indexing : {'xy', 'ij'}, optional
        Cartesian ('xy', default) or matrix ('ij') indexing of output.
        See :meth:`numpy.meshgrid` for more details.

    Returns
    -------
    A1, A2, ..., AN : ndarray
        For vectors `a1`, `a2`,..., 'an' with lengths ``Ni=len(ai)`` ,
        return ``(A1, A2, A3,...An)`` shaped arrays if indexing='ij'
        or ``(N2, N1, N3,...Nn)`` shaped arrays if indexing='xy'
        with the elements of `ai` repeated to fill the matrix along
        the first dimension for `a1`, the second for `a2` and so on.

    .. see also:: :meth:`numpy.meshgrid`
    """
    nparam = len(aranges)
    values = []
    for r in aranges:
        values.append(method(*r))
    return np.meshgrid(*values, indexing=indexing)
