import numpy as np
import os.path
import cv2
import math
import requests
import io
import time

import loaders
from helpers import mil

TILESIZE = 256
CROPH = 128
CROPW = 128

def project2web(latlng):
    # converts EPSG:4326 (degrees) to EPSG:3857 (metres)
    siny = math.sin(latlng[0] * math.pi / 180);
    siny = min(max(siny, -0.9999), 0.9999);
    x = TILESIZE * (0.5 + latlng[1] / 360)
    y = TILESIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
    return (x, y);

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

def gettiles(session, layer, latlng, h, w, z=19):
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
            x = math.floor(x)
            y = math.floor(y)
            if layer.flipy:
                y = scale - y - 1
            fname = layer.tilecache.format(z=z, x=x, y=y)
            
            if not os.path.isfile(fname):
                url = layer.url.format(z=z, x=x, y=y)
                print("downloading")
                r = session.get(url)
                if r.status_code == 200:
                    with io.open(fname, 'wb') as file:
                        file.write(r.content)
                else:
                    raise IOError(f"{r.status_code} at {url}'")
                
            img = cv2.imread(fname)
            result[ty:ty+TILESIZE, tx:tx+TILESIZE, :] = img
            tx += TILESIZE           
        ty += TILESIZE
        
    return result, center

def getcrop(session, layer, latlng, h, w, z=19):
    # crops an image or returns existing cached crop
    fname = layer.cropcache.format(lat=mil(latlng[0]), lng=mil(latlng[1]), z=z)
    if os.path.isfile(fname):
        crop = cv2.imread(fname)
        return crop
    
    image, (cx,cy) = gettiles(session, layer, latlng, h, w)
        
    print("cropping")
    crop = image[cy-h//2:cy+h//2, cx-w//2:cx+w//2, :]
    cv2.imwrite(fname, crop)
    return crop

class Imagery:
    def __init__(self):
        self.flipy = False
    
if __name__ == "__main__":
    maxar = Imagery()   
    maxar.url = "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@jpg/{z}/{x}/{y}.jpg?connectId=91e57457-aa2d-41ad-a42b-3b63a123f54a"
    maxar.flipy = True
    maxar.tilecache = "./tiles/maxar/x{x}y{y}z{z}.jpg"
    maxar.cropcache = "./crops/maxar/lat{lat}lng{lng}z{z}.jpg"
    
    dg = Imagery()
    dg.url = "https://a.tiles.mapbox.com/v4/digitalglobe.316c9a2e/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqZGFrZ2c2dzFlMWgyd2x0ZHdmMDB6NzYifQ.9Pl3XOO82ArX94fHV289Pg"
    dg.tilecache = "./tiles/dg/x{x}y{y}z{z}.jpg"
    dg.cropcache = "./crops/dg/lat{lat}lng{lng}z{z}.jpg"
    
    lamps = loaders.bbox(27.4583,53.9621,27.5956,53.9739) # north belt
#    lamps = loaders.bbox(27.4026,53.8306,27.7003,53.9739) # whole 10k
    sess = requests.session()
        
    start = time.time()
    for lamp in lamps:
        crop = getcrop(sess, dg, lamp, 256, 256)
    print(time.time() - start)