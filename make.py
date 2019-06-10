import pathlib
import shutil
import os.path
import random
import cv2

import layers
import loaders
import helpers
import tarfile

# use one original tile or expand it for later cropping
MAKE_POSITIVE_ORIGINAL = 0
MAKE_POSITIVE_EXPANDED = 0
MAKE_NEGATIVE_ORIGINAL = 0
MAKE_NEGATIVE_EXPANDED = 1

# this is 256 for all current imagery providers
TILESIZE = 256

# make sure we don't crop a lamp away:
# known satellite imagery has up to 40px offset.
# maximum acceptable padding is (128-40)=88
# which translates to image size 256+88*2=432
PADDING = 88

if __name__ == "__main__": 
#    box = (27.4583,53.9621,27.5956,53.9739) # north belt
#    box = (27.5682,53.8469,27.5741,53.8688) # south radius
    box = (27.4026,53.8306,27.7003,53.9739) # whole city    
    
    # MAKE POSITIVES
    
    lamps = loaders.query_nodes(*box)
    print("lamps:", len(lamps))
    
    if MAKE_POSITIVE_ORIGINAL: 
        # only use one tile where lamp exists
        target = pathlib.Path('lamps-orig/lamp')
        target.mkdir(parents=True, exist_ok=True)
        
        for lamp in lamps:
            fname = layers.maxar.gettile_wgs(lamp, skipedge=True)
            if fname is not None:
                dst = target / ("m_" + os.path.basename(fname))
                shutil.copy(fname, dst)

    if MAKE_POSITIVE_EXPANDED:
        # use a bigger picture, centered at the object, 
        # for later random cropping (augmentation)
        target = pathlib.Path('lamps-center/lamp')
        target.mkdir(parents=True, exist_ok=True)
        
        for lamp in lamps:        
            h = w = PADDING + TILESIZE + PADDING
            crop = layers.maxar.getcrop_wgs(lamp, h, w)
            lat = helpers.mil(lamp[0])
            lng = helpers.mil(lamp[1])
            dst = str(target / f"m_lat{lat}lng{lng}z19.jpg")
            cv2.imwrite(dst, crop)
    
    
    # MAKE NEGATIVES
    # (find points in box where no lamps should be)
    
    BATCHSIZE = len(lamps)
    
    mp = helpers.MercatorPainter(layers.maxar, *box)
    mp.add_dots_wgs(lamps)
    roads = loaders.query_ways(*box)
    for nodes in roads.values():
        mp.add_polyline_wgs(nodes, width=2)
    
    source = layers.maxar.tiledir
    localtiles = [layers.maxar.xy_fromfile(path) for path in source.glob("*.jpg")]
    print("local tiles found:", len(localtiles))
    negatives = list(filter(lambda x: not mp.contains(x), localtiles))
    print("confirmed negative:", len(negatives))
    random.shuffle(negatives)
    
    if len(negatives) >= BATCHSIZE:
        batch = negatives[:BATCHSIZE]
    else:
        print("not enough local tiles. downloading more")
        batch = negatives
        while BATCHSIZE > len(batch):
            batch.append(mp.find_random())

    if MAKE_NEGATIVE_ORIGINAL: 
        # only use one tile
        target = pathlib.Path('lamps-orig/nolamp')
        target.mkdir(parents=True, exist_ok=True) 
        for (tx,ty) in batch:
            fname = layers.maxar.download(tx,ty)
            dst = target / ("m_" + os.path.basename(fname))
            shutil.copy(fname, dst)
        
    if MAKE_NEGATIVE_EXPANDED:
        # expand the tile for later cropping
        target = pathlib.Path('lamps-center/nolamp')
        target.mkdir(parents=True, exist_ok=True) 
        for (tx,ty) in batch:
            wgs = layers.wgs_at_tile(tx, ty)
            h = w = PADDING + TILESIZE + PADDING
            crop = layers.maxar.getcrop_wgs(wgs, h, w)
            lat = helpers.mil(wgs[0])
            lng = helpers.mil(wgs[1])
            dst = str(target / f"m_lat{lat}lng{lng}z19.jpg")
            cv2.imwrite(dst, crop)
    
    if MAKE_POSITIVE_ORIGINAL and MAKE_NEGATIVE_ORIGINAL:
        tarball = "./lamps-orig.tar"
        if os.path.exists(tarball):
            os.remove(tarball)
        tar = tarfile.open(tarball, "w")
        tar.add("./lamps-orig")
        tar.close()
    
    if MAKE_POSITIVE_EXPANDED and MAKE_NEGATIVE_EXPANDED:
        tarball = "./lamps-center.tar"
        if os.path.exists(tarball):
            os.remove(tarball)
        tar = tarfile.open(tarball, "w")
        tar.add("./lamps-center")
        tar.close()