import time
import picamera
import picamera.array
import numpy as np

def takePic():
    with picamera.PiCamera() as camera:
        x , y = 1024, 1008
        camera.resolution=(x, y)
        #camera.framerate = 24

        time.sleep(2)

        output = np.empty((camera.resolution[1], camera.resolution[0], 3), dtype=np.uint8)    
        camera.capture(output, 'yuv')

        return output
