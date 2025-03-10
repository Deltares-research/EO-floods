## Introduction

EO-Floods aims to provide an easy to use interface for generating or retrieving flood data from Earth Observation (EO) data. It does this by wrapping the Hydrafloods package for access to the Google Earth Engine (GEE) and providing access to the Copernicus Global Flood Monitor (GFM). This package is aimed at users that do not qualify themselves as remote sensing experts but do want to create usable flood maps from EO.

## Requirements

To use the Hydrafloods provider an Earth Engine account and project is required, register [here](https://code.earthengine.google.com/register).
For authenticating to Earth Engine see the paragraph below.

You also need an account for GFM. You can register [here](https://portal.gfm.eodc.eu/register).

### Earth Engine Authentication

To authenticate to Earth Engine you need an environment with Earth Engine installed and run the following code with a Python interpreter:

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

### GFM Authentication

You can authenticate for the GFM API when you initialize a FloodMap instance with the 'GFM' provider. You will be prompted with an input box for your email and password.

### Installing

The current version is not pip installable yet. For now the package can be used by installing the conda environment from the environment.yml and do a developer install

```
conda env create -f environment.yml
conda activate EO-Floods
pip install -e .
```

## Examples

There are two example notebooks for the GFM and Hydrafloods providers located in the notebooks folder. These showcase the basic outline of a workflow for deriving flood maps from these two providers.
