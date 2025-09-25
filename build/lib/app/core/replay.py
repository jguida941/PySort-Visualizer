from .step import Step


def apply_step_sequence(arr: list[int], steps: list[Step]) -> list[int]:
    a = list(arr)
    for s in steps:
        if s.op == "swap":
            i, j = s.indices
            a[i], a[j] = a[j], a[i]
        elif s.op == "set":
            (k,) = s.indices
            a[k] = int(s.payload)
        # compares/pivots/marks don’t change state
    return a
