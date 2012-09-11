"""
Testing if ObsPy can correctly read negative numbers from SEG Y headers:

First, read example data:

>>> from obspy.segy.core import readSEGY
>>> from obspy.core.util import getExampleFile
>>> import sys
>>> filename = getExampleFile("00001034.sgy_first_trace")
>>> st = readSEGY(filename,unpack_trace_headers=True)

and print some of the geometry fields:

>>> print_geom(st)
source_coordinate_x : 0
source_coordinate_y : 0
coordinate_units : 1
scalar_to_be_applied_to_all_coordinates : 0

Now, copy ``st`` to ``st2`` and change ``source_coordinate_x`` and ``source_coordinate_y`` to large positve
and negative numbers, respectively:

>>> st2 = st.copy()
>>> st2[0].stats.segy.trace_header['source_coordinate_x']=1.234567890e6
>>> st2[0].stats.segy.trace_header['source_coordinate_y']=-1.234567890e6
>>> print_geom(st2)
source_coordinate_x : 1234567.89
source_coordinate_y : -1234567.89
coordinate_units : 1
scalar_to_be_applied_to_all_coordinates : 0

Write ``st2`` to a file:
>>> ofile = 'st2.segy'
>>> st2.write(ofile, format="SEGY", data_encoding=1, byteorder=sys.byteorder)

And read ``st2.segy`` back in as ``st3``:

>>> #st3 = readSEGY(ofile,unpack_trace_headers=True)
>>> #print_geom(st3)


"""


from obspy.segy.core import readSEGY
from obspy.core.util import getExampleFile

def print_geom(st):
    hdrwords = ['source_coordinate_x',
                'source_coordinate_y',
                'coordinate_units',
                'scalar_to_be_applied_to_all_coordinates']

    for tr in st:
        for k in hdrwords:
            print k,":",tr.stats.segy.trace_header[k]
    return






    
if __name__ == "__main__":

    import doctest
    doctest.testmod()
