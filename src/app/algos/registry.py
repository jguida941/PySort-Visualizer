from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
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


def register(info: AlgoInfo) -> Decorator:
    def deco(fn: Algorithm) -> Algorithm:
        REGISTRY[info.name] = fn
        INFO[info.name] = info
        return fn

    return deco
