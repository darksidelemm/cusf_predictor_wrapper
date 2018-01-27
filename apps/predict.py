#!/usr/bin/env python
#
#   Project Horus 
#   CUSF Standalone Predictor Python Wrapper - Example Predictor Usage
#   Copyright 2017 Mark Jessop <vk5qi@rfhead.net>
#
#	This is an example of running prediction, and outputting data to a KML file.
#

import fastkml
import datetime
import argparse
from dateutil.parser import parse
from cusfpredict.predict import Predictor
from pygeoif.geometry import Point, LineString
from cusfpredict.utils import *

# Predictor Parameters
PRED_BINARY = "./pred"
GFS_PATH = "./gfs"

# Launch Parameters
LAUNCH_TIME = datetime.datetime.utcnow().isoformat() # This can be anything that dateutil can parse. The time *must* be in UTC.
LAUNCH_LAT = -34.9499
LAUNCH_LON = 138.5194
LAUNCH_ALT = 0.0
ASCENT_RATE = 5.0
DESCENT_RATE = 5.0
BURST_ALT = 30000.0

# Read in command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument('-a', '--ascentrate', type=float, default=ASCENT_RATE, help="Ascent Rate (m/s). Default 5m/s")
parser.add_argument('-d', '--descentrate', type=float, default=DESCENT_RATE, help="Descent Rate (m/s). Default 5m/s")
parser.add_argument('-b', '--burstalt', type=float, default=BURST_ALT, help="Burst Altitude (m). Default 30000m")
parser.add_argument('--launchalt', type=float, default=LAUNCH_ALT, help="Launch Altitude (m). Default 0m")
parser.add_argument('--latitude', type=float, default=LAUNCH_LAT, help="Launch Latitude (dd.dddd)")
parser.add_argument('--longitude', type=float, default=LAUNCH_LON, help="Launch Longitude (dd.dddd)")
parser.add_argument('--time', type=str, default=LAUNCH_TIME, help="Launch Time (string, UTC). Default = Now")
parser.add_argument('-o', '--output', type=str, default='prediction.kml', help="Output KML File. Default = prediction.kml")
parser.add_argument('--altitude_deltas', type=str, default='0', help="Comma-delimited list of altitude deltas. (metres).")
parser.add_argument('--time_deltas', type=str, default='0', help="Comma-delimited list of time deltas. (hours)")
parser.add_argument('--absolute', action="store_true", default=False, help="Show absolute altitudes for tracks and placemarks.")
args = parser.parse_args()

LAUNCH_TIME = args.time
LAUNCH_LAT = args.latitude
LAUNCH_LON = args.longitude
LAUNCH_ALT = args.launchalt
ASCENT_RATE = args.ascentrate
DESCENT_RATE = args.descentrate
BURST_ALT = args.burstalt

altitude_mode = "absolute" if args.absolute else "clampToGround"
burst_alt_variations = [float(item) for item in args.altitude_deltas.split(',')]
launch_time_variations = [float(item) for item in args.time_deltas.split(',')]

predictions = []

print("Running using GFS Model: %s" % gfs_model_age(GFS_PATH))

# Create the predictor object.
pred = Predictor(bin_path=PRED_BINARY, gfs_path=GFS_PATH)

for _delta_alt in burst_alt_variations:
	for _delta_time in launch_time_variations:

		_burst_alt = BURST_ALT + _delta_alt
		_launch_time = parse(LAUNCH_TIME) + datetime.timedelta(seconds=_delta_time*3600)

		flight_path = pred.predict(
			launch_lat=LAUNCH_LAT,
			launch_lon=LAUNCH_LON,
			launch_alt=LAUNCH_ALT,
			ascent_rate=ASCENT_RATE,
			descent_rate=DESCENT_RATE,
			burst_alt=_burst_alt,
			launch_time=_launch_time)

		if len(flight_path) == 1:
			continue

		pred_comment = "%s %.1f/%.1f/%.1f" % (_launch_time.isoformat(), ASCENT_RATE, _burst_alt, DESCENT_RATE)

		predictions.append(flight_path_to_geometry(flight_path, comment=pred_comment, altitude_mode=altitude_mode))
		predictions.append(flight_path_burst_placemark(flight_path, comment="Burst", altitude_mode=altitude_mode))
		predictions.append(flight_path_landing_placemark(flight_path, comment=pred_comment))

		print("%s - Landing: %.4f, %.4f at %s" % (pred_comment, flight_path[-1][1], flight_path[-1][2], datetime.datetime.utcfromtimestamp(flight_path[-1][0]).isoformat()))

write_flight_path_kml(predictions, filename=args.output)
print("KML written to %s" % args.output)

