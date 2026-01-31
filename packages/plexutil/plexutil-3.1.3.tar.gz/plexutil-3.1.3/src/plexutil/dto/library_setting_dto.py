from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plexutil.dto.dropdown_item_dto import (
        DropdownItemDTO,
    )


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class LibrarySettingDTO:
    name: str = ""
    display_name: str = ""
    description: str = ""
    is_toggle: bool = False  # When response expected to be yes/no
    is_value: bool = (
        False  # When response is expected to be an arbitrary number
    )
    is_dropdown: bool = (
        False  # When response is expected to be an index pick on dropdown
    )
    dropdown: list[DropdownItemDTO] = field(default_factory=list)
    user_response: bool | int | str = 0
    is_from_server: bool = False  # Was the Setting already on the Plex Server
