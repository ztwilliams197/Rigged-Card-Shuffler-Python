from __future__ import annotations

from typing import Tuple, List, Callable, TypeVar, Generic, Optional
import numpy as np
import scipy.ndimage as img_filter

N = TypeVar('N', int, float)
Image = np.ndarray


class BoundingBox(Generic[N], Tuple[N, N, N, N]):
    @staticmethod
    def of(x1: N, y1: N, x2: N, y2: N) -> BoundingBox[N]:
        assert x1 <= x2 and y1 <= y2, "Invalid b-box coordinates"
        return BoundingBox((x1, y1, x2, y2))

    @staticmethod
    def hull(bboxes: List[BoundingBox[N]]) -> Optional[BoundingBox[N]]:
        if len(bboxes) == 0:
            return None
        x1, y1, x2, y2 = bboxes[0]
        for a1, b1, a2, b2 in bboxes:
            x1 = min(x1, a1)
            y1 = min(y1, b1)
            x2 = max(x2, a2)
            y2 = max(y2, b2)
        return BoundingBox.of(x1, y1, x2, y2)


def _increase_contrast(img: Image, *, threshold=0.5):
    img = np.copy(img)
    img[img < threshold * 255] = 0
    img[img >= threshold * 255] = 255
    return img


def _denoise_image(img: Image) -> Image:
    # img arg is dimensions h x w x 3 -- yuv for last dimension
    y = img[:, :, 0]
    return _increase_contrast(y, threshold=0.7)


def _get_edges(img: Image) -> Tuple[Image, Image, Image, Image]:
    x1 = img_filter.sobel(img, axis=0)
    x2 = img_filter.sobel(-img, axis=0)
    y1 = img_filter.sobel(img, axis=1)
    y2 = img_filter.sobel(-img, axis=1)
    return x1, x2, y1, y2


def _filter_edges(img: Image) -> Image:
    x1, x2, y1, y2 = _get_edges(img)
    out = np.copy(img) * 0
    out[np.logical_or(np.logical_or(x1 > 0, x2 > 0), np.logical_or(y1 > 0, y2 > 0))] = 255
    return out


def _get_bounding_boxes(img: Image) -> List[BoundingBox[int]]:
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

    # # exclude boxes inside other boxes
    # ret = []
    # for x1, y1, x2, y2 in temp_ret:
    #     keep = True
    #     for _x1, _y1, _x2, _y2 in temp_ret:
    #         if x1 == _x1 and y1 == _y1 and x2 == _x2 and y2 == _y2:
    #             continue
    #         if _x1 <= x1 <= x2 <= _x2 and _y1 <= y1 <= y2 <= _y2:
    #             keep = False
    #             break
    #     if keep:
    #         ret.append(BoundingBox.of(x1, y1, x2, y2))
    # return ret
    return [BoundingBox.of(x1, y1, x2, y2) for x1, y1, x2, y2 in temp_ret]


def preprocess_image(img: Image) -> Tuple[Image, List[BoundingBox[int]]]:
    edges = _filter_edges(_denoise_image(img))
    return edges, _get_bounding_boxes(edges)


Card = Tuple[str, str]  # rank, suit
CoordinateMapperFunc = Callable[[float, float], Tuple[float, float]]
ImageComparisonData = Tuple[Image, List[BoundingBox[float]], CoordinateMapperFunc]


def _normalize_bboxes(bboxes: List[BoundingBox[int]]) -> Tuple[List[BoundingBox[float]], CoordinateMapperFunc]:
    bbox_hull = BoundingBox.hull(bboxes)
    if bbox_hull is None:
        return [], lambda x, y: (x, y)

    x1, y1, x2, y2 = bbox_hull
    return [
               BoundingBox.of(
                   (a1 - x1) / (x2 - x1),
                   (b1 - y1) / (y2 - y1),
                   (a2 - x1) / (x2 - x1),
                   (b2 - y1) / (y2 - y1),
               )
               for a1, b1, a2, b2 in bboxes
           ], lambda x, y: ((x2 - x1) * x + x1, (y2 - y1) * y + y1)


def identify_card(edges: Image, bboxes: List[BoundingBox[int]]) -> Card:
    pass
