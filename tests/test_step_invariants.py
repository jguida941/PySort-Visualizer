from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.algos.registry import INFO, REGISTRY
from app.core.replay import apply_step_sequence
from app.core.step import Step

# ---------------------------- helpers ---------------------------- #


def _assert_indices_in_bounds(indices: tuple[int, ...], size: int) -> None:
    for idx in indices:
        assert 0 <= idx < size, f"index {idx} out of bounds for array of size {size}"


def _apply_step_in_place(state: list[int], step: Step) -> None:
    op = step.op
    idx = step.indices
    if op == "swap":
        i, j = idx
        assert (
            isinstance(step.payload, tuple) and len(step.payload) == 2
        ), "swap payload must be tuple of length 2"
        before = (state[i], state[j])
        assert before == tuple(step.payload), "swap payload mismatch"
        state[i], state[j] = state[j], state[i]
    elif op in {"set", "shift"}:
        (k,) = idx
        payload = step.payload
        assert isinstance(payload, int), "set/shift payload must be int"
        state[k] = payload
    elif op == "merge_compare":
        assert isinstance(step.payload, int), "merge_compare payload must be int"
    elif op in {"key", "compare", "pivot", "merge_mark", "confirm"}:
        # Visual-only operations; no mutation required.
        pass
    else:
        raise AssertionError(f"Unknown step op: {op}")


def _verify_structural_invariants(step: Step, size: int, algo_name: str) -> None:
    if step.op == "compare":
        assert len(step.indices) == 2
        _assert_indices_in_bounds(step.indices, size)
    elif step.op == "swap":
        assert len(step.indices) == 2
        _assert_indices_in_bounds(step.indices, size)
        i, j = step.indices
        assert i != j, "swap should involve distinct indices"
        assert isinstance(step.payload, tuple) and len(step.payload) == 2
    elif step.op in {"set", "shift"}:
        assert len(step.indices) == 1
        _assert_indices_in_bounds(step.indices, size)
        assert isinstance(step.payload, int), "set/shift require int payload"
    elif step.op == "merge_compare":
        assert len(step.indices) == 2
        _assert_indices_in_bounds(step.indices, size)
        assert isinstance(step.payload, int), "merge_compare payload must be int"
    elif step.op == "merge_mark":
        assert len(step.indices) == 2
        _assert_indices_in_bounds(step.indices, size)
        lo, hi = step.indices
        assert lo <= hi, "merge_mark lo should be <= hi"
    elif step.op in {"pivot", "confirm"}:
        assert len(step.indices) == 1
        _assert_indices_in_bounds(step.indices, size)
    elif step.op == "key":
        assert len(step.indices) in {0, 1}
        if step.indices:
            _assert_indices_in_bounds(step.indices, size)
            assert isinstance(step.payload, int), "key highlight should carry int payload"
    else:
        pytest.fail(f"Unhandled operation '{step.op}' from algorithm {algo_name}")


# ---------------------------- invariant tests ---------------------------- #


@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=40))
def test_step_invariants(arr: list[int]) -> None:
    for name, algo in REGISTRY.items():
        generator_state = list(arr)
        mirror_state = list(arr)
        steps: list[Step] = []
        snapshots: list[list[int]] = [list(mirror_state)]

        for step in algo(generator_state):
            _verify_structural_invariants(step, len(generator_state), name)
            steps.append(step)
            _apply_step_in_place(mirror_state, step)
            snapshots.append(list(mirror_state))

        # Generator should have produced a sorted array.
        assert generator_state == sorted(arr), f"{name} final array mismatch"
        assert mirror_state == generator_state

        # Replay invariants.
        replayed = apply_step_sequence(arr, steps)
        assert replayed == generator_state, f"Replay diverged for {name}"

        for idx, expected in enumerate(snapshots[1:], start=1):
            assert (
                apply_step_sequence(arr, steps[:idx]) == expected
            ), f"Prefix replay diverged for {name} at step {idx}"


def test_registry_metadata_unique() -> None:
    assert set(REGISTRY.keys()) == set(INFO.keys())
    assert len(REGISTRY) == len(INFO), "Registry/INFO size mismatch"

    seen = set()
    for algo_name, info in INFO.items():
        assert algo_name not in seen, "Duplicate algorithm name detected"
        seen.add(algo_name)

        assert info.name, "AlgoInfo.name must be non-empty"
        complexity = info.complexity
        for key in {"best", "avg", "worst"}:
            assert key in complexity, f"{info.name} missing complexity entry '{key}'"
            assert complexity[key], f"{info.name} complexity '{key}' empty"
