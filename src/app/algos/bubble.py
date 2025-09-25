from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Bubble Sort",
        stable=True,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n)", "avg": "O(n^2)", "worst": "O(n^2)"},
    )
)
def bubble_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            yield Step("compare", (j, j + 1))
            if a[j] > a[j + 1]:
                # Add payload for stateless narration
                payload = (a[j], a[j + 1])
                yield Step("swap", (j, j + 1), payload=payload)
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
