import io
import cv2
import math
import time
import os.path
import requests
import numpy as np
from pathlib import Path

TILESIZE = 256

def get_or_sleep(sess, url, t=0.1):
    r = sess.get(url)
    if r.status_code == 200:
        return r
    else:
        print(r.status_code, "sleeping for:", t)
        time.sleep(t)
        return get_or_sleep(sess, url, t*2)
    
def project2web(latlng):
    # converts EPSG:4326 (degrees) to EPSG:3857 (0..TILESIZE)
    siny = math.sin(latlng[0] * math.pi / 180)
    siny = min(max(siny, -0.9999), 0.9999)
    x = TILESIZE * (0.5 + latlng[1] / 360)
    y = TILESIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
    return (x, y)

def wgs_at_tile(tx, ty, z):
    # converts tile index to EPSG:3857 (0..1) then to EPSG:4326 (degrees)
    scale = 1 << z
    x = tx / scale
    y = ty / scale
    lng = 180 * (2 * x - 1)   
    lat = 180 / math.pi * (2 * math.atan( math.exp( (1 - 2 * y) * math.pi )) - math.pi / 2)
    return (lat,lng)

class Imagery:
    
    def __init__(self, name):
        self.name = name
        self.session = requests.session()
        self.flipy = False
        self.offsetx = 0
        self.offsety = 0
        self.tiledir = Path("../tiles") / name
    
    def tilefile(self, x, y, z):
        path = self.tiledir / f"z{z}"
        if not os.path.exists(path):
            os.makedirs(path)
        return path / f"x{x}y{y}.jpg"
        
    def xy_fromfile(self, path):
        f = path.name
        sx = f[1:7]
        sy = f[8:14]
        return (int(sx), int(sy))
        
    def tileurl(self, x, y, z):
        scale = 1 << z
        if self.flipy:
            y = scale - y - 1
        return self.url.format(z=z, x=x, y=y)
    
    def download(self, x, y, z):
        # returns tile at index (as filename)
        fname = self.tilefile(x, y, z)
        if not os.path.isfile(fname):
            url = self.tileurl(x, y, z)
            print("downloading")
#            r = self.session.get(url)
            r = get_or_sleep(self.session, url)
            if r.status_code == 200:
                with io.open(fname, 'wb') as file:
                    file.write(r.content)
            else:
                raise IOError(f"{r.status_code} at {url}")

        return str(fname)
    
    def tile_at_wgs(self, latlng, z):
        # returns index of tile which contains a location
        scale = 1 << z
        wc = project2web(latlng)
        # pixel in world
        px = (wc[0] + self.offsetx) * scale 
        py = (wc[1] + self.offsety) * scale
        # tile in world
        tx = math.floor(px / TILESIZE)
        ty = math.floor(py / TILESIZE)
        return (tx, ty)
    
    def gettile_wgs(self, latlng, z, skipedge=False, edge=16):
        # returns tile at location (as filename)
        # returns None if skipedge is enabled and location is indeed close to edge 
        scale = 1 << z
        wc = project2web(latlng)
        # pixel in world
        px = (wc[0] + self.offsetx) * scale 
        py = (wc[1] + self.offsety) * scale
        # tile in world
        tx = math.floor(px / TILESIZE)
        ty = math.floor(py / TILESIZE)
        # pixel in tile
        rx = (px - tx) % TILESIZE
        ry = (py - ty) % TILESIZE

        if skipedge:
            edge = (rx < edge) or (rx >= TILESIZE-edge) \
                or (ry < edge) or (ry >= TILESIZE-edge)
            if edge:
                print("edge")
                return None
        
        fname = self.download(tx, ty, z)
        return fname
    
    def tiles_near_wgs(self, latlng, scale, h, w):
        # returns a 2d array of tile indices to download
        wc = project2web(latlng)
        px = (wc[0] + self.offsetx) * scale 
        py = (wc[1] + self.offsety) * scale
        
        # pixel coords
        pxmin = px - h/2
        pxmax = px + h/2
        pymin = py - h/2
        pymax = py + h/2
        
        # tile coords
        txmin = math.floor(pxmin / TILESIZE)
        txmax = math.floor(pxmax / TILESIZE)
        tymin = math.floor(pymin / TILESIZE)
        tymax = math.floor(pymax / TILESIZE)
        
        # array of tiles
        tiles = []
        for ty in range(tymin, tymax+1):
            row = []
            for tx in range(txmin, txmax+1):
                row.append((tx,ty))
            tiles.append(row)
    
        # point relative to topleft corner
        rx = round(px - txmin * TILESIZE)
        ry = round(py - tymin * TILESIZE)
        
        return tiles, (rx,ry)
    
    def gettiles_wgs(self, latlng, h, w, z):
        # returns image around a location (whole tiles, combined)
        scale = 1 << z
        tiles, center = self.tiles_near_wgs(latlng, scale, h, w)
        
        htiles = len(tiles)
        wtiles = len(tiles[0])
        result = np.zeros((htiles*TILESIZE, wtiles*TILESIZE, 3), dtype=np.uint8)
        
        ty = 0
        for row in tiles:
            tx = 0
            for (x,y) in row:
                fname = self.download(x, y, z)
                img = cv2.imread(fname)
                result[ty:ty+TILESIZE, tx:tx+TILESIZE, :] = img
                tx += TILESIZE           
            ty += TILESIZE
            
        return result, center
    
    def getcrop_wgs(self, latlng, h, w, z):
        # return image around a location (cropped exactly to h, w )
        image, (cx,cy) = self.gettiles_wgs(latlng, h, w, z)
        print("cropping")
        crop = image[cy-h//2:cy+h//2, cx-w//2:cx+w//2, :]
        return crop


maxar = Imagery("maxar")   
maxar.url = "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@jpg/{z}/{x}/{y}.jpg?connectId=91e57457-aa2d-41ad-a42b-3b63a123f54a"
maxar.flipy = True
maxar.offsetx = -30 / (1 << 19)
maxar.offsety = 10 / (1 << 19)

dg = Imagery("dg")
dg.url = "https://c.tiles.mapbox.com/v4/digitalglobe.316c9a2e/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqZGFrZ2c2dzFlMWgyd2x0ZHdmMDB6NzYifQ.9Pl3XOO82ArX94fHV289Pg"