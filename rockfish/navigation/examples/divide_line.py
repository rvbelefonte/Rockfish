"""
Divide a line into equally-spaced segments.
"""
from rockfish.navigation.geographic import divide_line
# load lon, lat data
f = open('test_line.gmt')
pts = []
for line in f:
    d = line.split()
    pts.append((float(d[0]), float(d[1])))
f.close()
pts.sort()
# divide the line
div_pts = divide_line(pts, spacing_m=6.25, start_distance_m=0., ellps='WGS84')

# write out points
f = open('test_divide.gmt', 'w')
for pt in div_pts:
    f.write('{:f} {:f} {:f} {:d}\n'.format(*pt))
f.close()
