import pathlib
import shutil
import os.path
import random
import cv2

import layers
import loaders
import helpers
import tarfile

# this is 256 for all current imagery providers
TILESIZE = 256

# make sure we don't crop a lamp away:
# known satellite imagery has up to 40px offset.
# maximum acceptable EXPAND_PAD is (128-40)=88
# which translates to image size 256+88*2=432
EXPAND_PAD = 0

# imagery zoom level
IMZ = 18

# total images of each category
LIMIT = 5000

# validation set share
VALID = 0.2

def cleandir(path):
    target = pathlib.Path(path)
    if os.path.isdir(target):
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return target
    
if __name__ == "__main__":
#    box = (27.4583,53.9621,27.5956,53.9739) # north belt
#    box = (27.5682,53.8469,27.5741,53.8688) # south radius
    box = (27.4026,53.8306,27.7003,53.9739) # whole city    
    
    # MAKE POSITIVES
    
    lamps = loaders.query_nodes(*box)
    print("lamps in box:", len(lamps))
    random.shuffle(lamps)
    lamps = lamps[:LIMIT]
    
#    target = cleandir('lamps-expand/train/lamp')
    target = cleandir('lamps-expand/lamp')
    for lamp in lamps:        
        h = w = EXPAND_PAD + TILESIZE + EXPAND_PAD
        crop = layers.maxar.getcrop_wgs(lamp, h, w, IMZ)
        lat = helpers.mil(lamp[0])
        lng = helpers.mil(lamp[1])
        dst = str(target / f"m_lat{lat}lng{lng}.jpg")
        cv2.imwrite(dst, crop)
        
#    target = cleandir('lamps-expand/valid/lamp')
    
    # MAKE NEGATIVES
    
    mp = helpers.MercatorPainter(layers.maxar, *box, IMZ)
    mp.add_dots_wgs(lamps)
    roads = loaders.query_ways(*box)
    for nodes in roads.values():
        mp.add_polyline_wgs(nodes, width=2)
    
    batch = []
    while len(batch) < LIMIT:
        batch.append(mp.random_negative())


#    target = cleandir('lamps-expand/train/nolamp')
        target = cleandir('lamps-expand/nolamp')
    for (tx,ty) in batch:
        wgs = layers.wgs_at_tile(tx, ty, IMZ)
        h = w = EXPAND_PAD + TILESIZE + EXPAND_PAD
        crop = layers.maxar.getcrop_wgs(wgs, h, w, IMZ)
        lat = helpers.mil(wgs[0])
        lng = helpers.mil(wgs[1])
        dst = str(target / f"m_lat{lat}lng{lng}.jpg")
        cv2.imwrite(dst, crop)
        
#    target = cleandir('lamps-expand/valid/lamp')
    
    # PACK FOR UPLOAD

    tarball = "./lamps-center.tar"
    if os.path.exists(tarball):
        os.remove(tarball)
    tar = tarfile.open(tarball, "w")
    tar.add("./lamps-center")
    tar.close()