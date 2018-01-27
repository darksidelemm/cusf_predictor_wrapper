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


def gfs_model_age(gfs_path="./gfs"):
    """ Reads the model URL in from the dataset.txt file written by get_wind_data.py """

    dataset_file = os.path.join(gfs_path,"dataset.txt")

    try:
        _f = open(dataset_file,'r')
        dataset_url = _f.read()
        _f.close()

        dataset_date = dataset_url.split('/')[5]
        dataset_hour = dataset_url.split('/')[6].split('_')[3]

        return "%s-%s" % (dataset_date, dataset_hour)
    except:
        return "Unknown"




# Geometry and KML related stuff
ns = '{http://www.opengis.net/kml/2.2}'

def flight_path_to_linestring(flight_path):
    ''' Convert a predicted flight path to a LineString geometry object '''

    track_points = []
    for _point in flight_path:
        # Flight path array is in lat,lon,alt order, needs to be in lon,lat,alt
        track_points.append([_point[2],_point[1],_point[3]])

    return LineString(track_points)


def flight_path_to_geometry(flight_path,
    name="Flight Path",
    comment="Predicted Flight Path Data",
    track_color="ffff8000",
    poly_color="20000000",
    track_width=3.0,
    altitude_mode = 'absolute'):
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
        geometry=flight_path_to_linestring(flight_path),
        altitude_mode=altitude_mode,
        extrude=True,
        tessellate=True)

    return flight_line


def flight_path_landing_placemark(flight_path,
    name="Flight Path",
    comment="Landing"):
    """ Produce a placemark of the landing position of a flight """

    flight_icon_style = fastkml.styles.IconStyle(
        ns=ns, 
        icon_href="http://maps.google.com/mapfiles/kml/shapes/cross-hairs.png", 
        scale=2.0)

    flight_style = fastkml.styles.Style(
        ns=ns,
        styles=[flight_icon_style])

    flight_placemark = fastkml.kml.Placemark(
        ns=ns, 
        id=name,
        name=comment,
        description="",
        styles=[flight_style])

    flight_placemark.geometry = fastkml.geometry.Geometry(
        ns=ns,
        geometry=Point(flight_path[-1][2], flight_path[-1][1], flight_path[-1][3]),
        altitude_mode='clampToGround')

    return flight_placemark


def flight_path_burst_placemark(flight_path,
    name="Flight Path",
    comment="Burst",
    altitude_mode = 'absolute'):
    """ Produce a placemark of the burst position of a flight """

    flight_icon_style = fastkml.styles.IconStyle(
        ns=ns, 
        icon_href="http://maps.google.com/mapfiles/kml/shapes/star.png", 
        scale=2.0)

    flight_style = fastkml.styles.Style(
        ns=ns,
        styles=[flight_icon_style])

    flight_placemark = fastkml.kml.Placemark(
        ns=ns, 
        id=name,
        name=comment,
        description="",
        styles=[flight_style])

    # Read through array and hunt for max altitude point.
    current_alt = 0.0
    current_index = 0
    for i in range(len(flight_path)):
        if flight_path[i][3] > current_alt:
            current_alt = flight_path[i][3]
            current_index = i


    flight_placemark.geometry = fastkml.geometry.Geometry(
        ns=ns,
        geometry=Point(flight_path[current_index][2], flight_path[current_index][1], flight_path[current_index][3]),
        altitude_mode=altitude_mode)

    return flight_placemark


def write_flight_path_kml(flight_data,
                        filename="prediction.kml",
                        comment="HAB Prediction"):
    """ Write out flight path geometry objects to a kml file. """

    kml_root = fastkml.kml.KML()
    kml_doc = fastkml.kml.Document(
        ns=ns,
        name=comment)

    if type(flight_data) is not list:
        flight_data = [flight_data]

    for _flight in flight_data:
        kml_doc.append(_flight)

    with open(filename,'w') as kml_file:
        kml_file.write(kml_doc.to_string())
        kml_file.close()
