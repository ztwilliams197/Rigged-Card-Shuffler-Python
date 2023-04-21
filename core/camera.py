from time import sleep
from typing import Callable, Tuple, Final

from picamera import PiCamera
import numpy as np

from identify_card import Image

_CAMERA_RESOLUTION: Final[Tuple[int, int]] = 1024, 1008
_CROP_BOUNDS: Final[Tuple[int, int, int, int]] = 460, 331, 676, 690  # x1, y1, x2, y2


def init_camera() -> Callable[[], Image]:
    camera = PiCamera()
    sleep(2)  # give camera time to boot

    x, y = camera.resolution = _CAMERA_RESOLUTION
    x1, y1, x2, y2 = _CROP_BOUNDS

    output = np.empty((y, x, 3), dtype=np.uint8)

    def _capture_image() -> Image:
        camera.capture(output, 'yuv')
        return output[x1:x2, y1:y2]

    return _capture_image


if __name__ == '__main__':
    print("Usage: <script> <arg1=directory of file>")
    print("Suggested usage: <script> ./ground_truth/deck1")
    print()

    import sys

    _dir = sys.argv[1]
    capture_image = init_camera()

    while True:
        np.save(f"{_dir}/{input('Identity of the current scanned card: ')}.npy", capture_image())
