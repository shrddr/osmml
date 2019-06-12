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

# imagery zoom level
IMZ = 19

# if you want to train faster
LIMIT = 5000

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
    
    target = cleandir('lamps-orig/lamp')
    for lamp in lamps:
        fname = layers.maxar.gettile_wgs(lamp, IMZ, skipedge=True)
        if fname is not None:
            dst = target / ("m_" + os.path.basename(fname))
            shutil.copy(fname, dst)
    
    # MAKE NEGATIVES
    
    mp = helpers.MercatorPainter(layers.maxar, *box, IMZ)
    mp.add_dots_wgs(lamps)
    roads = loaders.query_ways(*box)
    for nodes in roads.values():
        mp.add_polyline_wgs(nodes, width=2)
    
    batch = []
    while len(batch) < LIMIT:
        batch.append(mp.random_negative())

    target = cleandir('lamps-orig/nolamp')
    for (tx,ty) in batch:
        fname = layers.maxar.download(tx, ty, IMZ)
        if fname is not None:
            dst = target / ("m_" + os.path.basename(fname))
            shutil.copy(fname, dst)

    tarball = "./lamps-orig.tar"
    if os.path.exists(tarball):
        os.remove(tarball)
    tar = tarfile.open(tarball, "w")
    tar.add("./lamps-orig")
    tar.close()
