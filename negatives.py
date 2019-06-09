import numpy as np
import random
import pathlib
import shutil
import os.path

import layers
import loaders
import helpers

TILESIZE = 256
BATCHSIZE = 7439

def path2xy(path):
    f = path.stem
    sx = f[1:7]
    sy = f[8:14]
    return (int(sx), int(sy))

if __name__ == "__main__":
#    box = (27.5682,53.8469,27.5741,53.8688) # south radius
    box = (27.4026,53.8306,27.7003,53.9739) # whole city
    
    mp = helpers.MercatorPainter(*box)
    lamps = loaders.query_nodes(*box)
    roads = loaders.query_ways(*box)
    mp.add_dots(lamps)      
    for nodes in roads.values():
        mp.add_polyline(nodes, width=2)
    
    source = layers.maxar.tiledir
    candidates = [path2xy(path) for path in source.glob("*.jpg")]
    print(len(candidates))
    confirmed = list(filter(lambda x: not mp.contains(x), candidates))
    print(len(confirmed))
    random.shuffle(confirmed)
    
    if len(confirmed) >= BATCHSIZE:
        batch = confirmed[:BATCHSIZE]
    else:
        raise ValueError("not enough local tiles")
        batch = confirmed
    
    while BATCHSIZE > len(batch):
        batch.append(mp.find_random())

    
    target = pathlib.Path('lamps/train/nolamp')
    target.mkdir(parents=True, exist_ok=True) 
             
    for (tx,ty) in batch:
        fname = layers.maxar.download(tx,ty)
        dst = target / ("m_" + os.path.basename(fname))
        shutil.copy(fname, dst)
