from app.core.step import Step


def apply_step_sequence(arr: list[int], steps: list[Step]) -> list[int]:
    a = list(arr)
    for step in steps:
        if step.op == "swap":
            i, j = step.indices
            a[i], a[j] = a[j], a[i]
        elif step.op in {"set", "shift"}:
            (k,) = step.indices
            if step.payload is None:
                raise ValueError("Set/shift step requires a payload")
            a[k] = int(step.payload)
        # compares/pivots/marks don’t change state
    return a
