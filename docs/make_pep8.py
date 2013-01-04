#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pep8 import input_file, input_dir, get_statistics, get_count, \
    process_options
import rockfish
import os
import sys
from StringIO import StringIO
from shutil import copyfile


ROOT = os.path.dirname(__file__)
PEP8_IMAGE = os.path.join(ROOT, 'source', 'pep8', 'pep8.png')
PEP8_FAIL_IMAGE = os.path.join(ROOT, 'source', '_static', 'pep8-failing.png')
PEP8_PASS_IMAGE = os.path.join(ROOT, 'source', '_static', 'pep8-passing.png')


path = rockfish.__path__[0]

try:
    os.makedirs(os.path.join('source', 'pep8'))
except:
    pass

# write index.rst
fh = open(os.path.join('source', 'pep8', 'index.rst'), 'wt')
fh.write("""
.. _pep8-index:

====
PEP8
====

.. image:: pep8.png

Like most Python projects, we try to adhere to :pep:`8` (Style Guide for Python
Code) and :pep:`257` (Docstring Conventions). Be sure to read those documents if you would like to contribute code to Rockfish.

Here are the results of the automatic PEP 8 syntax checker:

""")


# backup stdout
stdout = sys.stdout
sys.stdout = StringIO()

# clean up runner options
options, args = process_options()
options.repeat = True
input_dir(path, runner=input_file)
sys.stdout.seek(0)
data = sys.stdout.read()
statistic = get_statistics('')
count = get_count()

if count == 0:
    fh.write("The PEP 8 checker didn't find any issues.\n")
else:
    fh.write("\n")
    fh.write(".. rubric:: Statistics\n")
    fh.write("\n")
    fh.write("======= =====================================================\n")
    fh.write("Count   PEP 8 message string                                 \n")
    fh.write("======= =====================================================\n")
    for stat in statistic:
        fh.write(stat + "\n")
    fh.write("======= =====================================================\n")
    fh.write("\n")

    fh.write(".. rubric:: Warnings\n")
    fh.write("\n")
    fh.write("::\n")
    fh.write("\n")

    data = data.replace(path, '    rockfish')
    fh.write(data)
    fh.write("\n")

    fh.close()

# restore stdout
sys.stdout = stdout

# remove any old image
try:
    os.remove(PEP8_IMAGE)
except:
    pass
# copy correct pep8 image
if count > 0:
    copyfile(PEP8_FAIL_IMAGE, PEP8_IMAGE)
else:
    copyfile(PEP8_PASS_IMAGE, PEP8_IMAGE)

