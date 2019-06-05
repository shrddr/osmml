import numpy as np
import os.path
import cv2
import math
import requests

TILE_SIZE = 256
URL1 = "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@jpg/{z}/{x}/{y}.jpg?connectId=91e57457-aa2d-41ad-a42b-3b63a123f54a"
URL2 = "https://a.tiles.mapbox.com/v4/digitalglobe.316c9a2e/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqZGFrZ2c2dzFlMWgyd2x0ZHdmMDB6NzYifQ.9Pl3XOO82ArX94fHV289Pg"
OUT = "./x{x}y{y}z{z}.jpg"

def project2web(latlng):
    # converts EPSG:4326 (degrees) to EPSG:3857 (metres)
    siny = math.sin(latlng[0] * math.pi / 180);
    siny = min(max(siny, -0.9999), 0.9999);
    x = TILE_SIZE * (0.5 + latlng[1] / 360)
    y = TILE_SIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
    return (x, y);

def whichtile(latlng, scale):
    # returns a list of 4 tiles to download
    wc = project2web(latlng)
       
    tx = wc[0] * scale / TILE_SIZE
    ty = wc[1] * scale / TILE_SIZE
    
    tiles = [(tx-0.5, ty-0.5), (tx+0.5, ty-0.5),
             (tx-0.5, ty+0.5), (tx+0.5, ty+0.5)]

    return tiles

def gettiles(latlng, z=19, flip=True):
    
    
    # downloads tiles around a location, with caching
    scale = 1 << z
    tiles = whichtile(latlng, scale)

    sess = requests.session()
    
    files = []
    
    for (x,y) in tiles:
        x = math.floor(x)
        y = math.floor(y)
        if flip:
            y = scale - y - 1
        fname = OUT.format(z=z, x=x, y=y)
        if os.path.isfile(fname):
            files.append(fname)
            continue
        
        url = URL1.format(z=z, x=x, y=y)
        r = sess.get(url)
        if r.status_code == 200:
            with open(fname, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            files.append(fname)
        else:
            print(r.status_code, url)
    
    return files

files = gettiles((53.9264460, 27.5934246))

result = np.array((TILE_SIZE*2, TILE_SIZE*2, 3))
for file in files:
    img = cv2.imread(file, cv2.IMREAD_COLOR)

    cv2.imshow('image',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
