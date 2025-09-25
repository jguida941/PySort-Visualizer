from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib import import_module
from typing import TypeAlias

from app.core.step import Step

Algorithm: TypeAlias = Callable[[list[int]], Iterator[Step]]
Decorator: TypeAlias = Callable[[Algorithm], Algorithm]


@dataclass(frozen=True)
class AlgoInfo:
    name: str
    stable: bool
    in_place: bool
    comparison: bool
    complexity: dict[str, str]


REGISTRY: dict[str, Algorithm] = {}
INFO: dict[str, AlgoInfo] = {}

_ALGO_MODULES: tuple[str, ...] = (
    "app.algos.bubble",
    "app.algos.insertion",
    "app.algos.selection",
    "app.algos.heap",
    "app.algos.shell",
    "app.algos.merge",
    "app.algos.quick",
    "app.algos.cocktail",
    "app.algos.counting",
    "app.algos.radix_lsd",
    "app.algos.bucket",
    "app.algos.comb",
)


def register(info: AlgoInfo) -> Decorator:
    def deco(fn: Algorithm) -> Algorithm:
        REGISTRY[info.name] = fn
        INFO[info.name] = info
        return fn

    return deco


def load_all_algorithms() -> None:
    for module in _ALGO_MODULES:
        import_module(module)
