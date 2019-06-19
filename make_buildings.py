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
#    box = (27.4631,53.9359,27.4989,53.9566)
    box_minsk = (27.4013,53.8157,27.7827,53.9739)
#    box_hrodna = (23.7483,53.5909,23.9145,53.7544)   
    
    # These areas are where active construction/destruction is 
    # going on and the satellite imagery is outdated compared to OSM.
    # Use http://geojson.io to generate, but swap order (first LAT, then LNG)
    outdated_polys = [
       [[53.87178633, 27.52624511],
        [53.86988859, 27.52392768],
        [53.86009488, 27.54053592],
        [53.85908248, 27.55491256],
        [53.86371401, 27.55195140],
        [53.87160922, 27.55263805],
        [53.87244420, 27.53538608],
        [53.87178633, 27.52624511]],
       [[53.83925981, 27.59031772],
        [53.83752519, 27.59154081],
        [53.83652491, 27.59896516],
        [53.83890529, 27.59769916],
        [53.84100701, 27.59302139],
        [53.83925981, 27.59031772]]
    ]
          
    q = loaders.Querier()
    ways = q.query_buildings(*box_minsk)
    
    IMZ = 18
#    LIMIT = 10000
#    count = 0
#    target = helpers.cleandir(f"buildings/yes")
#    for wayid,nodes in ways:
#        print(wayid)
#        # fetch every tile the building has a node at
#        for node in nodes:
#            fpath = layers.maxar.gettile_wgs(node, IMZ, skipedge=True, edge=24)
#            if fpath is None:
#                continue
#            fname = os.path.basename(fpath)
#            dst = target / fname
#            if not os.path.isfile(dst):
#                shutil.copy(fpath, dst)
#                count += 1
#                
#        if count >= LIMIT:
#            break
            
#         OR focus on the building and crop
#        image = layers.maxar.tiles_way(nodes, IMZ, pad_pct=0.25, pad_px=48)
#        dst = str(target / f"m{wayid}.jpg")
#        cv2.imwrite(dst, image)
        
    mp = helpers.MercatorPainter(layers.maxar, *box_minsk, IMZ)
    for _, nodes in ways:
        mp.add_polyline_wgs(nodes)
    for poly in outdated_polys:
        mp.add_fillpoly_wgs(poly)
    mp.show()
        
#    target = helpers.cleandir(f"buildings/no")
#    
#    train = []
#    start = time.time()
#    for i in range(LIMIT):
#        tx, ty = mp.random_negative()
#        print(tx,ty)
#        fname = layers.maxar.download(tx, ty, IMZ)  
##        wgs = layers.wgs_at_tile(tx, ty, IMZ)
##        print(f"https://www.openstreetmap.org/edit#map=18/{wgs[0]}/{wgs[1]}")    
##        img = cv2.imread(fname)
##        cv2.imshow("sanity check", img)
##        cv2.waitKey(0)
#
#        dst = str(target / f"m_x{tx}y{ty}.jpg")
#        if not os.path.exists(dst):
#            shutil.copy(fname, dst)
#    
#    
#    tarball = "./buildings.tar"
#    if os.path.exists(tarball):
#        os.remove(tarball)
#    tar = tarfile.open(tarball, "w")
#    tar.add("./buildings")
#    tar.close()