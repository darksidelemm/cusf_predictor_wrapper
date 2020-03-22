#!/usr/bin/env python
#
#   Project Horus 
#   CUSF Standalone Predictor Python Wrapper
#	Radiosonde Launch Predictor
#   Copyright 2017 Mark Jessop <vk5qi@rfhead.net>
#
#	In this example we run predictions for a radiosonde launch from Adelaide Airport
#	for every launch for the next 7 days, and write the tracks out to a KML file.
#
#	For this script to work correctly, we need a weeks worth of GFS data available within the gfs directory.
#	This can be gathered using get_wind_data.py (or scripted with wind_grabber.sh), using :
#	    python get_wind_data.py --lat=-33 --lon=139 --latdelta=10 --londelta=10 -f 168 -m 0p25_1hr -o gfs
#	with lat/lon parameters chaged as appropriate.
#
import argparse
import fastkml
import datetime
import json
from dateutil.parser import parse
from cusfpredict.predict import Predictor
from pygeoif.geometry import Point, LineString
from cusfpredict.utils import *

# Predictor Parameters
PRED_BINARY = "./pred"
GFS_PATH = "./gfs/"

# Launch Parameters
LAUNCH_TIME = "11:15Z" # This can be anything that dateutil can parse. The time *must* be in UTC.
LAUNCH_STEP = 12 # Time step, in hours, between launch predictions.
LAUNCH_TIME_LIMIT = 168 # Predict out this many hours into the future
LAUNCH_LAT = -34.9499
LAUNCH_LON = 138.5194
LAUNCH_ALT = 0.0
ASCENT_RATE = 5.0
DESCENT_RATE = 6.0
BURST_ALT = 26000.0

# Read in command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument('-a', '--ascentrate', type=float, default=ASCENT_RATE, help="Ascent Rate (m/s). Default %.1fm/s" % ASCENT_RATE)
parser.add_argument('-d', '--descentrate', type=float, default=DESCENT_RATE, help="Descent Rate (m/s). Default %.1dm/s" % DESCENT_RATE)
parser.add_argument('-b', '--burstalt', type=float, default=BURST_ALT, help="Burst Altitude (m). Default %.1fm" % BURST_ALT)
parser.add_argument('--launchalt', type=float, default=LAUNCH_ALT, help="Launch Altitude (m). Default 0m")
parser.add_argument('--latitude', type=float, default=LAUNCH_LAT, help="Launch Latitude (dd.dddd)")
parser.add_argument('--longitude', type=float, default=LAUNCH_LON, help="Launch Longitude (dd.dddd)")
parser.add_argument('--time', type=str, default=LAUNCH_TIME, help="First Time of the day (string, UTC). Default = %s" % LAUNCH_TIME)
parser.add_argument('--step', type=int, default=LAUNCH_STEP, help="Time step between predictions (Hours). Default = %d" % LAUNCH_STEP)
parser.add_argument('--limit', type=int, default=LAUNCH_TIME_LIMIT, help="Predict up to this many hours into the future. Default = %d" % LAUNCH_TIME_LIMIT)
parser.add_argument('-s', '--site', type=str, default="Radiosonde", help="Launch site name. Default: Radiosonde")
parser.add_argument('-o', '--output', type=str, default='sonde_predictions', help="Output JSON File. .json will be appended. Default = sonde_predictions[.json]")
args = parser.parse_args()


OUTPUT_FILE = args.output
LAUNCH_LAT = args.latitude
LAUNCH_LON = args.longitude
LAUNCH_ALT = args.launchalt
ASCENT_RATE = args.ascentrate
DESCENT_RATE = args.descentrate
BURST_ALT = args.burstalt


# Set the launch time to the current UTC day, but set the hours to the 12Z sonde
current_day = datetime.datetime.utcnow()
launch_hour = parse(args.time)
LAUNCH_TIME = datetime.datetime(current_day.year, current_day.month, current_day.day, launch_hour.hour, launch_hour.minute)


# Parameter Variations
# These can all be left at zero, or you can add a range of delta values
launch_time_variations = range(0,args.limit,args.step)

# A list to store predicton results
predictions = []

# Separate store for JSON output data.
json_out = {
	'dataset': gfs_model_age(GFS_PATH),
	'predictions':{},
	'site': args.site,
	'launch_lat': LAUNCH_LAT,
	'launch_lon': LAUNCH_LON
}

# Create the predictor object.
pred = Predictor(bin_path=PRED_BINARY, gfs_path=GFS_PATH)


# Iterate through the range of launch times set above
for _delta_time in launch_time_variations:

	# Calculate the launch time for the current prediction.
	_launch_time = LAUNCH_TIME + datetime.timedelta(seconds=_delta_time*3600)

	# Run the prediction
	flight_path = pred.predict(
		launch_lat=LAUNCH_LAT,
		launch_lon=LAUNCH_LON,
		launch_alt=LAUNCH_ALT,
		ascent_rate=ASCENT_RATE,
		descent_rate=DESCENT_RATE,
		burst_alt=BURST_ALT,
		launch_time=_launch_time)

	# If we only get a single entry in the output array, it means we don't have any wind data for this time
	# Continue on to the next launch time.
	if len(flight_path) == 1:
		continue

	# Generate a descriptive comment for the track and placemark.
	pred_time_string = _launch_time.strftime("%Y%m%d-%H%M")
	pred_comment = "%s %.1f/%.1f/%.1f" % (pred_time_string, ASCENT_RATE, BURST_ALT, DESCENT_RATE)

	# Add the track and placemark to our list of predictions
	predictions.append(flight_path_to_geometry(flight_path, comment=pred_comment))
	predictions.append(flight_path_landing_placemark(flight_path, comment=pred_comment))

	json_out['predictions'][pred_comment] = {
		'timestamp': _launch_time.strftime("%Y-%m-%d %H:%M:%S"),
		'path':flight_path_to_polyline(flight_path),
		'burst_alt': BURST_ALT
	}

	print("Prediction Run: %s" % pred_comment)

# Write out the prediction data to the KML file
kml_comment = "Sonde Predictions - %s" % gfs_model_age()
write_flight_path_kml(predictions, filename=OUTPUT_FILE+".kml", comment=kml_comment)

# Write out the JSON blob.
with open(OUTPUT_FILE+".json",'w') as f:
	f.write(json.dumps(json_out))