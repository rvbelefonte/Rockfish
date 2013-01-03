'''
Miscellaneous utilities for Rockfish.
'''


def get_svn_revision(path=None):
    """
    Returns the SVN revision in the form SVN-XXXX,
    where XXXX is the revision number.

    Returns SVN-unknown if anything goes wrong, such as an unexpected
    format of internal SVN files.

    If path is provided, it should be a directory whose SVN info you want to
    inspect. If it's not provided, this will use the root rockfish/ package
    directory.

    :Based on: `Django <https://www.djangoproject.com/>`_'s django/util/version.py

    """

    import rockfish
    import re

    rev = None
    if path is None:
        path = rockfish.__path__[0]
    entries_path = '%s/.svn/entries' % path

    try:
        entries = open(entries_path, 'r').read()
    except IOError:
        pass
    else:
        # Versions >= 7 of the entries file are flat text.  The first line is
        # the version number. The next set of digits after 'dir' is the revision.
        if re.match('(\d+)', entries):
            rev_match = re.search('\d+\s+dir\s+(\d+)', entries)
            if rev_match:
                rev = rev_match.groups()[0]
        # Older XML versions of the file specify revision as an attribute of
        # the first entries node.
        else:
            from xml.dom import minidom
            dom = minidom.parse(entries_path)
            rev = dom.getElementsByTagName('entry')[0].getAttribute('revision')

    if rev:
        return u'SVN-%s' % rev
    return u'SVN-unknown'

def get_version(version=None):
    """
    Derives a PEP386-compliant version number from VERSION.
    
    :Based on: `Django <https://www.djangoproject.com/>`_'s
        django/__init__.get_version

    """
    if version is None:
        version = VERSION
    assert len(version) == 5
    assert version[3] in ('alpha', 'beta', 'rc', 'final')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] == 'alpha' and version[4] == 0:
        svn_revision = get_svn_revision()[4:]
        if svn_revision != 'unknown':
            sub = '.dev%s' % svn_revision

    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return main + sub

def get_logger(log_level='INFO',log_file=None):
    """
    Import logging module, set log level, destination, and format.

    """

    import logging

    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)

    if ( numeric_level == getattr(logging, 'DEBUG')):

        #FORMAT = '%(filename)s(%(asctime)s): %(funcName)s(%(lineno)d): %(levelname)s: %(message)s'
        FORMAT = '%(pathname)s:%(lineno)d: %(levelname)s: %(message)s'

    else:

        FORMAT = '%(filename)s: %(message)s'

    logging.basicConfig(format=FORMAT,level=numeric_level,filename=log_file)

    return logging


def load_example_segy(filename,unpack_headers=False, headonly=False):
    """
    Convienence function to load an example SEG-Y data file for use in tests and examples.

    Uses the ``rockfish.segy`` version of ``segy.py``.

    :param filename: (``str``) Name of the example file to load.
    :param unpack_headers: (``bool``) Determines whether or not all headers will be
        unpacked during reading the file. Has a huge impact on the memory usage
        and the performance. They can be unpacked on-the-fly after being read.
        Defaults to False.
    :param headonly: (``bool``) Determines whether or not the actual data records
        will be unpacked. Useful if one is just interested in the headers.
        Defaults to False.

    .. rubric:: Example:

    >>> from rockfish import tests
    >>> sgy = load_example_segy('obs.segy')
    >>> print sgy

    """


    from rockfish.segy.segy import readSEGY

    filepath = getExampleFile(filename) 

    return readSEGY(filepath,unpack_headers=unpack_headers)


def get_example_file(filename):
    """
    Function to find the absolute path of a test data file

    The Rockfish modules are installed to a custom installation directory.
    That is the path cannot be predicted. This functions searches for all
    installed Rockfish modules and checks weather the file is in any of
    the "tests/data" subdirectories.

    Based on ``getExampleFile()`` in ``obspy.core.util``.

    :param filename: A test file name to which the path should be returned.
    :return: Full path to file.

    .. rubric:: Example

    >>> getExampleFile('slist.ascii')  # doctest: +SKIP
    /custom/path/to/rockfish/tests/data/obs.segy

    >>> getExampleFile('does.not.exists')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    IOError: Could not find file does.not.exists ...
    """
   
    import os

    mod = __import__("rockfish.tests")
    file = os.path.join(mod.__path__[0], "tests/data", filename)

    if os.path.isfile(file):
        return file
    msg = "Could not find file %s in tests/data directory " % filename + \
          "of Rockfish modules (%s)." % mod.__path__[0]
    raise IOError(msg)



