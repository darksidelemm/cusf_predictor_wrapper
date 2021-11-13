#!/usr/bin/env python
#
#   Project Horus 
#   CUSF Standalone Predictor Python Wrapper
#   Radiosonde Launch Predictor
#   Copyright 2017 Mark Jessop <vk5qi@rfhead.net>
#
#   In this example we run predictions for a radiosonde launch from Meppen, West Germany
#   for their schedule (MON-FRI 05/07/09/11Z, and write the tracks out to a KML file.
#
#   For this script to work correctly, we need a weeks worth of GFS data available within the gfs directory.
#   This can be gathered using get_wind_data.py (or scripted with wind_grabber.sh), using :
#   python get_wind_data.py --lat=54 --lon=07 --latdelta=10 --londelta=10 -f 168 -m 0p25_1hr -o gfs
#   with lat/lon parameters chaged as appropriate.
#   Them Germans don't work weekends mod by MikeTango


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

# LAUNCH_COUNT = 1 # This thing counts how many launches there are per given day
# LAUNCH_STEPS = 2 # Steps between jumps per day
LAUNCH_TIMES = ["05:00Z", "07:00Z", "09:00Z", "11:00Z"]
LAUNCH_DAYS = 5 # Jumps 24hrs
LAUNCH_WEEKDAYS = [0,1,2,3,4] # This thing tells you on which weekdays to run the thing
LAUNCH_TIME_LIMIT = 168 # Predict out this many hours into the future
LAUNCH_TIME = "11:15Z"
LAUNCH_LAT = 52.715
LAUNCH_LON = 7.319
LAUNCH_ALT = 18.0
ASCENT_RATE = 5.0
DESCENT_RATE = 3.5
BURST_ALT = 25000.0
#ARRAY = []

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--ascentrate', type=float, default=ASCENT_RATE, help="Ascent Rate (m/s). Default %.1fm/s" % ASCENT_RATE)
parser.add_argument('-d', '--descentrate', type=float, default=DESCENT_RATE, help="Descent Rate (m/s). Default %.1dm/s" % DESCENT_RATE)
parser.add_argument('-b', '--burstalt', type=float, default=BURST_ALT, help="Burst Altitude (m). Default %.1fm" % BURST_ALT)
parser.add_argument('--launchalt', type=float, default=LAUNCH_ALT, help="Launch Altitude (m). Default 0m")
parser.add_argument('--latitude', type=float, default=LAUNCH_LAT, help="Launch Latitude (dd.dddd)")
parser.add_argument('--longitude', type=float, default=LAUNCH_LON, help="Launch Longitude (dd.dddd)")
parser.add_argument('--time', type=str, default=LAUNCH_TIME, help="First Time of the day (string, UTC). Default = %s" % LAUNCH_TIME)
# parser.add_argument('--steps', type=int, default=LAUNCH_STEPS, help="How many steps. Default = %s" % LAUNCH_STEPS)
# parser.add_argument('--step', type=int, default=LAUNCH_STEP, help="Time step between predictions (Hours). Default = %d" % LAUNCH_STEP)
parser.add_argument('--limit', type=int, default=LAUNCH_TIME_LIMIT, help="Predict up to this many hours into the future. Default = %d" % LAUNCH_TIME_LIMIT)
parser.add_argument('-s', '--site', type=str, default="Radiosonde", help="Launch site name. Default: Radiosonde")
parser.add_argument('-o', '--output', type=str, default='Meppen_predictions', help="Output JSON File. .json will be appended. Default = sonde_predictions[.json]")
args = parser.parse_args()

OUTPUT_FILE = args.output
LAUNCH_LAT = args.latitude
LAUNCH_LON = args.longitude
LAUNCH_ALT = args.launchalt
ASCENT_RATE = args.ascentrate
DESCENT_RATE = args.descentrate
BURST_ALT = args.burstalt

# Set the launch time to the current UTC day, but set the hours to the first sonde
current_day = datetime.datetime.utcnow()

launch_hour = parse(args.time)
LAUNCH_TIME = datetime.datetime(current_day.year, current_day.month, current_day.day, launch_hour.hour, launch_hour.minute)


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

for _delta_datum in range (0, LAUNCH_TIME_LIMIT, 24): # this limits the time to whatever model time we have before running anything, incrementing in 24hr steps
    
    _lunch_time = LAUNCH_TIME + datetime.timedelta(seconds=_delta_datum*3600) # this sets the steps to 24 hrs
 
     # print(_lunch_time)
    
    for _delta_werktag in range(0, len(LAUNCH_WEEKDAYS),1): #hello working day
        if _lunch_time.weekday() == LAUNCH_WEEKDAYS[_delta_werktag]: # if this step indeed has hit a working weekday, we shall
            for delta_launchtimes in range(0, len(LAUNCH_TIMES),1): # go through the array filled with launch times
                lunch_time_hour = parse (LAUNCH_TIMES[delta_launchtimes]) # parse the string in the array at the given increment
                _lunch_time = datetime.datetime(_lunch_time.year, _lunch_time.month, _lunch_time.day, lunch_time_hour.hour, lunch_time_hour.minute) #and append the model run at that time
                print(_lunch_time, _lunch_time.weekday()) # this just prints out which model time it is running and on which working day
               
               # Run the prediction
                flight_path = pred.predict(
                launch_lat=LAUNCH_LAT,
                launch_lon=LAUNCH_LON,
                launch_alt=LAUNCH_ALT,
                ascent_rate=ASCENT_RATE,
                descent_rate=DESCENT_RATE,
                burst_alt=BURST_ALT,
                launch_time=_lunch_time)

            # If we only get a single entry in the output array, it means we don't have any wind data for this time
            # Continue on to the next launch time.
            if len(flight_path) == 1:
                continue

            # Generate a descriptive comment for the track and placemark.
            pred_time_string = _lunch_time.strftime("%Y%m%d-%H%M")
            pred_comment = "%s %.1f/%.1f/%.1f" % (pred_time_string, ASCENT_RATE, BURST_ALT, DESCENT_RATE)

            # Add the track and placemark to our list of predictions
            predictions.append(flight_path_to_geometry(flight_path, comment=pred_comment))
            predictions.append(flight_path_landing_placemark(flight_path, comment=pred_comment))

            json_out['predictions'][pred_comment] = {
                'timestamp': _lunch_time.strftime("%Y-%m-%d %H:%M:%S"),
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