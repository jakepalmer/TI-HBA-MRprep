from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import Normalizer
import nibabel as nib
# from nilearn import plotting
import re
import numpy as np
import pandas as pd
import os
from os import listdir, fsencode
import math
from PIL import Image
import sys
import os
from glob import glob

subject = str(sys.argv[1])
directory = str(sys.argv[2])

y = 0
names = []

file = f"{subject}_brain_MNI.nii.gz"
myFile = os.fsencode(file)
myFile = myFile.decode("utf-8")
myNifti = nib.load((directory + "/" + myFile))

y = 1+y
data = myNifti.get_data()
data = data*(185.0/np.percentile(data, 97))

scaler = StandardScaler()
names.append(myFile)

for sl in range(0, 80):
    x = sl
    clipped = data[:, :, (45+x)]
    image_data = Image.fromarray(clipped).convert("RGB")
    image_data.save(
        (directory + "/Test/" + myFile[:-7] + "-" + str(x) + ".jpg"))
