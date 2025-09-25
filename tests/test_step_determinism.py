from __future__ import annotations

from importlib import import_module

from app.algos.registry import REGISTRY
from app.core.replay import apply_step_sequence

for module in (
    "app.algos.bubble",
    "app.algos.insertion",
    "app.algos.merge",
    "app.algos.quick",
):
    import_module(module)


def test_step_replay_deterministic():
    initial_array = [5, 3, 4, 1, 2]

    for name, algo in REGISTRY.items():
        working_array = list(initial_array)
        steps = list(algo(working_array))

        replayed_array = apply_step_sequence(initial_array, steps)

        assert working_array == sorted(initial_array), f"generator result mismatch for {name}"
        assert replayed_array == working_array, f"replay diverged from generator for {name}"
