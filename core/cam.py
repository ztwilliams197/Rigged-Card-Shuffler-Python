import time
import picamera
import picamera.array
import numpy as np

def initCamera():
    camera = picamera.PiCamera()
    time.sleep(2) # give jawn time to boot
    return camera

def getPic(camera):
    x,y = 1024,1008
    camera.resolution = (x,y)

    output = np.empty((camera.resolution[1], camera.resolution[0], 3), dtype=np.uint8)
    camera.capture(output, 'yuv')

    return output