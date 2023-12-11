## Introduction
An easy to use wrapper of Hydrafloods and Google Earth Engine for creating flood maps of EO data. This package is aimed at users that do not qualify themselves as remote sensing experts but do want to create usable flood maps from EO.

### Installation
The recommended way to install EO-Floods is by using conda or mamba and the environment.yml.

```
mamba env create -f environment.yml
```

Then activate the environment.yml:

```
conda activate EO-Floods
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
