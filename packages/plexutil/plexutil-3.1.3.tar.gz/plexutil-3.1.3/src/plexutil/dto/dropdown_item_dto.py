from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class DropdownItemDTO:
    display_name: str = ""
    value: Any = 0
    is_default: bool = False
