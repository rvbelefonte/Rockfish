import obspy.segy.core as core
import sys

filename = '/Users/ncm/Rockfish/rockfish/tests/data/pos_neg.segy'

hdrwords = ['source_coordinate_x', 'source_coordinate_y',
           'group_coordinate_x', 'group_coordinate_y']


print "\nWith obspy.segy.core.readSEGY:"
st = core.readSEGY(filename,unpack_trace_headers=True)
tr = st[0]
for k in hdrwords:
    print k,":",st[0].stats.segy.trace_header[k]


st2 = st.copy()
st2[0].stats.segy.trace_header['source_coordinate_x']=-1
st2.write('test_out.segy',format='SEGY',byteorder=sys.byteorder)
