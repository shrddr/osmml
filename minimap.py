import cv2
import numpy as np
from lib import helpers
from lib import layers

# shows how much is the box covered with cached tiles

IMZ = 18

if __name__ == "__main__": 
    box = (27.4026,53.8306,27.7003,53.9739)
    source = layers.maxar.tiledir / f"z{IMZ}"
    localtiles = [layers.maxar.xy_fromfile(path) for path in source.glob("*.jpg")]
#    localtiles = localtiles[:1000]
    
    W, S, E, N = box
    txmin, tymin = layers.maxar.tile_at_wgs((N, W), IMZ)
    txmax, tymax = layers.maxar.tile_at_wgs((S, E), IMZ)

    width = txmax-txmin+2
    height = tymax-tymin+2
    print(f"map size: {width}x{height}px")
    canvas = np.zeros((height, width, 3), np.uint8)
    
    for (tx,ty) in localtiles:
        fname = layers.maxar.download(tx, ty, IMZ)
        img = cv2.imread(fname)
        av = img.mean(axis=0).mean(axis=0)
        x = tx-txmin
        y = ty-tymin
        if helpers.outside((x,y), (0,0), (width, height)):
            continue
        canvas[y, x] = av
        
    cv2.imshow('canvas', canvas)
    cv2.waitKey(0)