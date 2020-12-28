# CUSF Standalone Predictor - Python Wrapper
This is a semi-fork of the [CUSF Standalone Predictor](https://github.com/jonsowman/cusf-standalone-predictor/), which provides a Python wrapper around the predictor binary, and provides a means of gathering the requisite wind data.

2018-02 Update: Wind downloader updated to use the [NOMADS GRIB Filter](http://nomads.ncep.noaa.gov/txt_descriptions/grib_filter_doc.shtml), as the OpenDAP interface stopped working. As such, we no longer require PyDAP, but we do now require GDAL to read in the GRIB2 files.

## 1. Install the Python Wrapper
Clone this repository with:
```
$ git clone https://github.com/darksidelemm/cusf_predictor_wrapper.git
```

The wind data downloader script depends on python-gdal, which needs gdal installed.
GDAL may need to be installed separately using the system package manager, for example:
```
Debian/Ubuntu: apt-get install python3-gdal
OSX (Macports): port install gdal +grib
Windows (Anaconda Python): conda install gdal
```
Note that on Windows you also need to install the [Visual C++ 2008 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=26368&ranMID=24542&ranEAID=TnL5HPStwNw&ranSiteID=TnL5HPStwNw-LlmdBk4XVrcPuOVDR8ONKA&tduid=(01174a65b485bdf3885d3de68395d4e3)(256380)(2459594)(TnL5HPStwNw-LlmdBk4XVrcPuOVDR8ONKA)()) for GDAL to import in Python correctly.

The custpredict python package can then be installed in the usual Python way:
```
$ cd cusf_predictor_wrapper
$ sudo python3 setup.py install
```

This should grab the other required Python dependencies, but if not, they are:
 * python-dateutil
 * shapely
 * fastkml
 * python-gdal (which may have been installed via apt-get previously)


## 2. Building the Predictor
The predictor itself is a binary ('pred'), which we (currently) build seperately, using CMake.
You may need to install `cmake` and `libglib2.0-dev` via your package manager before building, i.e.
```
$ sudo apt-get install cmake libglib2.0-dev
```

Then, from within the cusf_predictor_wrapper directory, run the following to build the predictor binary:

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
If you are building this utility for use with chasemapper, then you should copy `pred` into the chasemapper directory:
```
$ cp pred ~/chasemapper/
```

A pre-compiled Windows binary of the predictor is available here: http://rfhead.net/horus/cusf_standalone_predictor.zip
Use at your own risk!

## 3. Getting Wind Data
The predictor binary uses a custom wind data format, extracted from NOAA's Global Forecast System wind models. The `get_wind_data.py` Python script pulls down and formats the relevant data from NOAA's [NOMADS](http://nomads.ncep.noaa.gov) server.

An example of running `get_wind_data.py` is as follows:
```
$ python3 get_wind_data.py --lat=-33 --lon=139 --latdelta=10 --londelta=10 -f 24 -m 0p50 -o gfs
```
The command line arguments are as follows:
```
Area of interest:
     --lat       Latitude (Decimal Degrees) of the centre of the area to gather.
     --lon         Longitude (Decimal Degrees) of the centre of the area to gather.
     --latdelta    Gather data from lat+/-latdelta
     --londelta    Gather data from lon+/-londelta

   Time of interest:
     -f X   Gather data up to X hours into the future, from the start of the most recent model. (Note that this can be up to 8 hours in the past.) Make sure you get enough for the flight!   
   
   GFS Model Choice:
     -m <model>    Choose between either:
           0p50  - 0.5 Degree Spatial, 3-hour Time Resolution
           0p25_1hr - 0.25 Degree Spatial, 1-hour Time Resolution (default)

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

There is also a command-line utility, `predict.py`, which allows performing predictions with launch parameter variations:
```
usage: predict.py [-h] [-a ASCENTRATE] [-d DESCENTRATE] [-b BURSTALT]
                  [--launchalt LAUNCHALT] [--latitude LATITUDE]
                  [--longitude LONGITUDE] [--time TIME] [-o OUTPUT]
                  [--altitude_deltas ALTITUDE_DELTAS]
                  [--time_deltas TIME_DELTAS] [--absolute]

optional arguments:
  -h, --help            show this help message and exit
  -a ASCENTRATE, --ascentrate ASCENTRATE
                        Ascent Rate (m/s). Default 5m/s
  -d DESCENTRATE, --descentrate DESCENTRATE
                        Descent Rate (m/s). Default 5m/s
  -b BURSTALT, --burstalt BURSTALT
                        Burst Altitude (m). Default 30000m
  --launchalt LAUNCHALT
                        Launch Altitude (m). Default 0m
  --latitude LATITUDE   Launch Latitude (dd.dddd)
  --longitude LONGITUDE
                        Launch Longitude (dd.dddd)
  --time TIME           Launch Time (string, UTC). Default = Now
  -o OUTPUT, --output OUTPUT
                        Output KML File. Default = prediction.kml
  --altitude_deltas ALTITUDE_DELTAS
                        Comma-delimited list of altitude deltas. (metres).
  --time_deltas TIME_DELTAS
                        Comma-delimited list of time deltas. (hours)
  --absolute            Show absolute altitudes for tracks and placemarks.
```

For example, to predict a radiosonde launch from Adelaide Airport (5m/s ascent, 26km burst, 7.5m/s descent), but to look at what happens if the burst altitude is higher or lower than usual:
```
$ python3 predict.py --latitude=-34.9499 --longitude=138.5194 -a 5 -d 7.5 -b 26000 --time "2018-01-27 11:15Z" --altitude_deltas="-2000,0,2000"
Running using GFS Model: gfs20180127-00z
2018-01-27T11:15:00+00:00 5.0/24000.0/7.5 - Landing: -34.8585, 138.9600 at 2018-01-27T13:03:33
2018-01-27T11:15:00+00:00 5.0/26000.0/7.5 - Landing: -34.8587, 138.8870 at 2018-01-27T13:11:01
2018-01-27T11:15:00+00:00 5.0/28000.0/7.5 - Landing: -34.8598, 138.7990 at 2018-01-27T13:18:22
KML written to prediction.kml
```

A few other example scripts are located in the 'apps' directory:
 * basic_usage.py - Example showing how to write a predicted flight path out to a KML file
 * sonde_predict.py - A more complex example, where predictions for the next week's of radiosonde flights are run and written to a KML file.



