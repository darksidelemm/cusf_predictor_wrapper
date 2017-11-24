# CUSF Standalone Predictor - Python Wrapper
This is a semi-fork of the [CUSF Standalone Predictor](https://github.com/jonsowman/cusf-standalone-predictor/), which provides a Python wrapper around the predictor binary, and provides a means of gathering the requisite wind data.


## 1. Building the Predictor
The predictor binary ('pred') is built using CMake, in the usual manner:

```
$ cd src
$ mkdir build
$ cd build
$ cmake ../
$ make
```

The `pred` binary then needs to be copied somewhere useful, ideally the same directory as `Predictor.py`, i.e.
```
cp pred ../../
```

## 2. Dependencies
Due to requiring a specific version of [PyDAP](https://github.com/pydap/pydap) to download wind model data, this software requires *Python 2.7*. This is a result of an API change between 3.1.1 and 3.2 (the first Python3 supported version). Pull requests to help upgrade to the newer API would be appreciated!

You can grab the required version using:
```
$ pip install pydap==3.1.1
```

## 2. Getting Wind Data
The predictor binary uses a custom wind data format, extracted from NOAA's Global Forecast System wind models. The `get_wind_data.py` Python script pulls down and formats the relevant data from NOAA's [NOMADS](http://nomads.ncep.noaa.gov) server.

An example of running `get_wind_data.py` is as follows:
```
$ python get_wind_data.py --lat=-33 --lon=139 --latdelta=10 --londelta=10 -v -f 24 -r 0p50 -o gfs
```
The command line arguments are as follows:
```
Area of interest:
     --lat       Latitude (Decimal Degrees) of the centre of the area to gather.
     --lon         Longitude (Decimal Degrees) of the centre of the area to gather.
     --latdelta    Gather data from lat+/-latdelta
     --londelta    Gather data from lon+/-londelta

   Time of interest:
     -p X    Gather data up to X hours into the past. 
     -f X   Gather data up to X hours into the future. Make sure you get enough for the flight!   
   
   GFS Model Choice:
     -r <model>    Choose between either:
           1p00  - 1 Degree Spatial, 6-hour Time Resolution
           0p50  - 0.5 Degree Spatial, 3-hour Time Resolution (default)
           0p25 - 0.25 Degree Spatial, 1-hour Time Resolution

   Other settings:
     -v  Verbose output
     -o output_dir     (Where to save the gfs data to, defaults to ./gfs/)
```

The higher resolution wind model you choose, the larger the amount of data to download, and the longer it will take. It also increases the prediction calculation time (though not significantly).

`wind_grabber.sh` is an example script to automatically grab wind data first to a temporary directory, and then to the final gfs directory. This could be run from a cronjob to keep the wind data up-to-date.
New wind models become available approximately every 6 hours, approximately 4 hours after the model's nominal time (i.e. the 00Z model becomes availble aroudn 04Z). Information on the status of the GFS model generation is available here: http://www.nco.ncep.noaa.gov/pmb/nwprod/prodstat_new/

## 3. Using the Predictor

Notes to be fleshed out:
* Input time is a datetime object, and must be in UTC.
* Output is a list of lists, [utctimestamp,lat,long,alt]

TBD :-)


