#!/bin/bash
#
# Wind Grabber Script Example
#
# An example of how get_wind_data.py could be run as a cron-job, to keep a directory of wind data up to date.
#

# Run get_wind_data.py
# Update arguments as required.
python3 get_wind_data.py --lat=-33 --lon=139 --latdelta=10 --londelta=10 -f 24 -m 0p25_1hr -o gfs/
