from obspy.segy.core import readSEGY
from obspy.core.util import getExampleFile
import sys

def print_geom(st):
    hdrwords = ['source_coordinate_x',
                'source_coordinate_y',
                'coordinate_units',
                'scalar_to_be_applied_to_all_coordinates']

    for tr in st:
        for k in hdrwords:
            print k,":",tr.stats.segy.trace_header[k]
    return


# Load the example file and print some geomtery fields:
filename = getExampleFile("00001034.sgy_first_trace")
st = readSEGY(filename,unpack_trace_headers=True)
print "As read:"
print st
print_geom(st)
print

# Now, make a copy and change x,y:
st2 = st.copy()
st2[0].stats.segy.trace_header['source_coordinate_x']=1.234567890e7
st2[0].stats.segy.trace_header['source_coordinate_y']=1.234567890e7

print "New copy with changes:"
print st2
print_geom(st2)
print


# Write the modified copy to the disk:
ofile1 = 'st2.segy'
st2.write(ofile1, format="SEGY", data_encoding=1, byteorder=sys.byteorder)

# Read this back in:
st3 = readSEGY(ofile1,unpack_trace_headers=True)
print st3
print_geom(st3)


