from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Heap Sort",
        stable=False,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n log n)", "avg": "O(n log n)", "worst": "O(n log n)"},
    )
)
def heap_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        return

    def sift_down(start: int, end: int) -> Iterator[Step]:
        root = start
        while True:
            child = 2 * root + 1
            if child > end:
                break
            swap_candidate = root

            yield Step("compare", (swap_candidate, child))
            if a[swap_candidate] < a[child]:
                swap_candidate = child

            right = child + 1
            if right <= end:
                yield Step("compare", (swap_candidate, right))
                if a[swap_candidate] < a[right]:
                    swap_candidate = right

            if swap_candidate == root:
                return

            payload = (a[root], a[swap_candidate])
            yield Step("swap", (root, swap_candidate), payload=payload)
            a[root], a[swap_candidate] = a[swap_candidate], a[root]
            root = swap_candidate

    # Build max heap
    for start in range((n // 2) - 1, -1, -1):
        yield from sift_down(start, n - 1)

    # Extract elements
    for end in range(n - 1, 0, -1):
        payload = (a[0], a[end])
        yield Step("swap", (0, end), payload=payload)
        a[0], a[end] = a[end], a[0]
        yield Step("confirm", (end,))
        yield from sift_down(0, end - 1)

    yield Step("confirm", (0,))
