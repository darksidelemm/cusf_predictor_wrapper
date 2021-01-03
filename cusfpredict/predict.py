#!/usr/bin/env python
#
#   Project Horus 
#   CUSF Standalone Predictor Python Wrapper
#   Copyright 2017 Mark Jessop <vk5qi@rfhead.net>
#

import subprocess
import glob
import os
import time
import datetime
import logging

class Predictor:
    ''' CUSF Standalone Predictor Wrapper '''
    def __init__(self, bin_path = "./pred", gfs_path = "./gfs", verbose=False):
        # Sanity check that binary exists.
        if not os.path.isfile(bin_path):
            raise Exception("Predictor Binary does not exist.")

        if not self.test_pred_bin(bin_path):
            raise Exception("Not a valid CUSF predictor binary.")

        # Check that the gfs directory exists
        if not os.path.isdir(gfs_path):
            raise Exception("GFS data directory does not exist.")

        # Check the gfs directory contains some gfs data files.
        gfs_list = glob.glob(os.path.join(gfs_path, "gfs_*.dat"))
        if len(gfs_list) == 0:
            raise Exception("No GFS data files in directory.")

        self.bin_path = bin_path
        self.gfs_path = gfs_path
        self.verbose = verbose

    def test_pred_bin(self, bin_path):
        ''' Test that a binary is a CUSF predictor binary. '''
        try:
            pred_version = subprocess.check_output([bin_path, '--version']).decode('ascii')
            if 'Landing Prediction' in pred_version:
                return True
            else:
                return False
        except:
            return False

    def predict(self,launch_lat= -34.9499,
            launch_lon = 138.5194,
            launch_alt = 0,
            ascent_rate = 5.0,
            descent_rate = 8.0,
            burst_alt = 26000,
            launch_time = datetime.datetime.utcnow(),
            descent_mode = False):


        # Generate the 'scenario' input data (ini-like structure)
        scenario = "[launch-site]\n"
        scenario += "latitude = %.5f\n" % float(launch_lat)
        scenario += "longitude = %.5f\n" % float(launch_lon)
        scenario += "altitude = %d\n" % int(launch_alt)
        scenario += "[atmosphere]\nwind-error = 0\n"
        scenario += "[altitude-model]\n"
        scenario += "ascent-rate = %.1f\n" % float(ascent_rate)
        scenario += "descent-rate = %.1f\n" % float(descent_rate)
        scenario += "burst-altitude = %d\n" % (int(launch_alt) if descent_mode else int(burst_alt))
        scenario += "[launch-time]\n"
        scenario += "hour = %d\n" % (launch_time.hour)
        scenario += "minute = %d\n" % launch_time.minute
        scenario += "second = %d\n" % launch_time.second
        scenario += "day = %d\n" % launch_time.day
        scenario += "month = %d\n" % launch_time.month
        scenario += "year = %d\n" % launch_time.year

        # Attempt to run predictor

        # Force the local timezone env-var to UTC.
        env = dict(os.environ)
        env['TZ'] = 'UTC'
        subprocess_params = [self.bin_path, '-i', self.gfs_path]
        # If we are using 'descent mode', we just flag this to the predictor, so it ignores the ascent rate and burst altitude params.
        if descent_mode:
            subprocess_params.append('-d')

        if self.verbose:
            subprocess_params.append('-vv')
        # Run!
        pred = subprocess.Popen(subprocess_params, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
        (pred_stdout, pred_stderr) = pred.communicate(scenario.encode('ascii'))

        # Parse stdout data into an array of floats.
        logging.debug("Errors:")
        logging.debug(pred_stderr)

        # Parse output into an array.
        output = []
        for line in pred_stdout.decode('ascii').split('\n'):
            try:
                fields = line.split(',')
                timestamp = int(fields[0])
                lat = float(fields[1])
                lon = float(fields[2])
                alt = float(fields[3])
                output.append([timestamp,lat,lon,alt])
            except ValueError:
                continue

        return output


# Test Script. Run a prediction for Adelaide Airport and print the landing location.
if __name__ == "__main__":
    import argparse
    from dateutil.parser import parse
    from .utils import *
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
    parser.add_argument('--pred', type=str, default=PRED_BINARY, help="Location of the pred binary. (Default: ./pred)")
    parser.add_argument('--gfs', type=str, default=GFS_PATH, help="Location of the GFS data store. (Default: ./gfs/)")
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
    pred = Predictor(bin_path=args.pred, gfs_path=args.gfs)

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
            predictions.append(flight_path_burst_placemark(flight_path, comment="Burst (%dm)"%_burst_alt, altitude_mode=altitude_mode))
            predictions.append(flight_path_landing_placemark(flight_path, comment=pred_comment))

            print("%s - Landing: %.4f, %.4f at %s" % (pred_comment, flight_path[-1][1], flight_path[-1][2], datetime.datetime.utcfromtimestamp(flight_path[-1][0]).isoformat()))

    write_flight_path_kml(predictions, filename=args.output)
    print("KML written to %s" % args.output)
