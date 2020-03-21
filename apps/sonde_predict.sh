#!/bin/bash
#
#   Example script for grabbing the following week's wind data,
#   and then running predictions of radiosonde launches from a site.
#
#   Mark Jessop <vk5qi@rfhead.net>
#
#   For this script to work, you need
#     - cusf_predictor_wrapper installed and available on the current python path.
#     - get_wind_data.py in this directory (should already be the case)
#     - The 'pred' binary available in this directory.
#
#   New GFS models are available every 6 hours, approximately 3-4 hours after the model
#   start time (00/06/12/18Z).
#
#   I use the following crontab entry to run this script at a time where the model is either available,
#   or close to being available.
#
#   40 3,9,15,21 * * * /home/username/cusf_predictor_wrapper/apps/sonde_predict.sh

# Home location latitude & longitude
HOME_LAT=-34.0
HOME_LON=138.0

# Area to grab data for. +/- 10 degrees is usually plenty!
LATLON_DELTA=10

# How many hours to grab data for. 192 hours = 8 days, which is about the extent of the GFS model
HOUR_RANGE=192


# We assume this script is run from the cusf_predictor_wrapper/apps directory.
# If this is not the case (e.g. if it is run via a cronjob), then you may need
# to modify and uncomment the following line.
#cd /home/username/cusf_predictor_wrapper/apps/

# Clear old GFS data.
rm gfs/*.txt
rm gfs/*.dat

# Download the wind data.
# Note that this will wait up to 3 hours for the latest wind data to become available.
python get_wind_data.py --lat=$HOME_LAT --lon=$HOME_LON --latdelta=$LATLON_DELTA --londelta=$LATLON_DELTA -f $HOUR_RANGE -m 0p25_1hr --wait=180 2>&1 | tee sonde_predict.log 

# Run predictions
python sonde_predict.py

# Copy the resultant json file into the web interface directory.
# If the web interface is being hosted elsewhere, you may need to replace this with a SCP
# command to get the json file into the right place, e.g.
# scp sonde_predictions.json mywebserver.com:~/www/sondes/
cp sonde_predictions.json web/
