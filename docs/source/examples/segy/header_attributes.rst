.. _header_attributes:

Working with Header Attributes
==============================

The SEG-Y header structure is defined by `obspy.segy.segy.header.py <http://obspy.org/browser/obspy/trunk/obspy.segy/obspy/segy/header.py>`_.

Unpacking attributes
--------------------

SEG-Y files contain a large number of trace header fields which are
not unpacked by default. However these values can be accessed by calling the
header arrtibute directly or by using the ``unpack_headers`` keyword in
:meth:`rockfish.segy.segy.readSEGY`:

>>> from rockfish.segy.segy import readSEGY
>>> from rockfish.core.util import get_example_file
>>> filename = get_example_file('obs.segy')
>>> sgy = readSEGY(filename, unpack_headers=True)

Then, trace header attributes can by accessed with:

>>> print sgy.traces[0].header.energy_source_point_number
148000

Acessed attributes remain unpacked for future use.

Scaling of coordinates and elevations
-------------------------------------

Coordinates and elevations are stored in the SEG-Y format as signed integers.
For example:

>>> keys = ['source_coordinate_x','source_coordinate_y']
>>> for k in keys: print k,":",trs[0].header.__getattr__(k)
source_coordinate_x : -314346
source_coordinate_y : 36432

According to the SEG-Y format, coordinates and elevations are converted to real values
using these header attributes:

>>> keys = ['coordinate_units','scalar_to_be_applied_to_all_coordinates','scalar_to_be_applied_to_all_elevations_and_depths']
>>> for k in keys: print k,":",trs[0].header.__getattr__(k)
coordinate_units : 2
scalar_to_be_applied_to_all_coordinates : 1
scalar_to_be_applied_to_all_elevations_and_depths : 1

These scalers can be applied by using the ``scale_headers`` keyword in
:meth:`rockfish.segy.segy.readSEGY`:

>>> sgy2 =  readSEGY(filename, scale_headers = True)
>>> print sgy2.traces[0].header.source_coordinate_x
-87.3183333333

One can check if headers have been scaled with:

>>> print sgy2.IS_SCALED_HEADERS
True

Alternatively, coordinates and elevations can be scaled by calling 
:meth:`rockfish.segy.segy.SEGYFile.scale_headers`:

>>> print sgy.IS_SCALED_HEADERS
False
>>> sgy.scale_headers()
>>> print sgy.IS_SCALED_HEADERS
True
>>> print sgy.traces[0].header.source_coordinate_x
-87.3183333333

Similarily, coordinates and elevations can be converted back to signed integers
with ``scale_headers(False)``:

>>> sgy.scale_headers(False)
>>> print sgy.IS_SCALED_HEADERS
False
>>> print sgy.traces[0].header.source_coordinate_x
-314346


