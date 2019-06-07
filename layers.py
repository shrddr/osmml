import io
import cv2
import math
import os.path
import requests
import numpy as np
from pathlib import Path

TILESIZE = 256

def project2web(latlng):
    # converts EPSG:4326 (degrees) to EPSG:3857 (metres)
    siny = math.sin(latlng[0] * math.pi / 180)
    siny = min(max(siny, -0.9999), 0.9999)
    x = TILESIZE * (0.5 + latlng[1] / 360)
    y = TILESIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
    return (x, y)

def tile_at(latlng, z=19):
    scale = 1 << z
    wc = project2web(latlng)
    tx = math.floor(wc[0] * scale / TILESIZE)
    ty = math.floor(wc[1] * scale / TILESIZE)
    return (tx,ty)

def tiles_near(latlng, scale, h, w):
    # returns a list of tiles to download
    wc = project2web(latlng)
    px = wc[0] * scale
    py = wc[1] * scale
    
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

def gettile(layer, latlng, z=19):
    # returns one tile as cv2 image
    x,y = tile_at(latlng, z)
    img = layer.download(x, y, z)
    return img
    
def gettiles(layer, latlng, h, w, z=19):
    # returns imagery around a location (full tiles, combined)
    scale = 1 << z
    tiles, center = tiles_near(latlng, scale, h, w)
    
    htiles = len(tiles)
    wtiles = len(tiles[0])
    result = np.zeros((htiles*TILESIZE, wtiles*TILESIZE, 3), dtype=np.uint8)
    
    ty = 0
    for row in tiles:
        tx = 0
        for (x,y) in row:
            img = layer.download(x, y, z)
            result[ty:ty+TILESIZE, tx:tx+TILESIZE, :] = img
            tx += TILESIZE           
        ty += TILESIZE
        
    return result, center

class Imagery:
    
    def __init__(self, name, session):
        self.name = name
        self.session = session
        self.flipy = False
        self.offsetx = 0
        self.offsety = 0
        
    def download(self, x, y, z=19):
        scale = 1 << z
        if self.flipy:
            y = scale - y - 1
        fname = self.tilefile.format(z=z, x=x, y=y)
        if not os.path.isfile(fname):
            url = self.url.format(z=z, x=x, y=y)
            print("downloading")
            r = self.session.get(url)
            if r.status_code == 200:
                with io.open(fname, 'wb') as file:
                    file.write(r.content)
            else:
                raise IOError(f"{r.status_code} at {url}'")
        img = cv2.imread(fname)
        return img
        
sess = requests.session()

maxar = Imagery("maxar", sess)   
maxar.url = "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@jpg/{z}/{x}/{y}.jpg?connectId=91e57457-aa2d-41ad-a42b-3b63a123f54a"
maxar.flipy = True
maxar.offsetx = -30
maxar.offsety = 10
maxar.tiledir = Path("tiles/maxar")
maxar.tilefile = "./tiles/maxar/x{x}y{y}z{z}.jpg"
maxar.cropdir = Path("./crops/maxar")
maxar.cropfile = "./crops/maxar/lat{lat}lng{lng}z{z}.jpg"

dg = Imagery("dg", sess)
dg.url = "https://a.tiles.mapbox.com/v4/digitalglobe.316c9a2e/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqZGFrZ2c2dzFlMWgyd2x0ZHdmMDB6NzYifQ.9Pl3XOO82ArX94fHV289Pg"
dg.tiledir = Path("tiles/dg")
dg.tilefile = "./tiles/dg/x{x}y{y}z{z}.jpg"
dg.cropdir = Path("crops/dg")
dg.cropfile = "./crops/dg/lat{lat}lng{lng}z{z}.jpg"