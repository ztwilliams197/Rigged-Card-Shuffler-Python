from __future__ import annotations

from typing import Tuple, List, Callable, TypeVar, Generic, Optional, Dict, Final
import numpy as np
import scipy.ndimage as img_filter
from scipy.interpolate import RegularGridInterpolator
from math import sqrt

N = TypeVar('N', int, float)
Image = np.ndarray

_ImgDispFunc = Callable[[Image, str], None]


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

    @property
    def area(self) -> N:
        x1, y1, x2, y2 = self
        return abs(x2 - x1) * abs(y2 - y1)

    @property
    def center(self) -> Tuple[float, float]:
        x1, y1, x2, y2 = self
        return (x1 + x2) / 2, (y1 + y2) / 2

    @staticmethod
    def distance_squared(bbox1: BoundingBox[N], bbox2: BoundingBox[N]) -> float:
        cx1, cy1 = bbox1.center
        cx2, cy2 = bbox2.center
        return (cx1 - cx2) ** 2 + (cy1 - cy2) ** 2

    @staticmethod
    def distance(bbox1: BoundingBox[N], bbox2: BoundingBox[N]) -> float:
        return sqrt(BoundingBox.distance_squared(bbox1, bbox2))


def _increase_contrast(img: Image, threshold: float):
    img = img.copy()
    img[img < threshold * 255] = 0
    img[img >= threshold * 255] = 255
    return img


def _denoise_image(img: Image) -> Image:
    # img arg is dimensions h x w x 3 -- yuv for last dimension
    y = img[:, :, 0]
    v = img[:, :, 2]  # red component
    y = y - _increase_contrast(v, threshold=0.70)  # drop pixel values to black for red pixels
    return _increase_contrast(y, threshold=0.40)


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

    return [BoundingBox.of(x1, y1, x2, y2) for x1, y1, x2, y2 in temp_ret]


def preprocess_image(img: Image, *, verbose: bool = False) -> Tuple[Image, List[BoundingBox[int]]]:
    if verbose:
        print("Denoising image with threshold filter...")
    denoised = _denoise_image(img)
    if verbose:
        print("Filtering edges with Sobel operator...")
    edges = _filter_edges(denoised)
    if verbose:
        print("Extracting bounding boxes...")
    return edges, _get_bounding_boxes(edges)


Card = Tuple[str, str]  # rank, suit
CoordinateMapperFunc = Callable[[float, float], Tuple[float, float]]
ImageComparisonData = Tuple[Image, List[BoundingBox[float]], CoordinateMapperFunc]

_GROUND_TRUTH_IMAGES: Final[Tuple[List[Card], List[ImageComparisonData]]] = [], []


def _normalize_bboxes(bboxes: List[BoundingBox[int]], *, verbose: bool = False) \
        -> Tuple[List[BoundingBox[float]], CoordinateMapperFunc]:
    if verbose:
        print("Removing small noise bboxes & hull bbox")

    bboxes = [bbox for bbox in bboxes if bbox.area >= 400]  # TODO generalize min_bbox_area = 400
    bbox_hull = BoundingBox.hull(bboxes)
    if bbox_hull is None:
        return [], lambda x, y: (x, y)

    bboxes = [bbox for bbox in bboxes if bbox.area < bbox_hull.area * 0.95]  # filter out hull bbox

    if verbose:
        print("Scaling bboxes to unit hull bbox...")

    x1, y1, x2, y2 = bbox_hull
    mx, dx, my, dy = x2 - x1, x1, y2 - y1, y1
    bboxes: List[BoundingBox[float]] = [
        BoundingBox.of(
            (a1 - dx) / mx,
            (b1 - dy) / my,
            (a2 - dx) / mx,
            (b2 - dy) / my,
        )
        for a1, b1, a2, b2 in bboxes
    ]
    return sorted(bboxes, key=lambda bbox: bbox.area), lambda x, y: (mx * x + dx, my * y + dy)


def populate_ground_truth(images: Dict[Card, List[Image]], *, verbose: bool = False) -> None:
    cards, img_data_list = _GROUND_TRUTH_IMAGES
    cards.clear()
    img_data_list.clear()

    if verbose:
        print("---------------------------------")
    for card, images in images.items():
        if verbose:
            print(f"Beginning processing for card={card}")

        for img in images:
            # process image
            edges, bboxes = preprocess_image(img, verbose=verbose)
            bbox_norm, mapper = _normalize_bboxes(bboxes, verbose=verbose)
            img_data: ImageComparisonData = edges, bbox_norm, mapper
            # save data
            cards.append(card)
            img_data_list.append(img_data)

            if verbose:
                print(f"Num bboxes for card={card} == {len(bbox_norm)}")
            print("---------------------------------")


def _sample_img_at_bbox(img: Image, bbox: BoundingBox[float], mapper: CoordinateMapperFunc, *, n_samples: int) -> Image:
    h, w = img.shape
    interp = RegularGridInterpolator((np.arange(h), np.arange(w)), img)

    nsc = n_samples * 1j
    x1, y1, x2, y2 = bbox
    x1, y1 = mapper(x1, y1)
    x2, y2 = mapper(x2, y2)
    xy_samples = np.mgrid[x1:x2:nsc, y1:y2:nsc].reshape(2, -1).T

    return interp(xy_samples) / 255


def _compare_images(test_img: ImageComparisonData, truth_img: ImageComparisonData, *, verbose: bool = False) -> float:
    e1, bb1, m1 = test_img
    e2, bb2, m2 = truth_img

    bb2r = list(reversed(bb2))
    n_samples = 100
    n_samples_2 = n_samples ** 2

    running_score = 0
    if verbose:
        print("------------------------")
    for bbox1 in bb1:
        if verbose:
            print(f"Processing bbox {bbox1} with center {bbox1.center} and area {bbox1.area}")
        score_inc = 0
        found_match = False
        for bbox2 in bb2r:
            if bbox2.area > bbox1.area + 0.01:
                continue
            if bbox2.area < bbox1.area - 0.01:
                break
            if BoundingBox.distance_squared(bbox1, bbox2) > 0.005:
                continue
            found_match = True
            if verbose:
                print(f"match bbox = {bbox2} with center {bbox2.center} and area {bbox2.area}")
            s1 = _sample_img_at_bbox(e1, bbox1, m1, n_samples=n_samples)
            s2 = _sample_img_at_bbox(e2, bbox2, m2, n_samples=n_samples)
            score_inc = max(score_inc, n_samples_2 - np.abs(s1 - s2).sum())
        if verbose:
            print(f"Match score = {score_inc} and found_match = {found_match}")
        running_score += bbox1.area * (score_inc if found_match else -n_samples_2)
        if verbose:
            print("------------------------")
    return running_score


def identify_card(edges: Image, bboxes: List[BoundingBox[int]], *, verbose: bool = False) \
        -> Tuple[Card, Dict[Card, float]]:
    if verbose:
        print("Normalizing bounding boxes for fast comparison/matching...")
    bbox_norm, mapper = _normalize_bboxes(bboxes, verbose=verbose)
    img_data: ImageComparisonData = edges, bbox_norm, mapper

    truth_labels, truth_imgs = _GROUND_TRUTH_IMAGES
    truth_size = len(truth_labels)

    scores: List[float] = list(map(lambda gti: _compare_images(img_data, gti, verbose=verbose), truth_imgs))

    best_ind = max(range(truth_size), key=lambda i: scores[i])
    best_card: Card = truth_labels[best_ind]
    if verbose:
        print("Identified best card identity match...")

    score_map: Dict[Card, float] = {}
    for card, score in zip(truth_labels, scores):
        if card not in score_map or score_map[card] < score:
            score_map[card] = score

    if verbose:
        print("Built overall score map... returning identity...")
    return best_card, score_map
