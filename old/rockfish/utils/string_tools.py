"""
Tools for working with strings.
"""

def pad_string(msg, char=' ', width=78):
    """
    Center a string in a fixed-width line.

    :param char: Character to fill the pad with. Default is 
        ``' '``.
    :param width:  Width of the line. Default is 78.
    """
    npad = (width - len(msg))/2
    return char*npad + msg + char*npad
