#!/usr/bin/env python
#
#   Project Horus 
#   CUSF Standalone Predictor Python Wrapper - CUSF GFS File Reader
#   Copyright 2019 Mark Jessop <vk5qi@rfhead.net>
#
import datetime
import math
import pytz
import numpy as np



def read_cusf_gfs(filename):
    """ Read in a CUSF-format GFS data file """

    _output = {}

    with open(filename, 'r') as _f:
        # As this file has lots of comments, we just do the first few lines the hard way...

        # Check the first comment line exists.
        _line = _f.readline()
        if 'window centre latitude, window latitude radius' not in _line:
            raise ValueError('Not a CUSF GFS file.')
        
        # window centre latitude, window latitude radius, window centre longitude, window longitude radius, POSIX timestamp
        _line = _f.readline()
        _fields = _line.split(',')
        _output['window_centre_latitude'] = float(_fields[0])
        _output['window_latitude_radius'] = float(_fields[1])
        _output['window_centre_longitude'] = float(_fields[2])
        _output['window_longitude_radius'] = float(_fields[3])
        _output['posix_timestamp'] = int(_fields[4])
        # Parse timestamp into a datetime object.
        _output['timestamp'] = pytz.utc.localize(datetime.datetime.utcfromtimestamp(_output['posix_timestamp']))

        # Comment line
        _f.readline()
        # Number of axes
        _output['axes'] = int(_f.readline())

        # Comment line
        _f.readline()
        # Number of pressure levels
        _output['pressure_level_count'] = int(_f.readline())
        # Pressure levels
        _output['pressures'] = np.fromstring(_f.readline(), sep=',')


        # Comment line
        _f.readline()
        # Number of latitudes
        _output['latitude_count'] = int(_f.readline())
        # Latitudes
        _output['latitudes'] = np.fromstring(_f.readline(), sep=',')

        # Comment line
        _f.readline()
        # Number of longitudes
        _output['longitude_count'] = int(_f.readline())
        # Pressure levels
        _output['longitudes'] = np.fromstring(_f.readline(), sep=',')

        # Comment line
        _f.readline()
        # Number of lines of data
        _output['data_lines'] = int(_f.readline())

        # Comment line
        _f.readline()
        # Components per data line
        _output['components'] = int(_f.readline())

        # Two comment lines
        _f.readline()
        _f.readline()

        # Now read in the rest of the lines
        _output['raw_data'] = []
        for _line in _f:
            _fields = _line.split(',')
            if len(_fields) == 3:
                _hgt = float(_fields[0])
                _ugrd = float(_fields[1])
                _vgrd = float(_fields[2])
                _speed = math.sqrt(_ugrd*_ugrd + _vgrd*_vgrd)
                _dir = 57.29578*(math.atan2(_ugrd,_vgrd))+180.0
                _output['raw_data'].append([_hgt, _ugrd, _vgrd, _speed, _dir])

        # Re-shape into a 3D Array, with dimensions [pressure, latitude, longitude]
        _output['data'] = np.reshape(_output['raw_data'], (_output['pressure_level_count'], _output['latitude_count'], _output['longitude_count'], _output['components']+2), order='C')

    return _output


if __name__ == "__main__":
    import sys

    print(read_cusf_gfs(sys.argv[1]))
