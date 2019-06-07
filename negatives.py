import numpy as np
import cv2
import random

import layers
import loaders
import helpers

TILESIZE = 256
BATCHSIZE = 10000
negfile = "./negatives/x{x}y{y}z{z}.jpg"

if __name__ == "__main__":
#    box = (27.5682,53.8469,27.5741,53.8688) # south radius
    box = (27.4026,53.8306,27.7003,53.9739) # whole city
    
    W, S, E, N = box
    txmin, tymin = layers.tile_at((N, W))
    txmax, tymax = layers.tile_at((S, E))
    area = (txmax-txmin, tymax-tymin)
    print(f"search area: {txmin}..{txmax}, {tymin}..{tymax}")
    print(f"dimensions: {area} -> {area[0]*area[1]} tiles total")
    
    # tiles with no lamps and no road nodes 
    # we actually need to avoid road WAYS but this is much easier
    
    lamps = loaders.bbox(W, S, E, N)
    roadnodes = loaders.roads_bbox(W, S, E, N)
    exclude = lamps + roadnodes
    tiles = [layers.tile_at(e) for e in exclude]
    positives = helpers.Lookup(tiles)
    
    count = 0
    for i in range(BATCHSIZE):
        tx = random.randrange(txmin, txmax)
        ty = random.randrange(tymin, tymax)
        positive = positives.contains((tx, ty))
        if not positive:
            count += 1
#            img = layers.maxar.download(tx,ty)
            
            
    print(f"{100*count/BATCHSIZE}% negative")