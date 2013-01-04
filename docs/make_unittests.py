#!/usr/bin/env python
"""
Run all unit tests for Rockfish.

Results are printed to stdout and to unittest_results.html.
"""

import os
import nose
from shutil import copyfile
from htmloutput import HtmlOutput
import rockfish

ROOT = os.path.abspath(os.path.dirname(__file__))
UNITTEST_IMAGE = os.path.join(ROOT, 'source', 'unittest', 'unittest.png')
UNITTEST_FAIL_IMAGE = os.path.join(ROOT, 'source', '_static',
                                   'unittest-failing.png')
UNITTEST_PASS_IMAGE = os.path.join(ROOT, 'source', '_static',
                                   'unittest-passing.png')

try:
    os.makedirs(os.path.join('source', 'unittest'))
except:
    pass

try:
    os.makedirs(os.path.join('build', 'html', '_sources'))
except:
    pass


path = rockfish.__path__[0]

html_dir = os.path.abspath(os.curdir) + os.sep \
        + 'build' + os.sep + 'html' + os.sep + '_sources'
result_file = html_dir + os.sep + 'unittest_results.html'

passed = nose.run(argv=['', '--where={:}'.format(path), '--verbosity=3',
                        '--with-html-output', 
                        '--html-out-file={:}'.format(result_file),
                        '--with-doctest'],
                  addplugins=[HtmlOutput()])

if passed:
    copyfile(UNITTEST_PASS_IMAGE, UNITTEST_IMAGE)
else:
    copyfile(UNITTEST_FAIL_IMAGE, UNITTEST_IMAGE)

