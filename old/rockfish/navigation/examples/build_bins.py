"""
Build bins along a line of points
"""
from rockfish.navigation.geographic import build_bins 
# load lon, lat data
#f = open('test_line.gmt')
f = open('circle_line.gmt')
pts = []
for line in f:
    d = line.split()
    pts.append((float(d[0]), float(d[1])))
f.close()
#pts.sort()

# build bins along the line
bins = build_bins(pts, spacing_m=6.25, width_m=50, runin_m=0,
           ellps='WGS84')


# write out points
f = open('bins.gmt', 'w')
f1 = open('centers.gmt', 'w')
for _bin in bins:
    for pt in _bin[3]:
        f.write('{:f} {:f}\n'.format(*pt))
    f.write('{:f} {:f}\n'.format(*_bin[3][0]))
    f.write('>\n')
    f1.write('{:f} {:f} {:d} {:f}\n'\
             .format(_bin[2][0],_bin[2][1],_bin[0],_bin[1]))
f.close()
f1.close()
