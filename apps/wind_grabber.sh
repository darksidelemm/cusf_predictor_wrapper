#!/bin/bash
#
# Wind Grabber Script Example
#
# An example of how get_wind_data.py could be run as a cron-job, to keep a directory of wind data up to date.
#

# Make Temporary GFS data store if it doesn't already exist
mkdir gfs_temp

# Clear out directory
rm gfs_temp/*.dat

# Run get_wind_data.py
# Update arguments as required.
python get_wind_data.py --lat=-33 --lon=139 --latdelta=10 --londelta=10 -v -f 144 -r 0p25 -o gfs_temp

# Clear out data in gfs directory, and copy new data in.
rm gfs/*.dat
cp gfs_temp/*.dat gfs/

