#!/usr/bin/env python
#
#   Project Horus 
#   CUSF Standalone Predictor Python Wrapper - Utilities
#   Copyright 2017 Mark Jessop <vk5qi@rfhead.net>
#
import fastkml
import glob
import datetime
import os.path
from shapely.geometry import Point, LineString

def available_gfs(gfs_path='./gfs'):
    """ Determine the time extent of the GFS dataset """

    gfs_files = glob.glob(os.path.join(gfs_path,"gfs_*.dat"))

    if len(gfs_files) == 0:
        return (None, None)

    # Pull out the timestamps from each filename.
    _timestamps = []

    for _filename in gfs_files:
        try:
            _ts = int(_filename.split('_')[1])
            _timestamps.append(_ts)
        except:
            pass

    _timestamps.sort()

    start_time = datetime.datetime.utcfromtimestamp(_timestamps[0])
    end_time = datetime.datetime.utcfromtimestamp(_timestamps[-1])

    return (start_time, end_time)


# Geometry and KML related stuff
ns = '{http://www.opengis.net/kml/2.2}'

def flight_path_to_geometry(flight_path):
    ''' Convert a predicted flight path to a LineString geometry object '''

    track_points = []
    for _point in flight_path:
        # Flight path array is in lat,lon,alt order, needs to be in lon,lat,alt
        track_points.append([_point[2],_point[1],_point[3]])

    return LineString(track_points)


def flight_path_kml(flight_path,
    name="Flight Path",
    comment="Predicted Flight Path Data",
    track_color="ffff8000",
    poly_color="20000000",
    track_width=3.0):
    ''' Produce a fastkml geometry object from a flight path array '''

    flight_track_line_style = fastkml.styles.LineStyle(
        ns=ns,
        color=track_color,
        width=track_width)

    flight_extrusion_style = fastkml.styles.PolyStyle(
        ns=ns,
        color=poly_color)

    flight_track_style = fastkml.styles.Style(
        ns=ns,
        styles=[flight_track_line_style, flight_extrusion_style])

    flight_line = fastkml.kml.Placemark(
        ns=ns,
        id=name,
        name=comment,
        styles=[flight_track_style])

    flight_line.geometry = fastkml.geometry.Geometry(
        ns=ns,
        geometry=flight_path_to_geometry(flight_path),
        altitude_mode='absolute',
        extrude=True,
        tessellate=True)

    return flight_line