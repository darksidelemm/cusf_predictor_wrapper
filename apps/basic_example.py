#!/usr/bin/env python
#
#   Project Horus 
#   CUSF Standalone Predictor Python Wrapper - Basic Predictor Usage Example
#   Copyright 2017 Mark Jessop <vk5qi@rfhead.net>
#
#	This is an example of running prediction, and outputting data to a KML file.
#

import datetime, sys
from cusfpredict.predict import Predictor
from cusfpredict.utils import *

# Predictor Binary and GFS data location
PRED_BINARY = "./pred"
GFS_PATH = "./gfs"

# Launch Parameters
LAUNCH_TIME = datetime.datetime.utcnow() # Note that this time is interpreted as a UTC time

LAUNCH_LAT = -34.9499
LAUNCH_LON = 138.5194
LAUNCH_ALT = 0.0

ASCENT_RATE = 5.0
DESCENT_RATE = 5.0
BURST_ALT = 30000.0

# Output file
OUTPUT_KML = "prediction.kml"

# Create the predictor object.
pred = Predictor(bin_path=PRED_BINARY, gfs_path=GFS_PATH)

# Run the prediction
flight_path = pred.predict(
	launch_lat=LAUNCH_LAT,
	launch_lon=LAUNCH_LON,
	launch_alt=LAUNCH_ALT,
	ascent_rate=ASCENT_RATE,
	descent_rate=DESCENT_RATE,
	burst_alt=BURST_ALT,
	launch_time=LAUNCH_TIME)

# Check the output makes sense
if len(flight_path) == 1:
	print("No Wind Data available for this prediction scenario!")
	sys.exit(1)

# Create a list of items to add into the KML output file
geom_items = []

# Add the flight path track, and the landing location to the list
geom_items.append(flight_path_to_geometry(flight_path, comment="Predicted Flight Path"))
geom_items.append(flight_path_landing_placemark(flight_path, comment="Predicted Landing Location"))

# Write everything in the list out to the KML file
write_flight_path_kml(geom_items, filename=OUTPUT_KML, comment="Balloon Flight Prediction")

# Print out some basic information about the prediction
# Launch time:
launch_position = flight_path[0]
print("Launch Time: %s" % datetime.datetime.utcfromtimestamp(launch_position[0]).isoformat())
print("Launch Location: %.4f, %.4f" % (launch_position[1],launch_position[2]))

# Landing position
landing_position = flight_path[-1]
print("Landing Time: %s" % datetime.datetime.utcfromtimestamp(landing_position[0]).isoformat())
print("Landing Location: %.4f, %.4f" % (landing_position[1],landing_position[2]))

