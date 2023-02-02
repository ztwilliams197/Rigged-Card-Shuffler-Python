# from io import BytesIO
# from time import sleep
# from picamera2.picamera2 import Picamera2
from typing import Tuple, List, Set

import numpy as np
import skimage.measure
import scipy.ndimage as img_filter


def _bruteforce_match(img1: np.ndarray, img2: np.ndarray):
    diff = np.abs(img1 - img2)
    return diff, np.sum(diff * diff, axis=(0, 1))


def _increase_contrast(img: np.ndarray, *, threshold=0.5):
    img = np.copy(img)
    img[img < threshold * 255] = 0
    img[img >= threshold * 255] = 255
    return img


def _align_image(img: np.ndarray, *, height, width):
    min_x, max_x, min_y, max_y = 0, len(img) - 1, 0, len(img[0]) - 1
    while np.count_nonzero(img[min_x][:]) == 0:
        min_x += 1
    while np.count_nonzero(img[max_x][:]) == 0:
        max_x -= 1
    while np.count_nonzero(img[:][min_y]) == 0:
        min_y += 1
    while np.count_nonzero(img[:][max_y]) == 0:
        max_y -= 1
    # TODO rescale to height x width ??
    return img[min_x:max_x][min_y:max_y]


def _get_keypoints(img: np.ndarray):
    # generate octaves
    octaves = [img]
    for _ in range(4):
        octaves.append(skimage.measure.block_reduce(octaves[-1], (2, 2), np.max))  # max pooling to generate octaves
    # extend octaves with gaussian blurs
    img_table = []
    for octave_img in octaves:
        blurred = [octave_img]
        for sig in range(5):
            blurred.append(img_filter.gaussian_filter(octave_img, sigma=sig))
        img_table.append(blurred)
    # TODO compute differences of gaussian blurs for all octaves
    # TODO identify keypoints as local extrema
    # NTS probably don't need to eliminate keypoints since we want edge points


# noinspection PyShadowingNames
def _get_edges(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x1 = img_filter.sobel(img, axis=0)
    x2 = img_filter.sobel(-img, axis=0)
    y1 = img_filter.sobel(img, axis=1)
    y2 = img_filter.sobel(-img, axis=1)
    return x1, x2, y1, y2


# noinspection PyShadowingNames
def _filter_edges(img: np.ndarray, *, threshold=0.9) -> np.ndarray:
    x1, x2, y1, y2 = _get_edges(img)
    cutoff = threshold * 255
    out = np.copy(img) * 0
    out[np.logical_or(np.logical_or(x1 >= cutoff, x2 >= cutoff), np.logical_or(y1 >= cutoff, y2 >= cutoff))] = 255
    return out


# noinspection PyShadowingNames
def _get_bounding_boxes(img: np.ndarray) -> List[Tuple[int, int, int, int]]:
    # pre-req: input is full black/white contrast
    img = img > 127
    coords = np.where(img)
    coords = [(x, y) for x, y in zip(coords[0], coords[1])]
    temp_ret = []

    parents, sizes = {}, {}
    for coord in coords:
        parents[coord] = coord
        sizes[coord] = 1

    def _get_parent(c):
        if parents[c] != c:
            parents[c] = _get_parent(parents[c])
        return parents[c]

    for coord in coords:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            x, y = coord
            x += dx
            y += dy
            if 0 <= x < len(img) and 0 <= y < len(img[x]) and img[x, y]:
                p1 = _get_parent(coord)
                p2 = _get_parent((x, y))
                if p1 != p2:
                    if sizes[p1] < sizes[p2]:
                        p1, p2 = p2, p1
                    parents[p2] = p1
                    sizes[p1] += sizes[p2]

    groups = {}
    for coord in coords:
        parent = _get_parent(coord)
        if parent not in groups:
            groups[parent] = []
        groups[parent].append(coord)

    for group in groups.values():
        cx = [x for x, _ in group]
        cy = [y for _, y in group]
        temp_ret.append((int(min(cx)), int(min(cy)), int(max(cx)), int(max(cy))))

    ret = []
    for x1, y1, x2, y2 in temp_ret:
        keep = True
        for _x1, _y1, _x2, _y2 in temp_ret:
            if x1 == _x1 and y1 == _y1 and x2 == _x2 and y2 == _y2:
                continue
            if _x1 <= x1 <= x2 <= _x2 and _y1 <= y1 <= y2 <= _y2:
                keep = False
                break
        if keep:
            ret.append((x1, y1, x2, y2))
    return ret


if __name__ == '__main__':
    # img_width, img_height = 1920, 1440
    # key_width, key_height = 0, 0  # height/width of top corner of card (with card rank/suit)
    #
    # cam = Picamera2()  # TODO configure camera for YUV mode
    # cam.start()
    # sleep(1)
    # image = cam.capture_array()[:key_width, :key_height:, :3]  # extract 'top' nxm pixels of image

    import cv2


    def _load_image(path, scale=None):
        img = cv2.imread(path)
        if scale is not None:
            img = cv2.resize(img, scale)
        # returns y, u, v
        return cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2YUV))


    # y, u, v = _load_image('cards.jpeg')
    y, u, v = _load_image('cards2.png')
    # y, u, v = _load_image('/Users/up/Desktop/steins;gate.png')
    img = _increase_contrast(y, threshold=0.7)
    cv2.imshow('img', img)
    cv2.waitKey(0)
    # x1, x2, y1, y2 = _get_edges(y)
    # x1 = _increase_contrast(x1, threshold=0.9)
    # x2 = _increase_contrast(x2, threshold=0.9)
    # y1 = _increase_contrast(y1, threshold=0.9)
    # y2 = _increase_contrast(y2, threshold=0.9)
    # img = np.copy(y) * 0
    # img[np.logical_or(np.logical_or(x1 > 127, x2 > 127), np.logical_or(y1 > 127, y2 > 127))] = 255
    img = _filter_edges(img, threshold=0.9)
    cv2.imshow('img', img)
    cv2.waitKey(0)
    r, g, b = np.copy(img), np.copy(img), np.copy(img)


    def _bound(b1, b2):
        low = min(b1, b2)
        high = max(b1, b2)
        return range(low, high + 1)


    def _set_red(_r, _g, _b, _x, _y):
        _r[_x, _y] = 255
        _g[_x, _y] = 0
        _b[_x, _y] = 0


    for x1, y1, x2, y2 in _get_bounding_boxes(img):
        # print(f"({x1}, {y1}) to ({x2}, {y2})")
        for x in _bound(x1, x2):
            _set_red(r, g, b, x, y1)
            _set_red(r, g, b, x, y2)
        for y in _bound(y1, y2):
            _set_red(r, g, b, x1, y)
            _set_red(r, g, b, x2, y)

    img = cv2.merge((b, g, r))
    cv2.imwrite('bounding_boxes.png', img)
    # cv2.imshow('img', img)
    # cv2.waitKey(0)

    # pic1 = _load_image('/Users/up/Desktop/abe_lincoln.jpeg', scale=(640, 800))[0]
    # pic2 = _load_image('/Users/up/Desktop/PRIYAM_UTKARSH.jpeg', scale=(640, 800))[0]
    #
    # # cv2.imshow('pic1', pic1)
    # # cv2.imshow('pic2', pic2)
    # # cv2.waitKey(0)
    #
    # p1c = _increase_contrast(pic1)
    # p2c = _increase_contrast(pic2)
    #
    # cv2.imshow('pic1', p1c)
    # cv2.imshow('pic2', 255 - p2c)
    # # cv2.waitKey(0)
    #
    # diff, score = _bruteforce_match(p1c, 255 - p2c)
    # cv2.imshow(f"Score: {score}", diff)
    # cv2.waitKey(0)
