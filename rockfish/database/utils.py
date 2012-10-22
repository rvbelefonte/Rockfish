"""
General utilities for working with databases.
"""
def format_row_factory(rows):
    """
    Dump list of :class:`sqlite3.Row` instances to a string.
    
    :param filename: name of file to write data to
    :param rows: list of :class:`sqlite3.Row`
    :returns: string with all row data
    """
    sng = ''
    for row in rows:
        for v in row:
            sng += '{:} '.format(v)
        sng += '\n'
    return sng
