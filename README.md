Paegan - The Python CDM for Met/Ocean data
===========
Paegan attempts to fill the need for a high level common data model (CDM) library for array based met/ocean data stored in netCDF files or distributed over OPeNDAP.


Common Dataset Functions
------------------
### Grids / UGrids

```python
from paegan.cdm.dataset import CommonDataset
url = "http://thredds.axiomalaska.com/thredds/dodsC/PWS_DAS.nc"
pd = CommonDataset.open(url)
```

#### Subsets
#####Bbox
```python
pd.restrict_bbox((-74, 40, -70, 42))
```
#####Time
```python
from datetime import datetime,timedelta
ending = datetime.utcnow()
starting = ending - timedelta(hours=12)
pd.restrict_time((starting, ending))
```
#####Depth
```python
pd.restrict_depth((3,50))
```
#####Variables
```python
pd.restrict_vars(("u","v"))
```

#### Nearest subsetting

#####Time
```python
from datetime import datetime
import pytz
now = datetime.utcnow().replace(tzinfo=pytz.utc)
pd.nearest_time(now)
```

#####Depth
```python
pd.nearest_depth(5)
```

#### Regridding

##### Coming Soon

### Discrete Sampling Geometries

#### Coming Soon

Setup
------------------
You are using `virtualenv`, right?

1. Install [virtualenv-burrito](https://github.com/brainsik/virtualenv-burrito)
2. Create virtualenv named "paegan-dev": `mkvirtualenv -p your_python_binary paegan-dev`
3. Start using your new virtualenv: `workon paegan-dev`

Installation
-------------
Paegan requires python 2.7.x and is available on PyPI.

The best way to install Paegan is through pip:

```bash
pip install paegan
```

Paegan requires the following python libraries which will be downloaded and installed through `pip`:

* numpy==1.6.2
* netCDF4==1.0.2 (requires netcdf and hdf5 C libraries)
* Shapely==1.2.17 (requires geos C library)
* pytz==2012h
* python-dateutil==2.1

If your NetCDF4 and HDF5 libraries are in non-typical locations, you will need to pass the locations to the `pip` command:
```bash
NETCDF4_DIR=path HDF5_DIR=path pip install paegan
```

There seems to be a problem installing numpy through `pip` so you may need to install numpy before doing any of the above:

```bash
pip install numpy==1.6.2
```

Roadmap
--------
* CF-1.6 Discrete Sampling Geometry support
* Better grid support
* Regridding tools


Modules
--------
Other modules making use of Paegan

* [paegan-transport](https://github.com/asascience-open/paegan-transport) - Parallelized Lagrangian transport model for NetCDF/OPeNDAP data
* [paegan-viz](https://github.com/asascience-open/paegan-viz) - Visualization tools for NetCDF/OPeNDAP data


Troubleshooting
---------------
If you are having trouble getting any of the paegan functionality to work, try running the tests:

```bash
git clone git@github.com:asascience-open/paegan.git`
cd paegan
pip install pytest
python runtests.py
```

Contributors
----------------
* Kyle Wilcox <kwilcox@asascience.com>
* Alex Crosby <acrosby@asascience.com>

