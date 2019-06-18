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
    x = (tx + 0.5) / scale
    y = (ty + 0.5) / scale
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
        # combines tile indices into filename string
        path = self.tiledir / f"z{z}"
        if not os.path.exists(path):
            os.makedirs(path)
        return path / f"x{x}y{y}.jpg"
        
    def xy_fromfile(self, path):
        # parses filename string into tile indices
        f = path.name
        xpos = f.index('x')
        ypos = f.index('y')
        dpos = f.index('.')
        sx = f[xpos+1:ypos]
        sy = f[ypos+1:dpos]
        return (int(sx), int(sy))
        
    def tileurl(self, x, y, z):
        # combines tile indices into imagery provider URL
        scale = 1 << z
        if self.flipy:
            y = scale - y - 1
        return self.url.format(z=z, x=x, y=y)
    
    def download(self, x, y, z):
        # returns tile at index (as filename string)
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
    
    def tile_at_wcu(self, x, y, z):
        # takes point in unscaled world cords (0..TILESIZE)
        # returns index of tile which contains the point
        scale = 1 << z
        wc = (x * scale, y * scale)
        # pixel in world
        px = wc[0] + self.offsetx * scale
        py = wc[1] + self.offsety * scale
        # tile in world
        tx = math.floor(px / TILESIZE)
        ty = math.floor(py / TILESIZE)
        # pixel in tile
        rx = px - tx * TILESIZE
        ry = py - ty * TILESIZE
        return tx, ty, rx, ry
    
    def tile_at_wgs(self, latlng, z):
        # takes point in WGS coordinatres
        # returns index of tile which contains the point
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
        # returns tile at location (as filename string)
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
        # takes point in WGS coordinates
        # takes height and width of viewport, px
        # returns a 2d array of tile indices to cover the viewport
        # returns position of point in the viewport, px
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
        # takes point in WGS coordinates
        # takes height and width of viewport, px
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
        # takes point in WGS coordinates
        # takes height and width of viewport, px
        # return image around a location (cropped exactly to h, w)
        image, (cx,cy) = self.gettiles_wgs(latlng, h, w, z)
        print("cropping")
        crop = image[cy-h//2:cy+h//2, cx-w//2:cx+w//2, :]
        return crop

    def tiles_box_wc(self, W, S, E, N, z):
        # takes box corners in unscaled world coordinates (0..TILESIZE)
        # returns a 2d array of tile indices to cover the box
        txmin, tymin, pN, pW = self.tile_at_wcu(W, N, z)
        txmax, tymax, pS, pE = self.tile_at_wcu(E, S, z)
        
        htiles = tymax-tymin+1
        wtiles = txmax-txmin+1
        image = np.zeros((htiles*TILESIZE, wtiles*TILESIZE, 3), dtype=np.uint8)
        
        py = 0
        for ty in range(tymin, tymin+htiles):
            px = 0
            for tx in range(txmin, txmin+wtiles):
                fname = self.download(tx, ty, z)
                img = cv2.imread(fname)
                image[py:py+TILESIZE, px:px+TILESIZE, :] = img
                px += TILESIZE
            py += TILESIZE
        
        xmin = round(pN)
        ymin = round(pW)
        xmax = round(px - TILESIZE + pS)
        ymax = round(py - TILESIZE + pE)
        
#        cv2.line(image, (xmin,ymin), (xmin,ymax), (0,0,255), 1)
#        cv2.line(image, (xmin,ymin), (xmax,ymin), (0,0,255), 1)
#        cv2.imshow('canvas', image)
#        cv2.waitKey(0)
        print("cropping")
        crop = image[ymin:ymax, xmin:xmax, :]
        return crop

    def tiles_way(self, way, z, pad_pct=0.25, pad_px=48):
        # accepts way as list of nodes with WGS coords
        # accepts relative (%) and absolute (px) padding
        # returns 2d array of tiles to cover the whole way plus padding
        wcs = [project2web(p) for p in way]
        xs = [wc[0] for wc in wcs]
        ys = [wc[1] for wc in wcs]

        W = min(xs)
        E = max(xs)
        N = min(ys)
        S = max(ys)

        pad_WE = (E-W) * pad_pct
        pad_NS = (S-N) * pad_pct
        
        scale = 1 << z
        if pad_WE * scale < pad_px:
            pad_WE = pad_px / scale
        if pad_NS * scale < pad_px:
            pad_NS = pad_px / scale
        
        W -= pad_WE; W %= 256
        E += pad_WE; E %= 256
        N -= pad_NS; N %= 256
        S += pad_NS; S %= 256
        
        return self.tiles_box_wc(W, S, E, N, z)

maxar = Imagery("maxar")   
maxar.url = "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@jpg/{z}/{x}/{y}.jpg?connectId=91e57457-aa2d-41ad-a42b-3b63a123f54a"
maxar.flipy = True
maxar.offsetx = -30 / (1 << 19)
maxar.offsety = 10 / (1 << 19)

dg = Imagery("dg")
dg.url = "https://c.tiles.mapbox.com/v4/digitalglobe.316c9a2e/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqZGFrZ2c2dzFlMWgyd2x0ZHdmMDB6NzYifQ.9Pl3XOO82ArX94fHV289Pg"