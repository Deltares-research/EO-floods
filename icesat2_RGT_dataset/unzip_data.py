import zipfile
from glob import glob

files = glob(r"C:\Users\jong\Projects\Data\icesat2_RGT_data\\*.zip")
dir_extracted = r"C:\Users\jong\Projects\Data\icesat2_RGT_data\\"

for file in files:
    with zipfile.ZipFile(file, "r") as zip_ref:
        zip_ref.extractall(dir_extracted)
