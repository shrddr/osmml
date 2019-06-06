import cv2
import glob

FRAMESIZE = 256

images = []
i = 0
for fname in glob.glob('./crops/dg/*.jpg'):
    img = cv2.imread(fname)
    
    x = 95
    y = 135
    cv2.line(img, (x,y), (x+10,y+10), (0,0,255), 1)
    cv2.line(img, (x,y), (x-10,y+10), (0,0,255), 1)
    
    images.append(img)
    i += 1
    if i > 10000:
        break
    
out = cv2.VideoWriter('./dg.avi', cv2.VideoWriter_fourcc(*'DIVX'), 60, (FRAMESIZE,FRAMESIZE))
 
for i in range(len(images)):
    out.write(images[i])
out.release()
