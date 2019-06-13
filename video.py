import cv2
from pathlib import Path
from lib import loaders
from lib import layers

FRAMESIZE = 256

def dir2vid(path):
    images = []
    i = 0
    print(Path(path))
    for fname in Path(path).glob("*.jpg"):
        print(fname)
        img = cv2.imread(str(fname))
        x = 95
        y = 135
        cv2.line(img, (x,y), (x+10,y+10), (0,0,255), 1)
        cv2.line(img, (x,y), (x-10,y+10), (0,0,255), 1)
        
        images.append(img)
        i += 1
        if i > 10000:
            break
        
    out = cv2.VideoWriter(f"./dir.avi", cv2.VideoWriter_fourcc(*'DIVX'), 60, (FRAMESIZE,FRAMESIZE))
     
    for i in range(len(images)):
        out.write(images[i])
    out.release()
    
def list2vid(lamps, layer, z):
    print(1)
    images = []
    for lamp in lamps:
        img = layers.maxar.getcrop_wgs(lamp, FRAMESIZE, FRAMESIZE, z)
        x = 95
        y = 135
        cv2.line(img, (x,y), (x+10,y+10), (0,0,255), 1)
        cv2.line(img, (x,y), (x-10,y+10), (0,0,255), 1)
        
        images.append(img)
    print("video out") 
    out = cv2.VideoWriter(f"./list-{layer.name}.avi", cv2.VideoWriter_fourcc(*'DIVX'), 60, (FRAMESIZE,FRAMESIZE))
     
    for i in range(len(images)):
        out.write(images[i])
    out.release()

if __name__ == "__main__":
#    dir2vid(layers.maxar, 19)
    dir2vid("lamps-expand/train/lamp")
#    lamps = loaders.query_nodes(27.4026,53.8306,27.7003,53.9739)
#    list2vid(lamps, layers.maxar, 19)
#    list2vid(lamps, layers.dg, 19)