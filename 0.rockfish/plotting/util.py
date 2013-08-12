"""
General plotting utilities.
"""

MPL_COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

def get_mpl_color(n, colors=MPL_COLORS, cycle=True):
    """
    Takes an integer and returns a :mod:`matplotlib` color name.

    :param n: Index of the color to return.
    :param colors: Optional. ``list`` of color names. Default is to use the
        list of standard :mod:`matplotlib` colors.
    :param cycle: Optional. Determines whether to repeat colors if ``n``
        is greater than the number of colors in ``colors``. If ``True``, colors
        are recycled. If ``False``, the last color in the list is returned for
        all ``n > len(colors) - 1``. Default is ``True``.
    :returns: :mod:`matplotlib` color name
    """
    ncolors = len(colors)
    if cycle:
        while n > ncolors - 1:
            n -= ncolors
    else:
        n = min(n, ncolors - 1)
    return MPL_COLORS[n]
