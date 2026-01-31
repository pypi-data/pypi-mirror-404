from __future__ import annotations

from enum import Enum

from plexutil.dto.dropdown_item_dto import (
    DropdownItemDTO,
)
from plexutil.dto.library_setting_dto import LibrarySettingDTO


class ServerSetting(Enum):
    BUTLER_START_HOUR = (
        "ButlerStartHour",
        "Time at which tasks start to run",
        (
            "The time at which the server starts running background "
            "maintenance tasks"
        ),
        False,
        False,
        True,
        [
            DropdownItemDTO(display_name="0:00", value=0),
            DropdownItemDTO(display_name="1:00", value=1),
            DropdownItemDTO(display_name="2:00", value=2),
            DropdownItemDTO(display_name="3:00", value=3),
            DropdownItemDTO(display_name="4:00", value=4),
            DropdownItemDTO(display_name="5:00", value=5),
            DropdownItemDTO(display_name="6:00", value=6),
            DropdownItemDTO(display_name="7:00", value=7),
            DropdownItemDTO(display_name="8:00", value=8),
            DropdownItemDTO(display_name="9:00", value=9),
            DropdownItemDTO(display_name="10:00", value=10),
            DropdownItemDTO(display_name="11:00", value=11),
            DropdownItemDTO(display_name="12:00", value=12),
            DropdownItemDTO(display_name="13:00", value=13),
            DropdownItemDTO(display_name="14:00", value=14),
            DropdownItemDTO(display_name="15:00", value=15),
            DropdownItemDTO(display_name="16:00", value=16),
            DropdownItemDTO(display_name="17:00", value=17),
            DropdownItemDTO(display_name="18:00", value=18),
            DropdownItemDTO(display_name="19:00", value=19),
            DropdownItemDTO(display_name="20:00", value=20),
            DropdownItemDTO(display_name="21:00", value=21),
            DropdownItemDTO(display_name="22:00", value=22),
            DropdownItemDTO(display_name="23:00", value=23, is_default=True),
            DropdownItemDTO(display_name="24:00", value=24),
        ],
        0,
    )
    BUTLER_END_HOUR = (
        "ButlerEndHour",
        "Time at which tasks stop running",
        ("The time at which the background maintenance tasks stop running"),
        False,
        False,
        True,
        [
            DropdownItemDTO(display_name="0:00", value=0),
            DropdownItemDTO(display_name="1:00", value=1),
            DropdownItemDTO(display_name="2:00", value=2),
            DropdownItemDTO(display_name="3:00", value=3),
            DropdownItemDTO(display_name="4:00", value=4),
            DropdownItemDTO(display_name="5:00", value=5),
            DropdownItemDTO(display_name="6:00", value=6, is_default=True),
            DropdownItemDTO(display_name="7:00", value=7),
            DropdownItemDTO(display_name="8:00", value=8),
            DropdownItemDTO(display_name="9:00", value=9),
            DropdownItemDTO(display_name="10:00", value=10),
            DropdownItemDTO(display_name="11:00", value=11),
            DropdownItemDTO(display_name="12:00", value=12),
            DropdownItemDTO(display_name="13:00", value=13),
            DropdownItemDTO(display_name="14:00", value=14),
            DropdownItemDTO(display_name="15:00", value=15),
            DropdownItemDTO(display_name="16:00", value=16),
            DropdownItemDTO(display_name="17:00", value=17),
            DropdownItemDTO(display_name="18:00", value=18),
            DropdownItemDTO(display_name="19:00", value=19),
            DropdownItemDTO(display_name="20:00", value=20),
            DropdownItemDTO(display_name="21:00", value=21),
            DropdownItemDTO(display_name="22:00", value=22),
            DropdownItemDTO(display_name="23:00", value=23),
            DropdownItemDTO(display_name="24:00", value=24),
        ],
        0,
    )
    GENERATE_INTRO_MARKER = (
        "GenerateIntroMarkerBehavior",
        " Generate intro video markers",
        ("Detects show intros, exposing the 'Skip Intro' button in clients"),
        False,
        False,
        True,
        [
            DropdownItemDTO(display_name="never", value="never"),
            DropdownItemDTO(
                display_name="as a scheduled task",
                value="scheduled",
                is_default=True,
            ),
            DropdownItemDTO(
                display_name="as a scheduled task and when media is added",
                value="asap",
            ),
        ],
        0,
    )

    GENERATE_CREDITS_MARKER = (
        "GenerateCreditsMarkerBehavior",
        " Generate credits video markers",
        ("Detects movie and episode end credits"),
        False,
        False,
        True,
        [
            DropdownItemDTO(display_name="never", value="never"),
            DropdownItemDTO(
                display_name="as a scheduled task",
                value="scheduled",
                is_default=True,
            ),
            DropdownItemDTO(
                display_name="as a scheduled task and when media is added",
                value="asap",
            ),
        ],
        0,
    )

    @staticmethod
    def get_all() -> list[ServerSetting]:
        return list(ServerSetting)

    def get_name(self) -> str:
        """
        Name is the canonical name of the Setting in the Plex Server

        Returns:
            str: This Setting's canonical name
        """
        return self.value[0]

    def get_display_name(self) -> str:
        """
        Display Name of the Setting in the GUI

        Returns:
            str: The Display Name
        """
        return self.value[1]

    def get_description(self) -> str:
        """
        Short Description

        Returns:
            str: The Description
        """
        return self.value[2]

    def is_toggle(self) -> bool:
        """
        Is this a Setting a toggle

        Returns:
            bool: Is this a Setting a toggle
        """
        return self.value[3]

    def is_value(self) -> bool:
        """
        Is this a Setting a value i.e: 2

        Returns:
            bool: Is this a Setting a value
        """
        return self.value[4]

    def is_dropdown(self) -> bool:
        """
        Is this a Setting a Dropdown

        Returns:
            bool: Is this a Setting Dropdown
        """
        return self.value[5]

    def get_dropdown(self) -> list[DropdownItemDTO]:
        """
        Get the Dropdown items for this setting

        Returns:
            list[LibrarySettingDropdownItemDTO]: The Dropdown items
        """
        return self.value[6]

    def get_default_selection(self) -> bool | int | str:
        """
        Get the Default selection for this Setting

        Returns:
            bool | int | str: The Default selection
        """
        return self.value[7]

    def to_dto(self, is_from_server: bool = False) -> LibrarySettingDTO:
        """
        Maps to a LibrarySettingDTO

        Args:
            is_from_server (bool): Is setting from Plex Server?

        Returns:
            LibrarySettingDTO: The mapped DTO
        """
        return LibrarySettingDTO(
            name=self.get_name(),
            display_name=self.get_display_name(),
            description=self.get_description(),
            user_response=self.get_default_selection(),
            is_toggle=self.is_toggle(),
            is_value=self.is_value(),
            is_dropdown=self.is_dropdown(),
            dropdown=self.get_dropdown(),
            is_from_server=is_from_server,
        )
