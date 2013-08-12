"""
General utilities for working with databases
"""


def format_row_factory(rows, none_value=None, step=1):
    """
    Dump list of :class:`sqlite3.Row` instances to a string.

    :param rows: list of :class:`sqlite3.Row`
    :param none_value: value to replace ``None`` values with
    :returns: string with all row data
    """
    sng = ''
    dat = rows.fetchall()
    for i in range(0, len(dat), step):
        for v in dat[i]:
            if v is None:
                v = none_value
            sng += '{:} '.format(v)
        sng += '\n'
    return sng


def py2str(values):
    """
    Convert python variables to strings for use in SQLite statements.

    :param values: List of values to convert.
    :returns: List of strings.
    """
    if type(values) in [str, unicode]:
        values = [values]
    strings = []
    for v in values:
        if type(v) in [str, unicode]:
            strings.append("'" + str(v) + "'")
        else:
            strings.append(str(v))
    return strings


def format_search(match_dict, list_op='OR', key_op='AND'):
    """
    Format a dictionary of search terms into a SQLite search string.

    Parameters
    ----------
    match_dict : dict
        Keywords and values to match.
    list_op : str, optional
        SQLite operator to use when combining multiple values for a single key.
    key_op : str, optional
        SQLite operator to use when combining multiple values.
    Returns
    -------
    sql : str
        SQLite query
    """
    fields = []
    _list_op = ' ' + list_op + ' '
    for k in match_dict:
        try:
            values = ['{:}={:}'.format(k, v) for v in py2str(match_dict[k])]
        except TypeError:
            values = ['{:}={:}'.format(k, py2str([match_dict[k]])[0])]
        fields.append('(' + _list_op.join(values) + ')')
    _key_op = ' ' + key_op + ' '
    sql = _key_op.join(fields)
    return sql
