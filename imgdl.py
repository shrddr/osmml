import numpy as np
import os.path
import cv2
import math


import time

import layers
import loaders
import helpers

def getcrop(layer, latlng, h, w, z=19):
    # crops an image or returns existing cached crop
    fname = layer.cropfile.format(lat=helpers.mil(latlng[0]),
                                  lng=helpers.mil(latlng[1]),
                                  z=z)
    if os.path.isfile(fname):
        crop = cv2.imread(fname)
        return crop
    
    image, (cx,cy) = layers.gettiles(layer, latlng, h, w)
        
    print("cropping")
    crop = image[cy-h//2:cy+h//2, cx-w//2:cx+w//2, :]
    cv2.imwrite(fname, crop)
    return crop

if __name__ == "__main__":
    
#    lamps = loaders.bbox(27.4583,53.9621,27.5956,53.9739) # north belt
#    lamps = loaders.bbox(27.5682,53.8469,27.5741,53.8688) # south radius
    lamps = loaders.bbox(27.4026,53.8306,27.7003,53.9739) # whole city
        
    start = time.time()
    for lamp in lamps:
        crop = getcrop(layers.maxar, lamp, 256, 256)
    print(time.time() - start)