"""
Utilities for working with configuration files
"""
import os

USER_CONF_DIR = os.path.join(os.path.expanduser('~'), '.rockfish')
DEFAULT_CONF_DIR = os.path.abspath(os.path.dirname(__file__))
_CONF_SEARCH_PATHS = [USER_CONF_DIR, DEFAULT_CONF_DIR]


def _get_conf_file(name):

    for path in _CONF_SEARCH_PATHS: 
        conf_file = os.path.join(path, name)
        if os.path.isfile(conf_file):
            return conf_file

    raise IOError('Could not find {:} in {:}'\
                  .format(name, _CONF_SEARCH_PATHS))
