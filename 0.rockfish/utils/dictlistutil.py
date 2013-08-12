"""
Utilities for manipulating dictionaries and lists.
"""

def get_dict_default(key, dictionary, default):
    """
    Returns a value for a ``dict`` entry, or a default value. 
    """
    try:
        return dictionary[key] 
    except:
        return default


def dict_cat(a, b):
    """ Concatenate dictionaries `a` and `b`, giving preference to the values
    in dictionary `a`.

    >>> a = {'entry1':'value1','entry2':'value2'}
    >>> b = {'entry3':'value3'}
    >>> print dict_cat(a,b)
    {'entry2': 'value2', 'entry3': 'value3', 'entry1': 'value1'}
    >>> b={'entry1':'value3'}
    >>> print dict_cat(a,b)
    {'entry2': 'value2', 'entry1': 'value1'}
    """
    return dict(b, **a)


def dict_diff(dict1, dict2):
    """
    Return a dictionary with entries in dict1 that are not in dict2
    That is, `dict2 - dict1`

    >>> dict1 = { 'field1':1111, 'field2':2222, 'field3':3333 }
    >>> dict2 = { 'field1':9999 }
    >>> print dict_diff(dict1,dict2)
    {'field2': 2222, 'field3': 3333}
    """
    entries = list_diff(list(dict1), list(dict2))
    new_dict = {}
    for items in entries:
        new_dict[items] = dict1[items]
    return new_dict


def list_diff(list1, list2):
    """
    Return a list of items in `list1` that are not in `list2`.  That is,
    `list2 - list1`.

    >>> list1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    >>> list2 = [1, 2, 3, 4, 4, 6, 7, 8, 11, 77]
    >>> print list_diff(list1,list2)
    [5, 9, 10]
    """
    return [item for item in list1 if not item in list2]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
