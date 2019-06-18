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
#    box_linetype = (27.643,53.843,27.647,53.846)
#    box_hrodna = (23.7483,53.5909,23.9145,53.7544)
    
    irl_destroyed = []
    irl_completed = []
    
    q = loaders.Querier()
    ways = q.query_buildings(*box_minsk)
    
    IMZ = 18
#    target = helpers.cleandir(f"buildings/yes")
#    for wayid,nodes in ways:
#        print(wayid)
#        
#        # fetch every tile the building touches
#        for i,node in enumerate(nodes):
#            fname = layers.maxar.gettile_wgs(node, IMZ, skipedge=True, edge=16)
#            if fname is None:
#                continue
#            dst = str(target)
#            shutil.copy(fname, dst)
            
        # OR focus on the building and crop
#        image = layers.maxar.tiles_way(nodes, IMZ, pad_pct=0.25, pad_px=48)
#        dst = str(target / f"m{wayid}.jpg")
#        cv2.imwrite(dst, image)
        
    mp = helpers.MercatorPainter(layers.maxar, *box_minsk, IMZ)
    for wayid,nodes in ways:
        mp.add_polyline_wgs(nodes, width=1)
#    mp.show_fixedwindow(600, 600)
#    mp.random_check(151202,84361)
#    cv2.destroyAllWindows()
        
    target = helpers.cleandir(f"buildings/no")
    
    train = []
    TRAIN = 5755
    start = time.time()
    for i in range(TRAIN):
        tx, ty = mp.random_negative()
        print(tx,ty)
        fname = layers.maxar.download(tx, ty, IMZ)  
#        wgs = layers.wgs_at_tile(tx, ty, IMZ)
#        print(f"https://www.openstreetmap.org/edit#map=18/{wgs[0]}/{wgs[1]}")    
#        img = cv2.imread(fname)
#        cv2.imshow("sanity check", img)
#        cv2.waitKey(0)

        dst = str(target / f"m_x{tx}y{ty}.jpg")
        if not os.path.exists(dst):
            shutil.copy(fname, dst)
    
    
    tarball = "./buildings.tar"
    if os.path.exists(tarball):
        os.remove(tarball)
    tar = tarfile.open(tarball, "w")
    tar.add("./buildings")
    tar.close()