import pathlib
import shutil
import os.path

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
    
    # work area
    
#    lamps = loaders.query_nodes(27.4583,53.9621,27.5956,53.9739) # north belt
#    lamps = loaders.query_nodes(27.5682,53.8469,27.5741,53.8688) # south radius
    lamps = loaders.query_nodes(27.4026,53.8306,27.7003,53.9739) # whole city
    
    target = pathlib.Path('lamps/train/lamp')
    target.mkdir(parents=True, exist_ok=True)

    # only use one tile where a lamp exists

    print(len(lamps))
    for lamp in lamps:
        fname = layers.gettile(layers.maxar, lamp)
        dst = target / ("m_" + os.path.basename(fname))
        shutil.copy(fname, dst)
#        fname = layers.gettile(layers.dg, lamp)
#        shutil.copy(fname, target)
    
    # use a bigger picture for later random cropping (augmentation).
    # make sure we don't crop a lamp away:
    # known satellite imagery has up to 40px offset
    # maximum acceptable augmentation shift is (128-40)=88
    # means we prepare images of size 256+88*2=432
    
#    for lamp in lamps:
#        crop = getcrop(layers.maxar, lamp, 432, 432)