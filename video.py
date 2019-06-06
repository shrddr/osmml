import cv2
import loaders
import glob
import imgdl
import layers

FRAMESIZE = 256

def dir2vid(layer):
    images = []
    i = 0
    for fname in layer.cropdir.glob("*.jpg"):
        img = cv2.imread(str(fname))

        x = 95
        y = 135
        cv2.line(img, (x,y), (x+10,y+10), (0,0,255), 1)
        cv2.line(img, (x,y), (x-10,y+10), (0,0,255), 1)
        
        images.append(img)
        i += 1
        if i > 10000:
            break
        
    out = cv2.VideoWriter(f"./all-{layer.name}.avi", cv2.VideoWriter_fourcc(*'DIVX'), 60, (FRAMESIZE,FRAMESIZE))
     
    for i in range(len(images)):
        out.write(images[i])
    out.release()
    
def list2vid(lamps, layer):
    print(1)
    images = []
    for lamp in lamps:
        print("getting crop")
        img = imgdl.getcrop(None, layer, lamp, FRAMESIZE, FRAMESIZE)
        print("painting")
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
#    dir2vid(layers.maxar)
#    dir2vid(layers.dg)
    lamps = loaders.bbox(27.5682,53.8469,27.5741,53.8688)
    list2vid(lamps, layers.maxar)
    list2vid(lamps, layers.dg)