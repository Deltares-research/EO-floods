## Introduction
EO-Floods is an easy to use wrapper of Hydrafloods and Google Earth Engine for creating flood maps of Earth Observation (EO) data. This package is aimed at users that do not qualify themselves as remote sensing experts but do want to create usable flood maps from EO.

### Installation
EO-Floods is available at PyPI and can thus be easily installed with pip.
In a python environment of your choice run the following command:
```
pip install EO_Floods
```


### Earth Engine Authentication
An Earth Engine account is required to use the HydraFloods provider. To authenticate to Earth Engine you need an environment with Earth Engine installed and run the following code with a Python interpreter:
```
import ee
ee.Authenticate()
```
This code will trigger the authentication flow of Earth Engine.

Whenever you use Earth Engine in a script or notebook you first need to initialize the Earth Engine library.
```
import ee
ee.Initialize()
```
