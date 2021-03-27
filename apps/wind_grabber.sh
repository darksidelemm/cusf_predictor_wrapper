#!/bin/bash
#
# Wind Grabber Script Example
#
# An example of how cusfpredict.gfs could be run as a cron-job, to keep a directory of wind data up to date.
#

# Run cusfpredict.gfs
# Update arguments as required.
python3 -m cusfpredict.gfs --lat=-33 --lon=139 --latdelta=10 --londelta=10 -f 24 -m 0p25_1hr -o gfs/
