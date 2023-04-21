from time import sleep
from typing import Callable, Tuple, Final

from picamera import PiCamera
import numpy as np

from identify_card import Image

_CAMERA_RESOLUTION: Final[Tuple[int, int]] = 1024, 1008


def init_camera() -> Callable[[], Image]:
    camera = PiCamera()
    sleep(2)  # give camera time to boot

    x, y = camera.resolution = _CAMERA_RESOLUTION

    output = np.empty((y, x, 3), dtype=np.uint8)

    def _capture_image() -> Image:
        camera.capture(output, 'yuv')
        return output

    return _capture_image
