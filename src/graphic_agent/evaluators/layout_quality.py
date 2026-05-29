"""Future layout quality helpers."""


def area(box: tuple[int, int, int, int]) -> int:
    left, top, right, bottom = box
    return max(0, right - left) * max(0, bottom - top)
