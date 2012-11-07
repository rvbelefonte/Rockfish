"""
General utilities for working with databases.
"""
def format_row_factory(rows, none_value=None):
    """
    Dump list of :class:`sqlite3.Row` instances to a string.
    
    :param rows: list of :class:`sqlite3.Row`
    :param none_value: value to replace ``None`` values with
    :returns: string with all row data
    """
    sng = ''
    for row in rows:
        for v in row:
            if v is None:
                v = none_value
            sng += '{:} '.format(v)
        sng += '\n'
    return sng
