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
    def __init__(self, bin_path = "./pred", gfs_path = "./gfs"):
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
    p = Predictor()
    flight_path = p.predict()

    # Launch time:
    launch_position = flight_path[0]
    print("Launch Time: %s" % datetime.datetime.utcfromtimestamp(launch_position[0]).isoformat())
    print("Launch Location: %.4f, %.4f" % (launch_position[1],launch_position[2]))

    # Landing position
    landing_position = flight_path[-1]
    print("Landing Time: %s" % datetime.datetime.utcfromtimestamp(landing_position[0]).isoformat())
    print("Landing Location: %.4f, %.4f" % (landing_position[1],landing_position[2]))




