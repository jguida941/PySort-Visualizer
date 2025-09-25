from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Counting Sort",
        stable=True,
        in_place=False,
        comparison=False,
        complexity={"best": "O(n + k)", "avg": "O(n + k)", "worst": "O(n + k)"},
    )
)
def counting_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        return

    original = list(a)
    min_val = min(original)
    max_val = max(original)
    offset = -min_val
    size = max_val - min_val + 1

    counts = [0] * size
    for value in original:
        counts[value + offset] += 1

    total = 0
    for i, cnt in enumerate(counts):
        counts[i] = total
        total += cnt

    for value in reversed(original):
        bucket = value + offset
        position = counts[bucket]
        counts[bucket] += 1
        a[position] = value
        yield Step("set", (position,), value)
        yield Step("key", (position,), value)

    for idx in range(n):
        yield Step("confirm", (idx,))
