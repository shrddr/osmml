import re
import cv2
import math
import random
import shutil
import os.path
import pathlib
import numpy as np

from lib import layers
from lib import loaders

def mil(fp):
    return math.floor(fp*1000000)

def osm_at_tile(tx, ty, z):
    # prints a link to open iD editor at specified tile
    lat, lng = layers.wgs_at_tile(tx, ty, z)
    print(f"https://www.openstreetmap.org/edit#map={z}/{lat}/{lng}")

def cleandir(path):
    # removes a directory and creates it again
    target = pathlib.Path(path)
    if os.path.isdir(target):
        shutil.rmtree(target)
    target.mkdir(parents=True)
    return target

def outside(point, lefttop, rightbot):
    # returns True if point is outside of the box defined by 2 corners
    return point[0] < lefttop[0] \
        or point[1] < lefttop[1] \
        or point[0] >= rightbot[0] \
        or point[1] >= rightbot[1]

class MercatorPainter:
    # paints an area with dots and lines representing positive examples.
    # everything not painted over is supposed to be negative.
    # uses dict for fast lookup (builds itself on first query).
    # also has a function to find a random negative (unpainted) pixel.
    # if more than 90% of canvas is busy, uses inverted index for random search.
    def __init__(self, layer, W, S, E, N, z):
        txmin, tymin = layer.tile_at_wgs((N, W), z)
        txmax, tymax = layer.tile_at_wgs((S, E), z)
        area = (txmax-txmin, tymax-tymin)
        print(f"paint area: {txmin}..{txmax}, {tymin}..{tymax}")
        print(f"dimensions: {area} -> {area[0]*area[1]} tiles total")
        
        self.z = z
        self.layer = layer
        self.txmin = txmin
        self.tymin = tymin
        self.width = txmax-txmin+1
        self.height = tymax-tymin+1
        self.canvas = np.zeros((self.height, self.width), np.uint8)
        
        self.dict_busy = None
        self.dict_free = None
        self.is_busy = False
    
    def wgs2px(self, latlng):
        tx, ty = self.layer.tile_at_wgs(latlng, self.z)
        x = tx - self.txmin
        y = ty - self.tymin
        return (x,y)

    def add_dot_tile(self, tile, color=255):
        tx, ty = tile
        x = tx - self.txmin
        y = ty - self.tymin
        self.canvas[y][x] = color
            
    def add_dots_wgs(self, latlngs, color=255):
        for latlng in latlngs:
            x, y = self.wgs2px(latlng)
            self.canvas[y][x] = color
            
    def add_line_wgs(self, latlng1, latlng2, width):
        # the lines are actually curves in mercator but we don't care
        p1 = self.wgs2px(latlng1)
        p2 = self.wgs2px(latlng2)
        cv2.line(self.canvas, p1, p2, 255, width)
    
    def add_polyline_wgs(self, latlngs, width=1):
        pixels = [self.wgs2px(ll) for ll in latlngs]
        pixels = np.array(pixels)
        # lineType means 4-connected or 8-connected
        cv2.polylines(self.canvas, [pixels], True, 255, width, lineType=4)
        
    def add_fillpoly_wgs(self, latlngs, width=1):
        print(latlngs)
        pixels = [self.wgs2px(ll) for ll in latlngs]
        print(pixels)
        pixels = np.array(pixels)
        # lineType means 4-connected or 8-connected
        cv2.fillPoly(self.canvas, [pixels], 255, lineType=4)
        
    def show(self):
        # displays the canvas at native resolution
        cv2.imshow('canvas', self.canvas)
        cv2.waitKey(0)
        
    def show_fixedwindow(self, h, w):
        # displays the canvas resized to specified dimensions
        # useful for very small or large maps
        cv2.namedWindow('canvas-fixed', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('canvas-fixed', h, w)
        cv2.imshow('canvas-fixed', self.canvas)
        cv2.waitKey(0)
    
    def build_index(self):
        # creates lookup dict of occupied pixels
        d = {}
        for y in range(self.height):
            ty = self.tymin + y
            for x in range(self.width):
                tx = self.txmin + x
                if self.canvas[y][x] != 0:
                    if tx in d:
                        d[tx].append(ty)
                    else:
                        d[tx] = [ty]
        for k in d:
            d[k] = set(d[k])
        self.dict_busy = d
    
    def build_index_free(self):
        # creates lookup dict of non-occupied pixels
        d = {}
        for y in range(self.height):
            ty = self.tymin + y
            for x in range(self.width):
                tx = self.txmin + x
                if self.canvas[y][x] == 0:
                    if tx in d:
                        d[tx].append(ty)
                    else:
                        d[tx] = [ty]
        self.dict_free = d
        
    def contains(self, tile, result_outside=True):
        if self.dict_busy is None:
            self.build_index()

        tx, ty = tile
        
        if tx < self.txmin or ty < self.tymin:
            return result_outside
        if tx >= self.txmin + self.width:
            return result_outside
        if ty >= self.tymin + self.height:
            return result_outside
        
        if tx in self.dict_busy:
            if ty in self.dict_busy[tx]:
                return True
        return False
    
    def random_negative(self):
        # returns a random free pixel and marks it busy
        # uses one method whichever is faster
        if self.is_busy:
            return self.random_free()
        else:
            return self.random_busy()
        
    def random_busy(self):
        # propose random, check if it's occupied, repeat
        if self.dict_busy is None:
            self.build_index()
        
        count = 0
        while True:
            count += 1
            if count > 10:
                # after 10 retries we assume the canvas is 90% full and
                # it's faster to look through free cells rather than occupied
                print("switching indexing")
                self.is_busy = True
                return self.random_free()
                
            x = random.randrange(self.width)
            y = random.randrange(self.height)
            
            if self.canvas[y][x] != 0:
                continue
            
            tx = self.txmin + x
            ty = self.tymin + y
            tile = (tx, ty)
            
            self.add_dot_tile(tile)
#            print("adding", tile, "retries", count)
            self.dict_busy[tx].add(ty)
            return tile
        
    def random_check(self, tx, ty):
        # use for debugging
        x = tx - self.txmin
        y = ty - self.tymin
        print(x, y, "free =", self.canvas[y][x] == 0)

    def random_free(self):
        # use dict of free pixels
        if self.dict_free is None:
            self.build_index_free()
            
        tx = random.choice(list(self.dict_free.keys()))
        ty = random.choice(self.dict_free[tx])
        tile = (tx, ty)
        self.add_dot_tile(tile)
#        lens = [len(l) for k,l in self.dict_free.items()]
#        print("adding", tile, "dict_free is", sum(lens))
        self.dict_free[tx].remove(ty)
        if self.dict_free[tx] == []:
            self.dict_free.pop(tx)
        return tile
        
if __name__ == "__main__":
#    box = (27.4026,53.8306,27.7003,53.9739)
#    lamps = [(53.85, 27.6), (53.92, 27.5)]
#    roads = [[(53.85, 27.5), (53.92, 27.6)]]
#    
#    mp = MercatorPainter(layers.maxar, *box, z=18)
#    mp.add_dots_wgs(lamps)  
#    
#    for nodes in roads:
#        mp.add_polyline_wgs(nodes, width=2)
#       
#    mp.show()
#
#    print(mp.contains((302304, 168755)))
    
    s = """POLYGON ((27.590317726135254 53.83925981221627, 27.591540813446045 53.837525198055296, 27.598965167999268 53.83652491343047, 27.59769916534424 53.83890529837573, 27.593021392822266 53.84100701515295, 27.590317726135254 53.83925981221627))
             POLYGON ((27.52676010131836 53.87231769137863, 27.52371311187744 53.869939206161845, 27.5392484664917 53.86017081679297, 27.558088302612305 53.85801944014527, 27.560791969299316 53.86885113060123, 27.55173683166504 53.87188754981568, 27.53920555114746 53.872849036613374, 27.52676010131836 53.87231769137863))"""
    nums = re.findall(r'\d+(?:\.\d*)?', s.rpartition(',')[0])
    coords = zip(*[iter(nums)] * 2)
    for c in coords:
        print(c)