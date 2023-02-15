from typing import List, Tuple, Dict
from math import ceil, floor


# noinspection PyShadowingNames
def compute_step_list(num_bins: int, num_whole_steps: int, substep_count: int) \
        -> Dict[str, Tuple[List[int], List[float]]]:
    steps_per_bin: float = num_whole_steps * substep_count / num_bins
    ranges: List[Tuple[int, int]] = [(ceil(i * steps_per_bin), floor((i + 1) * steps_per_bin)) for i in range(num_bins)]

    def _closest_mult_to_mid(low: int, high: int, mult: int) -> int:
        mid: float = (low + high) / 2
        c2: int = int(mid // mult) * mult
        c1, c3 = c2 - mult, c2 + mult
        d1, d2, d3 = abs(mid - c1), abs(mid - c2), abs(mid - c3)
        if d1 <= min(d2, d3):
            return c1
        if d2 <= min(d1, d3):
            return c2
        return c3

    ret = {}
    num_bundled_substeps = substep_count
    degrees_per_smallest_step: float = 360 / num_whole_steps / substep_count
    while num_bundled_substeps >= 1:
        key_float = degrees_per_smallest_step * num_bundled_substeps
        key_int = int(key_float)
        key_rem = f"{round(1e5 * (key_float - key_int))}"
        key = f"{key_int}.{key_rem.zfill(5)}"
        step_list = [
            _closest_mult_to_mid(low, high, num_bundled_substeps) // num_bundled_substeps
            for low, high in ranges
        ]
        errors = []
        for step_ind, bin_range in zip(step_list, ranges):
            low, high = bin_range
            errors.append(degrees_per_smallest_step * abs((low + high) / 2 - num_bundled_substeps * step_ind))
        ret[key] = ([v - step_list[0] for v in step_list], errors)
        num_bundled_substeps = num_bundled_substeps // 2
    return ret


if __name__ == '__main__':
    step_lists = compute_step_list(52, 200, 32)
    for key in step_lists.keys():
        step_list, errors = step_lists[key]
        print(f"Step list for step size of {key} degrees:")
        print(step_list)
        print(f"Bin-wise errors (in degrees): {errors}")
        print(f"Accumulated error [= sum(errors)]: {sum(errors)}")
        print(f"Maximum error [= max(errors)]: {max(errors)}")
        print()
