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

def py2str(values):
    """
    Convert python variables to strings for use in SQLite statements.

    :param values: List of values to convert.
    :returns: List of strings.
    """
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

    :param match_dict: Dictionary of keys and values to match.
    :param list_op: Operator to use when combining multiple values for single
        key. Default is 'OR'.
    :param key_op: Operator to use when combining mulitple keys. Default is 
        'AND'.
    :returns: String of SQLite code.
    """
    fields = []
    _list_op = ' ' + list_op + ' '
    for k in match_dict:
        try:
            values = ['{:}={:}'.format(k,v) for v in py2str(match_dict[k])]
        except TypeError:
            values = ['{:}={:}'.format(k, py2str([match_dict[k]])[0])]
        fields.append('(' + _list_op.join(values) + ')')
    _key_op = ' ' + key_op + ' '
    sql = _key_op.join(fields)
    return sql
