from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Bucket Sort",
        stable=True,
        in_place=False,
        comparison=False,
        complexity={"best": "O(n)", "avg": "O(n + k)", "worst": "O(n^2)"},
    )
)
def bucket_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        return

    arr = list(a)
    min_val = min(arr)
    max_val = max(arr)
    if min_val == max_val:
        for idx, value in enumerate(arr):
            a[idx] = value
            yield Step("confirm", (idx,))
        return

    # Normalize values to [0, 1]
    range_val = max_val - min_val
    bucket_count = max(1, min(n, range_val + 1))
    buckets: list[list[int]] = [[] for _ in range(bucket_count)]

    for value in arr:
        index = int((value - min_val) / range_val * (bucket_count - 1))
        buckets[index].append(value)

    idx = 0
    for bucket in buckets:
        bucket.sort()
        for value in bucket:
            a[idx] = value
            yield Step("set", (idx,), value)
            yield Step("key", (idx,), value)
            idx += 1

    for i in range(n):
        yield Step("confirm", (i,))
