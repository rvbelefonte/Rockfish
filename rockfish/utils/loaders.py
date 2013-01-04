"""
Functions for loading example data
"""
import os


def get_test_data_dirs():
    """
    Finds the absolute paths to data directories.

    The Rockfish modules are installed to a custom installation directory.
    That is the path cannot be predicted. This functions searches through
    all Rockfish modules for "tests/data" subdirectories.

    :returns: `list` of "tests/data" directories
    """
    from rockfish import __path__ as ROOT
    matches = []
    for root, dirnames, filenames in os.walk(ROOT[0]):
        for _dirname in dirnames:
            if _dirname == 'data' and os.path.basename(root) == 'tests':
                matches.append(os.path.join(root, _dirname))
    return matches


def get_example_file(filename):
    """
    Function to find the absolute path of a test data file.

    The Rockfish modules are installed to a custom installation directory.
    That is the path cannot be predicted. This functions searches for all
    Rockfish modules and checks weather the file is in any of
    the "tests/data" subdirectories.

    :param filename: A test file name to which the path should be returned.
    :returns: Full path to file.

    >>> getExampleFile('example_file.dat')  # doctest: +SKIP
    /custom/path/to/rockfish/module/tests/data/example_file.dat
    """
    test_data_dirs = get_test_data_dirs()
    for dirname in test_data_dirs:
        filepath = os.path.join(dirname, filename)
        if os.path.isfile(filepath):
            return filepath
    msg = "Could not find file {:} in {:}".format(filename,
                                                  get_test_data_dirs())
    raise IOError(msg)
