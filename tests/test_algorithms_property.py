from importlib import import_module

from hypothesis import given
from hypothesis import strategies as st

from app.algos.registry import REGISTRY
from app.core.replay import apply_step_sequence

for module in (
    "app.algos.bubble",
    "app.algos.insertion",
    "app.algos.merge",
    "app.algos.quick",
):
    import_module(module)


@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=60))
def test_all_algorithms_property(arr):
    for name, algo in REGISTRY.items():
        src = list(arr)
        work = list(arr)
        steps = list(algo(work))
        result = apply_step_sequence(src, steps)
        assert result == sorted(arr), f"{name}"
