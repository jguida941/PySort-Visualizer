from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Cocktail Shaker Sort",
        stable=True,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n)", "avg": "O(n^2)", "worst": "O(n^2)"},
    )
)
def cocktail_shaker_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        return

    start = 0
    end = n - 1
    while start < end:
        swapped = False

        # Forward pass
        for i in range(start, end):
            yield Step("compare", (i, i + 1))
            if a[i] > a[i + 1]:
                payload = (a[i], a[i + 1])
                yield Step("swap", (i, i + 1), payload=payload)
                a[i], a[i + 1] = a[i + 1], a[i]
                swapped = True
        yield Step("confirm", (end,))
        end -= 1

        if not swapped:
            break

        swapped = False

        # Backward pass
        for i in range(end, start, -1):
            yield Step("compare", (i - 1, i))
            if a[i - 1] > a[i]:
                payload = (a[i - 1], a[i])
                yield Step("swap", (i - 1, i), payload=payload)
                a[i - 1], a[i] = a[i], a[i - 1]
                swapped = True
        yield Step("confirm", (start,))
        start += 1

        if not swapped:
            break

    for idx in range(n):
        yield Step("confirm", (idx,))
