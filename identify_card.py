from typing import Tuple, List
import numpy as np
import scipy.ndimage as img_filter
import cv2


# noinspection PyShadowingNames
def _load_image(path, scale=None):
    img = cv2.imread(path)
    if scale is not None:
        img = cv2.resize(img, scale)
    # returns [y, u, v] -- indexed in 3rd dimension [:,:, ??]
    return cv2.cvtColor(img, cv2.COLOR_BGR2YUV)


# noinspection PyShadowingNames
def _increase_contrast(img: np.ndarray, *, threshold=0.5):
    img = np.copy(img)
    img[img < threshold * 255] = 0
    img[img >= threshold * 255] = 255
    return img


# noinspection PyShadowingNames
def _get_edges(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x1 = img_filter.sobel(img, axis=0)
    x2 = img_filter.sobel(-img, axis=0)
    y1 = img_filter.sobel(img, axis=1)
    y2 = img_filter.sobel(-img, axis=1)
    return x1, x2, y1, y2


# noinspection PyShadowingNames
def _filter_edges(img: np.ndarray) -> np.ndarray:
    x1, x2, y1, y2 = _get_edges(img)
    out = np.copy(img) * 0
    out[np.logical_or(np.logical_or(x1 > 0, x2 > 0), np.logical_or(y1 > 0, y2 > 0))] = 255
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
        # noinspection PyUnresolvedReferences
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


# noinspection PyShadowingNames
def preprocess_image(img: np.ndarray) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]]]:
    # img arg is dimensions h x w x 3 -- yuv for last dimension
    y = img[:, :, 0]
    y_contr = _increase_contrast(y, threshold=0.7)
    edges = _filter_edges(y_contr)

    return edges, _get_bounding_boxes(edges)


# noinspection PyShadowingNames
def _add_bounding_boxes_to_image(img: np.ndarray, bboxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
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


if __name__ == '__main__':
    img = _load_image('cards2.png')
    img, bboxes = preprocess_image(img)
    img = _add_bounding_boxes_to_image(img, bboxes)
    cv2.imwrite('bounding_boxes.png', img)
