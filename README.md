# CUSF Standalone Predictor - Python Wrapper
This is a semi-fork of the [CUSF Standalone Predictor](https://github.com/jonsowman/cusf-standalone-predictor/), which provides a Python wrapper around the predictor binary, and provides a means of gathering the requisite wind data.

## 1. Install the Python Wrapper
The usual Python package installation utilities work for this:
```
$ sudo python setup.py install
```

This should grab the necessary Python dependencies, but if not, they are:
 * python-dateutil
 * shapely
 * fastkml
 * pydap==3.1.1

Due to requiring a specific version of [PyDAP](https://github.com/pydap/pydap) to download wind model data, this software requires *Python 2.7*. This is a result of an API change between 3.1.1 and 3.2 (the first Python3 supported version). Pull requests to help upgrade to the newer API would be appreciated!

## 2. Building the Predictor
The predictor itself is a binary ('pred'), which we (currently) build seperately, using CMake:

```
$ cd src
$ mkdir build
$ cd build
$ cmake ../
$ make
```

The `pred` binary then needs to be copied into the 'apps' directory, or somewhere else useful, i.e.
```
$ cp pred ../../apps/
```

## 3. Getting Wind Data
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

New wind models become available approximately every 6 hours, approximately 4 hours after the model's nominal time (i.e. the 00Z model becomes available around 04Z). Information on the status of the GFS model generation is available here: http://www.nco.ncep.noaa.gov/pmb/nwprod/prodstat_new/

## 4. Using the Predictor

The basic usage of the predictor is as follows:
```
import datetime
from cusfpredict.predict import Predictor

pred = Predictor(bin_path='./pred', gfs_path='./gfs')

flight_path = pred.predict(
    launch_lat=-34.9499,
    launch_lon=138.5194,
    launch_alt=0.0,
    ascent_rate=5.0,
    descent_rate=5.0,
    burst_alt=30000,
    launch_time=datetime.datetime.utcnow()
    )

```

Note that the launch time is a datetime object interpreted as UTC, so make sure you convert your launch time as appropriate.

The output is a list-of-lists, containing entries of [utctimestamp, lat, lon, alt], i.e.:

```
>>> flight_path
[[1516702953, -34.9471, 138.517, 250.0], [1516703003, -34.9436, 138.514, 500.0], <etc>, [1516703053, -34.9415, 138.513, 750.0]]
```

The list-of-lists can be converted to a LineString geometry object using:
```
>>> from cusfpredict.utils import *
>>> linestring = flight_path_to_linestring(flight_path)
>>> linestring
<shapely.geometry.linestring.LineString object at 0x107106ad0>

```

A few example scripts are located in the 'apps' directory:
 * basic_usage.py - Example showing how to write a predicted flight path out to a KML file
 * sonde_predict.py - A more complex example, where predictions for the next week's of radiosonde flights are run and written to a KML file.



