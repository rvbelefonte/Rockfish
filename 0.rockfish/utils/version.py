import subprocess


def get_git_revision():
    """
    Returns the revision number of the git repository.
    """

    modpath = __import__("rockfish").__path__[0]
    sh = 'cd {:}; git log --oneline | wc -l'.format(modpath)
    proc = subprocess.Popen(sh, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return int(out)


def get_version(version):
    """
    Derives a PEP386-compliant version number from a version tuple.

    :param version: Tuple of ``X, Y, Z, release_type, revision``. If ``Z`` is
        ``0``, this subversion number is omitted.  If ``release_type`` is
        ``alpha``, the given ``revision`` number is included (if ``revision``
        is not ``0``) or the revision number of git repository is used
        (if ``revision`` is ``0``).
    :returns: PEP386-compliant version number string

    >>> from rockfish.utils.version import get_version
    >>> VERSION = (0, 5, 0, 'alpha', 48)
    >>> get_version(VERSION)
    '0.5a48'
    >>> VERSION = (1, 2, 1, 'beta', 0)
    >>> get_version(VERSION)
    '1.2.1b0'
    >>> VERSION = (1, 2, 1, 'final', 0)
    >>> get_version(VERSION)
    '1.2.1'
    """
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
        # At the toplevel, this would cause an import loop.
        from rockfish.utils.version import get_git_revision
        revision = get_git_revision()
        sub = '.dev{:}'.format(revision)

    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return main + sub


if __name__ == "__main__":
    import doctest
    doctest.testmod()
