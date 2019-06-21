import cv2
import time
import math
import shutil
import os.path
import random
import tarfile

from lib import layers
from lib import loaders
from lib import helpers
              
def mil(fp):
    return math.floor(fp*1000000)
        
if __name__ == "__main__":
    # bounding box to work on
    box_minsk = (27.4013,53.8157,27.7827,53.9739)
#    box_hrodna = (23.7483,53.5909,23.9145,53.7544)   
    
    # These areas are where active construction/destruction is 
    # going on and the satellite imagery is outdated compared to OSM.
    # Use http://geojson.io to draw, then export as WKT
    with open("make_buildings_except.wkt") as reader:
        wkt = reader.read()
    # or just initialise with [] if you have nothing to exclude
    outdated_polys = helpers.latlngs_from_wkt(wkt)
          
    q = loaders.Querier()
    ways = q.query_buildings(*box_minsk)
    
    IMZ = 18
    LIMIT = 5000
    count = 0
    target = helpers.cleandir(f"buildings/yes")
    for wayid,nodes in ways:
        print(wayid)
        # fetch every tile the building has a node at
        for node in nodes:
            fpath = layers.maxar.gettile_wgs(node, IMZ, skipedge=True, edge=24)
            if fpath is None:
                continue
            fname = os.path.basename(fpath)
            dst = target / fname
            if not os.path.isfile(dst):
                shutil.copy(fpath, dst)
                count += 1      
                
        if count >= LIMIT:
            break
        
    mp = helpers.MercatorPainter(layers.maxar, *box_minsk, IMZ)
    for _, nodes in ways:
        mp.add_polyline_wgs(nodes)
    # FIXME: painter expands area to a whole number of tiles
    # and marks the border tile free even if there are
    # buildings in the expansion band
    for poly in outdated_polys:
        mp.add_fillpoly_wgs(poly)
    
    target = helpers.cleandir(f"buildings/no")
    
    train = []
    start = time.time()
    for i in range(LIMIT):
        tx, ty = mp.random_negative()
        print(tx,ty)
        fname = layers.maxar.download(tx, ty, IMZ)  

        dst = str(target / f"m_x{tx}y{ty}.jpg")
        if not os.path.exists(dst):
            shutil.copy(fname, dst)
    
    
    tarball = "./buildings.tar"
    if os.path.exists(tarball):
        os.remove(tarball)
    tar = tarfile.open(tarball, "w")
    tar.add("./buildings")
    tar.close()