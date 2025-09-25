# app/algos/registry.py
from __future__ import annotations
from typing import Callable, Iterable, Dict
from dataclasses import dataclass

# Your existing Step dataclass should live in app/core/step.py and be imported here.
from app.core.step import Step

Algorithm = Callable[[list[int]], Iterable[Step]]


@dataclass(frozen=True)
class AlgoInfo:
    name: str
    stable: bool
    in_place: bool
    comparison: bool
    complexity: dict[str, str]  # {"best": "O(n)", "avg": "...", "worst": "..."}


REGISTRY: Dict[str, Algorithm] = {}
INFO: Dict[str, AlgoInfo] = {}


def register(info: AlgoInfo):
    def deco(fn: Algorithm) -> Algorithm:
        REGISTRY[info.name] = fn
        INFO[info.name] = info
        return fn

    return deco
