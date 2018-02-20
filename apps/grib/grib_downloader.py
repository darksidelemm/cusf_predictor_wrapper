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
import os.path
import traceback
import requests
import argparse
import logging
import datetime
import numpy as np
from osgeo import gdal

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
		f = open(filename, 'wb')
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



def parse_grib_to_dict(gribfile):
	''' Parse a GRIB file into a python dictionary format '''

	_grib = gdal.Open(gribfile)

	output = {}

	try:
		# Extract coordinate extents from the GRIB
		_grib_geotransform = _grib.GetGeoTransform()
		_grib_Xres = _grib_geotransform[1]
		_grib_Xsize = _grib.RasterXSize
		_grib_Yres = _grib_geotransform[5]
		_grib_Ysize = _grib.RasterYSize
		_grib_topLeftX = _grib_geotransform[0]+_grib_Xres/2.0
		_grib_topLeftY = _grib_geotransform[3]+_grib_Yres/2.0
		_grib_topRightX = _grib_topLeftX + _grib_Xsize*_grib_Xres
		_grib_bottomLeftY = _grib_topLeftY + _grib_Ysize*_grib_Yres
		# Generate arrays containing the lat/lon scales
		_grib_Xscale = np.arange(_grib_topLeftX, _grib_topRightX, _grib_Xres)
		_grib_Yscale = np.arange(_grib_topLeftY, _grib_bottomLeftY, _grib_Yres)

		# Copy the variables we will need later to the output dictionary
		output['lon_scale'] = _grib_Xscale
		output['lat_scale'] = _grib_Yscale
		output['lon_centre'] = _grib_Xscale[_grib_Xsize//2]
		output['lat_centre'] = _grib_Yscale[_grib_Ysize//2]
		output['lon_radius'] = (max(_grib_Xscale) - min(_grib_Xscale))/2.0
		output['lat_radius'] = (max(_grib_Yscale) - min(_grib_Yscale))/2.0

	except:
		traceback.print_exc()
		return None

	# Iterate over all the rasters (GRIB messages) within the file, and 
	# if they contain data we need, copy the data into the output dictionary.
	for _n in range(1,_grib.RasterCount+1):
		try:
			_band = _grib.GetRasterBand(_n)
			_metadata = _band.GetMetadata()

			_level = _metadata['GRIB_SHORT_NAME']
			_level_int = int(_level.split('-')[0])//100


			if _level_int not in output.keys():
				output[_level_int] = {}

			_variable = _metadata['GRIB_ELEMENT']
			#print(_variable)
			#print(GFS_PARAMS)

			if _variable in GFS_PARAMS:
				output[_level_int][_variable] = _band.ReadAsArray()
				#print("Level: %d, Variable: %s" % (_level_int, _variable))

				_valid_time = int(_metadata['GRIB_VALID_TIME'].split('sec')[0].strip())
				output['valid_time'] = _valid_time

		except:
			traceback.print_exc()
			continue

	return output



def wind_dict_to_cusf(data, output_dir='./gfs/'):
	''' 
	Export wind data to a cusf-standalone-predictor compatible file
	Note that the file-naming scheme is fixed, so only the output directory is user-selectable.
	'''


	# Generate Output Filename: i.e. gfs_1506052799_-33.0_139.0_10.0_10.0.dat
	_output_filename = "gfs_%d_%.1f_%.1f_%.1f_%.1f.dat" % (
						data['valid_time'],
						data['lat_centre'],
						data['lon_centre'],
						data['lat_radius'],
						data['lon_radius']
						)
	_output_filename = os.path.join(output_dir, _output_filename)

	output_text = ""

	# Get the list of pressures. This is essentially all the integer keys in the data dictionary.
	_pressures = []
	for _key in data.keys():
		if type(_key) == int:
			_pressures.append(_key)

	# Sort the list of pressures from highest to lowest
	_pressures = np.flip(np.sort(_pressures),0)


	# Build up the output file, section by section.

	# HEADER Block
	# Window coverage area, and timestamp
	output_text += "# window centre latitude, window latitude radius, window centre longitude, window longitude radius, POSIX timestamp\n"
	output_text += "%.1f,%.1f,%.1f,%.1f,%d\n" % (
					data['lat_centre'],
					data['lat_radius'],
					data['lon_centre'],
					data['lon_radius'],
					data['valid_time'])

	# Number of axes in dataset - always 3 - pressure, latitude, longitude
	output_text += "# Number of axes\n3\n"

	# First Axis definition - Pressure
	output_text += "# axis 1: pressures\n"
	# Size of Axis
	output_text += "%d\n" % len(_pressures)
	# Values
	output_text += ",".join(["%.1f" % num for num in _pressures.tolist()]) + "\n"

	# Second Axis Definition - Latitude
	output_text += "# axis 2: latitudes\n"
	# Size of Axis
	output_text += "%d\n" % len(data['lat_scale'])
	# Values
	output_text += ",".join(["%.1f" % num for num in data['lat_scale']]) + "\n"

	# Third Axis Definition - Longitude
	output_text += "# axis 3: longitudes\n"
	# Size of Axis
	output_text += "%d\n" % len(data['lon_scale'])
	# Values
	output_text += ",".join(["%.1f" % num for num in data['lon_scale']]) + "\n"

	# DATA BLOCK
	# Number of lines of data
	output_text += "# number of lines of data\n"
	output_text += "%d\n" % (len(data['lat_scale']) * len(data['lon_scale']) * len(_pressures))
	# Components of data (3)
	output_text += "# data line component count\n3\n"
	# Output Data header
	output_text += "# now the data in axis 3 major order\n# data is: geopotential height [gpm], u-component wind [m/s], v-component wind [m/s]\n"

	# Now we need to format our output values.

	_values = ""
	# TODO: Nice Numpy way of doing this.
	for pressureidx, pressure in enumerate(_pressures):
	    for latidx, latitude in enumerate(data['lat_scale']):
	       for lonidx, longitude in enumerate(data['lon_scale']):
	       		_hgt_val = data[pressure]['HGT'][lonidx,latidx]
	       		_ugrd_val = data[pressure]['UGRD'][lonidx,latidx]
	       		_vgrd_val = data[pressure]['VGRD'][lonidx,latidx]

	       		output_text += "%.5f,%.5f,%.5f\n" % (_hgt_val,_ugrd_val,_vgrd_val)

	# Write out to file!
	f = open(_output_filename,'w')
	f.write(output_text)
	f.close()

	return (_output_filename, output_text)



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--age', type=int, default=0, help="Age of the model to grab, in blocks of 6 hours.")
	parser.add_argument('-f', '--future', type=int, default=48, help="window of time to save data is at most HOURS hours in future.")
	parser.add_argument('--lat', type=float, default=-34.0, help="tile centre latitude in range (-90,90) degrees north")
	parser.add_argument('--lon', type=float, default=138.0, help="tile centre longitude in range (-180,180) degrees north")
	parser.add_argument('--latdelta', type=float, default=10.0, help='tile radius in latitude in degrees')
	parser.add_argument('--londelta', type=float, default=10.0, help='tile radius in longitude in degrees')
	parser.add_argument('--model', type=str, default='0p25_1hr', help="GFS Model to use.")
	parser.add_argument('--output_dir', type=str, default='./gfs/', help='GFS data output directory.')
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

		success = download_grib(url, params, filename='temp.grib')

		if success:
			logging.info("Downloaded data for T+%03d" % forecast_time)
		else:
			logging.error("Could not download data for T+%03d" % forecast_time)


		# TODO: Process GRIB file into cusf-predictor compatible output
		logging.info("Processing GRIB file...")
		_wind = parse_grib_to_dict('temp.grib')

		if _wind is not None:
			(_filename, _text) = wind_dict_to_cusf(_wind, output_dir=args.output_dir)
			logging.info("GFS data written to: %s" % _filename)
		else:
			print("Error processing GRIB file.")

