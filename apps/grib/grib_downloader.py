#!/usr/bin/env python
#
#   Project Horus 
#   CUSF Standalone Predictor Python Wrapper - GRIB Downloader & Parser
#   Copyright 2018 Mark Jessop <vk5qi@rfhead.net>
#
#	Download GRIB files and convert them to predict-compatible GFS files.
#
import pygrib
import sys
import requests
import argparse
import logging
import datetime
import numpy as np

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# GFS Parameters we are interested in
GFS_LEVELS = [1000.0,975.0,950.0,925.0,900.0,850.0,800.0,750.0,700.0,650.0,600.0,550.0,500.0,450.0,400.0,350.0,300.0,250.0,200.0,150.0,100.0,70.0,50.0,30.0,20.0,10.0,7.0,5.0,3.0,2.0,1.0]
GFS_PARAMS = ['HGT', 'UGRD', 'VGRD']
VALID_MODELS = ['0p25_1hr']

# Other Globals
REQUEST_TIMEOUT = 30

# Functions to Generate the GRIB Filter 

# http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25_1hr.pl?
#file=gfs.t00z.pgrb2.0p25.f000
#&lev_850_mb=on&lev_900_mb=on&lev_925_mb=on
#&var_HGT=on&var_UGRD=on&var_VGRD=on&subregion=
#&leftlon=128&rightlon=148&toplat=-24&bottomlat=-44&dir=%2Fgfs.2018021900


def latest_model_name(age = 0):
	''' Get the N-th latest GFS model time '''

	# Get Current UTC time.
	_current_dt = datetime.datetime.utcnow()

	# Round to the last 6-hour interval
	_model_hour  = _current_dt.hour - _current_dt.hour%6
	_last_model_dt = datetime.datetime(_current_dt.year, _current_dt.month, _current_dt.day, _model_hour, 0, 0)

	# If we have been requested to get an older model, subtract <age>*6 hours from the current time
	_last_model_dt = _last_model_dt + datetime.timedelta(0,6*3600*age)

	return _last_model_dt


def generate_filter_request(model='0p25_1hr',
							forecast_time=0,
							model_dt=latest_model_name(0),
							lat=-34.0,
							lon=138.0,
							latdelta=10.0,
							londelta=10.0
							):
	''' Generate a URL and a dictionary of request parameters for use with the GRIB filter '''

	if model not in VALID_MODELS:
		raise ValueError("Invalid GFS Model!")

	# 

	# Get latest model time
	_model_dt = model_dt
	_model_timestring = _model_dt.strftime("%Y%m%d%H")
	_model_hour = _model_dt.strftime("%H")

	_filter_url = "http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_%s.pl" % model

	_filter_params = {}
	_filter_params['file'] = "gfs.t%sz.pgrb2.%s.f%03d" % (_model_hour, model.split('_')[0], forecast_time)
	_filter_params['dir'] = "/gfs.%s" % (_model_timestring)
	_filter_params['subregion'] = ''
	# TODO: Fix this to handle borders at -180 degrees properly.
	_filter_params['leftlon'] = int(lon - londelta)
	_filter_params['rightlon'] = int(lon + londelta)
	_filter_params['toplat'] = min(90, int(lat + latdelta))
	_filter_params['bottomlat'] = max(-90, int(lat - latdelta))

	# Add the parameters we want:
	for _param in GFS_PARAMS:
		_filter_params['var_%s'%_param] = 'on'

	# Add in the levels we want:
	for _level in GFS_LEVELS:
		_filter_params['lev_%d_mb' % int(_level)] = 'on'


	return (_filter_url, _filter_params)


def download_grib(url, params, filename="temp.grib"):
	''' Attempt to download a GRIB file to disk '''
	_r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

	if _r.status_code == requests.codes.ok:
		# Writeout to disk.
		f = open(filename, 'w')
		f.write(_r.content)
		f.close()
		return True
	else:
		return False


def determine_latest_available_dataset(model='0p25_1hr',
										forecast_time=0
										):
	''' Determine what the latest available dataset with <forecast_time> hours of model available is '''

	# Attempt to grab a small amount of data from the most recent model.
	# if that fails, go to the next most recent, and continue until either we have data, or have completely failed.
	for _model_age in range(0,-5,-1):
		_model_dt = latest_model_name(_model_age)
		_model_timestring = _model_dt.strftime("%Y%m%d%H")
		logging.info("Testing Model: %s" % _model_timestring)
		(_url, _params) = generate_filter_request(
												model=model,
												forecast_time=forecast_time,
												model_dt = _model_dt,
												lat=0.0,
												lon=0.0,
												latdelta=1.0,
												londelta=1.0)

		_r = requests.get(_url, params=_params, timeout=REQUEST_TIMEOUT)
		if _r.status_code == requests.codes.ok:
			logging.info("Found valid data in model %s!" % _model_timestring)
			return _model_dt
		else:
			continue

	logging.error("Could not find a model with the required data.")
	return None



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--age', type=int, default=0, help="Age of the model to grab, in blocks of 6 hours.")
	parser.add_argument('-f', '--future', type=int, default=48, help="window of time to save data is at most HOURS hours in future.")
	parser.add_argument('--lat', type=float, default=-34.0, help="tile centre latitude in range (-90,90) degrees north")
	parser.add_argument('--lon', type=float, default=138.0, help="tile centre longitude in range (-180,180) degrees north")
	parser.add_argument('--latdelta', type=float, default=10.0, help='tile radius in latitude in degrees')
	parser.add_argument('--londelta', type=float, default=10.0, help='tile radius in longitude in degrees')
	parser.add_argument('--model', type=str, default='0p25_1hr', help="GFS Model to use.")
	args = parser.parse_args()

	_model_dt = determine_latest_available_dataset(model=args.model, forecast_time=args.future)

	if _model_dt == None:
		sys.exit(1)

	logging.info("Starting download of wind data...")
	# Iterate through all forecast times, download and parse.
	for forecast_time in range(0,args.future+1, 1):
		(url, params) = generate_filter_request(
			model=args.model,
			forecast_time=forecast_time,
			model_dt=_model_dt,
			lat=args.lat,
			lon=args.lon,
			latdelta=args.latdelta,
			londelta=args.londelta
			)

		success = download_grib(url, params, filename='output.grib')

		if success:
			logging.info("Dowloaded data for T+%03d" % forecast_time)
		else:
			logging.error("Could not download data for T+%03d" % forecast_time)


		# TODO: Process GRIB file into cusf-predictor compatible output

