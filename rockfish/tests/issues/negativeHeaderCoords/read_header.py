import obspy.segy.core as core
import obspy.segy.segy as segy

filename = '/Users/ncm/Rockfish/rockfish/tests/data/pos_neg.segy'

hdrwords = ['source_coordinate_x', 'source_coordinate_y',
           'group_coordinate_x', 'group_coordinate_y']

print "With obspy.segy.segy.readSEGY:"
sgy = segy.readSEGY(filename,unpack_headers=True)
for k in hdrwords:
    print k,":",sgy.traces[0].header.__getattribute__(k)

print "\nWith obspy.segy.core.readSEGY:"
st = core.readSEGY(filename,unpack_trace_headers=True)
tr = st[0]
for k in hdrwords:
    print k,":",st[0].stats.segy.trace_header[k]


