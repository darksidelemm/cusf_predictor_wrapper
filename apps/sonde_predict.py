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

import fastkml
import datetime
import json
from dateutil.parser import parse
from cusfpredict.predict import Predictor
from pygeoif.geometry import Point, LineString
from cusfpredict.utils import *

# Predictor Parameters
PRED_BINARY = "./pred"
GFS_PATH = "./gfs"

OUTPUT_FILE = "sonde_predictions"

# Launch Parameters - Update as appropriate for your launch site
LAUNCH_LAT = -34.9499
LAUNCH_LON = 138.5194
LAUNCH_ALT = 0.0

# 5m/s is the typical target ascent rate for most radiosonde launches.
ASCENT_RATE = 5.0

# The descent rate can vary depending on how your site launches their sondes.
# Note that this is the descent rate just before landing.
# If a parachute is used, this could be as low as 3m/s.
# Manual BOM launch sites in Australia use old-stock radar reflectors as parachutes, resulting in a ~6m/s descent rate.
DESCENT_RATE = 6.0

# Typical burst altitudes are between 25-30km.
BURST_ALT = 26000.0

# Set the launch time to the current UTC day, but set the hours to the 12Z sonde
current_day = datetime.datetime.utcnow()
LAUNCH_TIME = datetime.datetime(current_day.year, current_day.month, current_day.day, 11, 15)


# Parameter Variations
# These can all be left at zero, or you can add a range of delta values
launch_time_variations = range(0,168,12) # Every 12 hours from the start time until 7 days time.

# A list to store predicton results
predictions = []

# Separate store for JSON output data.
json_out = {
	'dataset': gfs_model_age(GFS_PATH),
	'predictions':{}
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