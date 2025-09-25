from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Tuple


@dataclass
class Step:
    """
    op:
      - "compare"       indices=(i, j)
      - "swap"          indices=(i, j), payload=(value_i, value_j)
      - "pivot"         indices=(p,)
      - "merge_mark"    indices=(lo, hi)
      - "merge_compare" indices=(i, j), payload=k (destination index)
      - "set"           indices=(k,), payload=value
      - "confirm"       indices=(i,) - final green sweep (used by finish sweep)
    """

    op: str
    indices: Tuple[int, ...]
    payload: Optional[Any] = None
