import math
import cv2
import random
import numpy as np

import layers
import loaders

def mil(fp):
    return math.floor(fp*1000000)

def locate_tile(tx, ty, z=19):
    # converts tileindex to EPSG:3857 (0..1) then to EPSG:4326 (degrees)
    scale = 1 << z
    x = tx / scale
    y = ty / scale
    lng = 180 * (2 * x - 1)   
    lat = 180 / math.pi * (2 * math.atan( math.exp( (1 - 2 * y) * math.pi )) - math.pi / 2)
    print(f"https://www.openstreetmap.org/edit#map={z}/{lat}/{lng}")
    return (lat,lng)

class MercatorPainter:
    # paints an area with dots and lines representing positive examples.
    # everything not painted over is supposed to be negative.
    # uses dict for fast lookup (builds itself on first query)
    # also has a random shot
    def __init__(self, W, S, E, N):   
        txmin, tymin = layers.tile_at((N, W))
        txmax, tymax = layers.tile_at((S, E))
        area = (txmax-txmin, tymax-tymin)
        print(f"paint area: {txmin}..{txmax}, {tymin}..{tymax}")
        print(f"dimensions: {area} -> {area[0]*area[1]} tiles total")
        
        self.txmin = txmin
        self.tymin = tymin
        self.canvas = np.zeros((tymax-tymin+1, txmax-txmin+1), np.uint8)
        
        self.dict = None
    
    def wgs2px(self, latlng):
        tx, ty = layers.tile_at(latlng)
        x = tx - self.txmin
        y = ty - self.tymin
        return (x,y)

    def add_dot_tile(self, tile, color=255):
        tx, ty = tile
        x = tx - self.txmin
        y = ty - self.tymin
        self.canvas[y][x] = color
            
    def add_dots(self, latlngs, color=255):
        for latlng in latlngs:
            x, y = self.wgs2px(latlng)
            self.canvas[y][x] = color
            
    def add_line(self, latlng1, latlng2, width):
        # the lines are actually curves in mercator but we don't care
        p1 = self.wgs2px(latlng1)
        p2 = self.wgs2px(latlng2)
        cv2.line(self.canvas, p1, p2, 255, width)
    
    def add_polyline(self, latlngs, width):
        pixels = [self.wgs2px(l) for l in latlngs]
        pixels = np.array(pixels)
        cv2.polylines(self.canvas, [pixels], False, 255, width)
        
    def show(self):
        cv2.imshow('canvas', self.canvas)
        cv2.waitKey(0)
    
    def reindex(self):
        d = {}
        h, w = self.canvas.shape
        for y in range(h):
            ty = self.tymin + y
            for x in range(w):
                tx = self.txmin + x
                if self.canvas[y][x] == 255:
                    if tx in d:
                        d[tx].append(ty)
                    else:
                        d[tx] = [ty]
        for k in d:
            d[k] = set(d[k])
        self.dict = d
        
    def contains(self, tile):
        if self.dict is None:
            self.reindex()

        tx, ty = tile
        if tx in self.dict:
            if ty in self.dict[tx]:
                return True
        return False
    
    def find_random(self):
        h, w = self.canvas.shape
        
        while True: 
            tx = random.randrange(self.txmin, self.txmax+w) # that's dumb maybe just walk through the dict?
            ty = random.randrange(self.tymin, self.tymax+h)
            tile = (tx, ty) 
            if self.contains(tile):
                continue
            else:
                return tile
        
if __name__ == "__main__":
#    box = (27.5682,53.8469,27.5741,53.8688) # south radius
    box = (27.4026,53.8306,27.7003,53.9739) # whole city
    lamps = loaders.query_nodes(*box)
    roads = loaders.query_ways(*box)
    
    mp = MercatorPainter(*box)
    mp.add_dots(lamps)  
    
    for nodes in roads.values():
        mp.add_polyline(nodes, width=1)
       
    mp.show()

    print(mp.contains((302116, 168700)))
