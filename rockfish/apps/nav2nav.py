#!/usr/bin/env python
"""
Convert between seismic navigation formats.
"""
import os
import argparse
import rockfish


class ShotRecord(object):
    """
    Class for standardizing shot time and navigation records.
    """
    def __init__(self, datetime, shotno, source_latitude, source_longitude,
                 water_depth_at_source, line_name=None, ship_latitude=None,
                 ship_longitude=None):
        self.datetime = datetime
        self.shotno = shotno
        self.source_latitude = source_latitude
        self.source_longitude = source_longitude
        self.line_name = line_name
        self.ship_latitude = ship_latitude
        self.ship_longitude = ship_longitude

class ShotRecordFormatters(object):

    def parse_ts(line):
        """
        Parse a line from a LDEO/Ewing ts or ts-like format file.
        """
        d = line.split()
        return {'datetime':self.ts2datetime(d[0]),
                'shot_number':int(d[1]),
                'source_lat':self._dm2dd(int(d[3]), float(d[4]),
                                         direction=d[2]),
                'source_lon':self._dm2dd(int(d[6]), float(d[7]),
                                         direction=d[5]),
                'depth_at_source':float(d[8]),
                'line_name':d[9]}

    def ts2datetime(tstime):
        """
        Convert a Ewing shot-navigation time string to a datetime object.
        >>> print ewing2mgl_date('2008+099:15:21:08.1443')
        2008-04-08 15:21:08.144300
        """
        d = tstime.split(":")
        y, j = [int(v) for v in d[0].split('+')]
        h = int(d[1])
        m = int(d[2])
        s = float(d[3])
        return datetime.datetime(y,1,1) \
              + datetime.timedelta(j - 1, h*60.*60. + m*60. + s)

    def dm2dd(degrees, minutes, direction=None):
        """
        Convert degrees, decimal minutes (dm) to decimal degrees (dd).
        If direction is given, applies correct sign to the output.
        """
        dd = degrees + minutes/60.
        if direction is not None:
            if direction is 'S' or direction is 'W':
                dd = -dd
        return dd

    def format_sioseis(self, line):
        """
        SIOSEIS navfil format:
        2002 283 23 59 34.288 26 49.6255 -110 38.3602 036130
        """
        return '%4i %3i %2i %2i %f %2i %f %3i %f %i'\
                %(line['datetime'].year,line['datetime'].timetuple().tm_yday,
                  line['datetime'].year




class NavigationFormatters(object):
    """
    Conveince class for the navigation file formaters.
    """


def get_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description='description: convert between seismic navigation formats',
        prog=os.path.basename(__file__))
    parser.add_argument(dest='input',metavar='INPUT',type=str, 
                        help='input file')
    parser.add_argument(dest='output',metavar='OUTPUT',type=str, 
                        help='output file')
    parser.add_argument('-i', '--input_format', dest='informat',
                        metavar='INPUT_FORMAT',type=str, 
                        help='input format', choices=['ts'])
    parser.add_argument('-o', '--output_format', dest='outformat',
                        metavar='OUTPUT_FORMAT',type=str, 
                        help='output format', choices=['sioseis'])
    parser.add_argument('--version', action='version', version='%(prog)s ' +
                        str(rockfish.__version__))
    return parser.parse_args()


def main():
    args = get_args()


if __name__ == '__main__':
    main()
