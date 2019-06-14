import cv2
import time
import math
import os.path
import random
import tarfile

from lib import layers
from lib import loaders
from lib import helpers

TILESIZE = 256
              
def mil(fp):
    return math.floor(fp*1000000)
        
if __name__ == "__main__": 
    box_small = (27.4819,53.9392,27.4882,53.9432)
    box_minsk = (27.4013,53.8157,27.7827,53.9739)
    box_hrodna = (23.7483,53.5909,23.9145,53.7544)
    q = loaders.Querier()
    cats = ["flat", "hipped", "gabled"]
    ways = {cat:[] for cat in cats}
    for cat in cats:
        ways[cat] += q.query_shape(cat, *box_minsk)
        ways[cat] += q.query_shape(cat, *box_hrodna)
        print(cat, len(ways[cat]))
    
    counts = [(cat, len(ways[cat])) for cat in cats]
    counts.sort(key=lambda x: x[1])
    print(counts)
    
        
    IMZ = 18
    LIMIT = None
    LIMIT = counts[0][1] # use smallest category size to limit others
    for cat,count in counts:
        target = helpers.cleandir(f"roofshapes/{cat}")
#        random.shuffle(ways[cat])
        if LIMIT is not None:
            ways[cat] = ways[cat][:LIMIT]
        for wayid, nodes in ways[cat]:
            image = layers.maxar.tiles_way(nodes, IMZ)
#            print(image.shape)
#            if helpers.outside(image.shape[:2], (50,50), (500,500)):
#                continue
#            cv2.imshow('crop', image)
#            cv2.waitKey(0)
#            cv2.destroyAllWindows()
            dst = str(target / f"{wayid}.jpg")
            cv2.imwrite(dst, image)
            
    tarball = "./roofshapes.tar"
    if os.path.exists(tarball):
        os.remove(tarball)
    tar = tarfile.open(tarball, "w")
    tar.add("./roofshapes")
    tar.close()