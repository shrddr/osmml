import numpy as np
import os.path
import cv2
import math
import requests
import io
import time

import loaders

TILESIZE = 256
HALFSIZE = TILESIZE//2
URL1 = "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@jpg/{z}/{x}/{y}.jpg?connectId=91e57457-aa2d-41ad-a42b-3b63a123f54a"
URL2 = "https://a.tiles.mapbox.com/v4/digitalglobe.316c9a2e/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqZGFrZ2c2dzFlMWgyd2x0ZHdmMDB6NzYifQ.9Pl3XOO82ArX94fHV289Pg"
TILEFILE = "./tiles/x{x}y{y}z{z}.jpg"
OUTFILE = "./out/lat{lat}lng{lng}z{z}.jpg"

def project2web(latlng):
    # converts EPSG:4326 (degrees) to EPSG:3857 (metres)
    siny = math.sin(latlng[0] * math.pi / 180);
    siny = min(max(siny, -0.9999), 0.9999);
    x = TILESIZE * (0.5 + latlng[1] / 360)
    y = TILESIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
    return (x, y);

def tiles_near(latlng, scale):
    # returns a list of 4 tiles to download
    wc = project2web(latlng)
    
    # pixel coords
    px = wc[0] * scale
    py = wc[1] * scale
    
    # tile coords
    tx = px / TILESIZE
    ty = py / TILESIZE
    
    tiles = [[(tx-0.5, ty-0.5), (tx+0.5, ty-0.5)],
             [(tx-0.5, ty+0.5), (tx+0.5, ty+0.5)]]

    return tiles, (px,py)

def gettiles(session, latlng, z=19, flip=True):
    # returns tiles around a location
    scale = 1 << z
    tiles, center = tiles_near(latlng, scale)

    images = []
    for row in tiles:
        imagerow = []
        for (x,y) in row:
            x = math.floor(x)
            y = math.floor(y)
            if flip:
                y = scale - y - 1
            fname = TILEFILE.format(z=z, x=x, y=y)
            if os.path.isfile(fname):
                img = cv2.imread(fname)
                imagerow.append(img)
                continue
            
            url = URL1.format(z=z, x=x, y=y)
            print("downloading")
            r = session.get(url)
            if r.status_code == 200:
                with io.open(fname, 'wb') as file:
                    file.write(r.content)
                img = cv2.imread(fname)
                imagerow.append(img)
            else:
                raise Exception(f"{r.status_code} at {url}'")
                
        images.append(imagerow)
    
    ilat = math.floor(latlng[0]*1000000)
    ilng = math.floor(latlng[1]*1000000)
    fname = OUTFILE.format(lat=ilat, lng=ilng, z=z)
    if os.path.isfile(fname):
        crop = cv2.imread(fname)
        return crop
        
    print("cropping")
    result = np.zeros((TILESIZE*2, TILESIZE*2, 3), dtype=np.uint8)
    y = 0
    for row in images:
        x = 0
        for img in row:
            result[y:y+TILESIZE, x:x+TILESIZE, :] = img
            x += TILESIZE
        y += TILESIZE
    
    px_min = math.floor(tiles[0][0][0]) * TILESIZE
    py_min = math.floor(tiles[0][0][1]) * TILESIZE
    cx = round(center[0]-px_min)
    cy = round(center[1]-py_min)

    crop = result[cy-128:cy+128, cx-128:cx+128, :]
    cv2.imwrite(fname, crop)
    return crop

if __name__ == "__main__":
    lamps = loaders.readjson('in4.json')
#    lamps = loaders.bbox(27.4583,53.9621,27.5956,53.9739)
    sess = requests.session()
    
    start = time.time()
    for lamp in lamps:
        crop = gettiles(sess, lamp)
    print(time.time() - start)