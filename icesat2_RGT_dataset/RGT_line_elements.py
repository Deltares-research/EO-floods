from glob import glob
import geopandas as gpd
import fiona

fiona.drvsupport.supported_drivers[
    "LIBKML"
] = "rw"  # enable LIBKML driver for geopandas

cycle_dirs = glob(r"C:\Users\jong\Projects\Data\icesat2_RGT_data\\*")

for cycle_dir in cycle_dirs:
    kml_files = glob(cycle_dir + "/*.kml")
    for kml_file in kml_files:
        pass

### TODO ###
# check the GEE requirements for uploading a shp
# Get cycle number, date, and linesection number from file name
# open KML file with geopandas
# concatenate gdf with initialized gdf
# write final gdf to shp
