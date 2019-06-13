import cv2
import random
import shutil
import os.path
import tarfile

from lib import layers
from lib import loaders
from lib import helpers

# this is 256 for all current imagery providers
TILESIZE = 256

# make sure we don't crop a lamp away:
# known satellite imagery has up to 40px offset.
# maximum acceptable EXPAND_PAD is (128-40)=88
# which translates to image size 256+88*2=432
EXPAND_PAD = 0

# imagery zoom level
IMZ = 18

# train images of each category
TRAIN = 4000

# validation images of each category
VALID = 1000
    
if __name__ == "__main__":
#    box = (27.4583,53.9621,27.5956,53.9739) # north belt
#    box = (27.5682,53.8469,27.5741,53.8688) # south radius
    box = (27.4026,53.8306,27.7003,53.9739) # whole city    
    
    # MAKE POSITIVES
    
    lamps = loaders.query_nodes(*box)
    print("lamps in box:", len(lamps))
    random.shuffle(lamps)
    train = lamps[:TRAIN]
    valid = lamps[TRAIN:]
    
    target = helpers.cleandir('lamps-expand/train/lamp')
    for lamp in train:        
        h = w = EXPAND_PAD + TILESIZE + EXPAND_PAD
        crop = layers.maxar.getcrop_wgs(lamp, h, w, IMZ)
        lat = helpers.mil(lamp[0])
        lng = helpers.mil(lamp[1])
        dst = str(target / f"m_lat{lat}lng{lng}.jpg")
        cv2.imwrite(dst, crop)
    
    
    target = helpers.cleandir('lamps-expand/valid/lamp')
    count = 0
    it = iter(valid)
    while count < VALID:
        lamp = next(it)
        fname = layers.maxar.gettile_wgs(lamp, IMZ, skipedge=True)
        if fname is not None:
            dst = target / ("m_" + os.path.basename(fname))
            if not os.path.exists(dst):
                shutil.copy(fname, dst)
                count += 1
    
    # MAKE NEGATIVES
    
    mp = helpers.MercatorPainter(layers.maxar, *box, IMZ)
    mp.add_dots_wgs(lamps)
    roads = loaders.query_ways(*box)
    for nodes in roads.values():
        mp.add_polyline_wgs(nodes, width=2)
    
    data = { 't': [], 'v': [] }
    for i in range(TRAIN):       
        data['t'].append(mp.random_negative())
    for i in range(VALID):
        data['v'].append(mp.random_negative())

    target = helpers.cleandir('lamps-expand/train/nolamp')
    for (tx,ty) in data['t']:
        wgs = layers.wgs_at_tile(tx, ty, IMZ)
        h = w = EXPAND_PAD + TILESIZE + EXPAND_PAD
        crop = layers.maxar.getcrop_wgs(wgs, h, w, IMZ)
        lat = helpers.mil(wgs[0])
        lng = helpers.mil(wgs[1])
        dst = str(target / f"m_lat{lat}lng{lng}.jpg")
        cv2.imwrite(dst, crop)
        
    target = helpers.cleandir('lamps-expand/valid/nolamp')
    for (tx,ty) in data['v']:
        fname = layers.maxar.download(tx, ty, IMZ)
        if fname is not None:
            dst = target / ("m_" + os.path.basename(fname))
            shutil.copy(fname, dst)
    
    # PACK FOR UPLOAD

    tarball = "./lamps-expand.tar"
    if os.path.exists(tarball):
        os.remove(tarball)
    tar = tarfile.open(tarball, "w")
    tar.add("./lamps-expand")
    tar.close()