import numpy as np
import os.path
import cv2
import math
import requests

TILESIZE = 256
HALFSIZE = TILESIZE//2
URL1 = "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@jpg/{z}/{x}/{y}.jpg?connectId=91e57457-aa2d-41ad-a42b-3b63a123f54a"
URL2 = "https://a.tiles.mapbox.com/v4/digitalglobe.316c9a2e/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqZGFrZ2c2dzFlMWgyd2x0ZHdmMDB6NzYifQ.9Pl3XOO82ArX94fHV289Pg"
CACHEFILE = "./x{x}y{y}z{z}.jpg"
OUTFILE = "./lat{lat}lng{lng}z{z}.jpg"

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

def gettiles(latlng, z=19, flip=True):
    # returns tiles around a location
    scale = 1 << z
    tiles, center = tiles_near(latlng, scale)

    sess = requests.session()
    
    images = []
    for row in tiles:
        imagerow = []
        for (x,y) in row:
            x = math.floor(x)
            y = math.floor(y)
            if flip:
                y = scale - y - 1
            fname = CACHEFILE.format(z=z, x=x, y=y)
            if os.path.isfile(fname):
                img = cv2.imread(fname)
                imagerow.append(img)
                continue
            
            url = URL1.format(z=z, x=x, y=y)
            r = sess.get(url)
            if r.status_code == 200:
                with open(fname, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
                img = cv2.imread(fname)
                imagerow.append(img)
            else:
                raise Exception(f"{r.status_code} at {url}'")
                
        images.append(imagerow)
    

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
    cv2.imwrite(OUTFILE.format(lat=latlng[0], lng=latlng[1], z=z), crop)
    return crop

if __name__ == "__main__":
    lamps = [(53.9171254, 27.4128943),
             (53.9227905, 27.4159448),
             (53.9279740, 27.4195899)]
    for lamp in lamps:
        img = gettiles(lamp)
        cv2.imshow('image', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()