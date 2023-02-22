import sys

import cv2
from time import perf_counter

from identify_card import *


# noinspection PyShadowingNames,PyUnresolvedReferences
def _load_image(path, scale=None) -> Image:
    img = cv2.imread(path)
    if scale is not None:
        img = cv2.resize(img, scale)
    # returns [y, u, v] -- indexed in 3rd dimension [:,:, ??]
    return cv2.cvtColor(img, cv2.COLOR_BGR2YUV)


# noinspection PyShadowingNames,PyUnresolvedReferences
def _add_bounding_boxes_to_image(img: Image, bboxes: List[BoundingBox[int]]) -> Image:
    r, g, b = np.copy(img), np.copy(img), np.copy(img)

    def _bound(b1, b2):
        low = min(b1, b2)
        high = max(b1, b2)
        return range(low, high + 1)

    def _set_red(_r, _g, _b, _x, _y):
        _r[_x, _y] = 255
        _g[_x, _y] = 0
        _b[_x, _y] = 0

    for x1, y1, x2, y2 in bboxes:
        for x in _bound(x1, x2):
            _set_red(r, g, b, x, y1)
            _set_red(r, g, b, x, y2)
        for y in _bound(y1, y2):
            _set_red(r, g, b, x1, y)
            _set_red(r, g, b, x2, y)

    return cv2.merge((b, g, r))


# noinspection PyCompatibility,PyShadowingNames
def _run_test(img, path_out):
    print("starting preprocessing")
    start = perf_counter()
    img, bboxes = preprocess_image(img)
    end = perf_counter()
    print(f"preprocessing complete: time taken = {end - start} seconds")
    img = _add_bounding_boxes_to_image(img, bboxes)
    print(f"outputting image with bounding boxes drawn (to file {path_out})")
    # noinspection PyUnresolvedReferences
    cv2.imwrite(path_out, img)


# noinspection PyCompatibility,PyShadowingNames
def run_test_on_path(path_in, path_out):
    print(f"loading image from path {path_in}")
    _run_test(_load_image(path_in), path_out)


# noinspection PyShadowingNames
def run_test_on_yuv(yuv_in, path_out):
    _run_test(yuv_in, path_out)


if __name__ == '__main__':
    path_in = sys.argv[1] if len(sys.argv) > 1 else 'cards3.png'
    path_out = sys.argv[2] if len(sys.argv) > 2 else 'bounding_boxes.png'
    run_test_on_path(path_in, path_out)
