from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step

MIN_RUN = 32


def _insertion_sort_section(a: list[int], start: int, end: int) -> Iterator[Step]:
    for i in range(start + 1, end):
        key = a[i]
        yield Step("key", (i,), key)
        j = i - 1
        while j >= start:
            yield Step("compare", (j, j + 1))
            if a[j] <= key:
                break
            a[j + 1] = a[j]
            yield Step("shift", (j + 1,), a[j + 1])
            j -= 1
        dest = j + 1
        if dest != i:
            a[dest] = key
            yield Step("set", (dest,), key)
        yield Step("key", (dest,), key)
    yield Step("key", ())


def _merge_sections(a: list[int], start: int, mid: int, end: int) -> Iterator[Step]:
    left = a[start:mid]
    right = a[mid:end]
    yield Step("merge_mark", (start, end - 1))

    i = 0
    j = 0
    k = start
    while i < len(left) and j < len(right):
        yield Step("merge_compare", (start + i, mid + j), payload=k)
        if left[i] <= right[j]:
            yield Step("set", (k,), left[i])
            a[k] = left[i]
            i += 1
        else:
            yield Step("set", (k,), right[j])
            a[k] = right[j]
            j += 1
        k += 1

    while i < len(left):
        yield Step("set", (k,), left[i])
        a[k] = left[i]
        i += 1
        k += 1

    while j < len(right):
        yield Step("set", (k,), right[j])
        a[k] = right[j]
        j += 1
        k += 1


@register(
    AlgoInfo(
        name="Timsort Trace",
        stable=True,
        in_place=False,
        comparison=True,
        complexity={"best": "O(n)", "avg": "O(n log n)", "worst": "O(n log n)"},
    )
)
def timsort_trace(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        return

    run = max(MIN_RUN, 1)
    run = min(run, n)

    for start in range(0, n, run):
        end = min(start + run, n)
        yield from _insertion_sort_section(a, start, end)

    size = run
    while size < n:
        for start in range(0, n, 2 * size):
            mid = min(start + size, n)
            end = min(start + 2 * size, n)
            if mid < end:
                yield from _merge_sections(a, start, mid, end)
        size *= 2

    for idx in range(n):
        yield Step("confirm", (idx,))
