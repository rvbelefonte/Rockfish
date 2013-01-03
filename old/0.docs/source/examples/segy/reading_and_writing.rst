.. _reading_and_writing:

Reading and Writing SEG-Y Files
===============================

Rockfish uses :class:`rockfish.segy.segy.SEGYFile` to handle reading,
internal storage, and writing of SEG-Y files. 

Reading 
-------

A SEG-Y file is loaded into a :class:`rockfish.segy.segy.SEGYFile` object with:

>>> from rockfish.segy.segy import readSEGY
>>> from rockfish.core.util import get_example_file
>>> filename = get_example_file('obs.segy')
>>> sgy = readSEGY(filename)
>>> print sgy
804 traces in the SEG Y structure.

Writing
-------

A :class:`rockfish.segy.segy.SEGYFile` object can be written to the disk as a SEG-Y file with:

>>> sgy.write('/path/to/file.segy') # doctest: +SKIP

Other methods
-------------

:class:`rockfish.segy.segy.SEGYFile` is an extended version of 
:class:`obspy.segy.segy.SEGYFile` and supports methods supplied by this parent.  See :class:`obspy.segy.segy.SEGYFile` for more information.
