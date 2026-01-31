from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from plexapi.exceptions import NotFound

from plexutil.core.prompt import Prompt
from plexutil.dto.dropdown_item_dto import DropdownItemDTO
from plexutil.dto.library_setting_dto import LibrarySettingDTO
from plexutil.dto.song_dto import SongDTO
from plexutil.enums.server_setting import ServerSetting
from plexutil.exception.plex_media_missing_error import PlexMediaMissingError
from plexutil.plex_util_logger import PlexUtilLogger
from plexutil.static import Static
from plexutil.util.icons import Icons

if TYPE_CHECKING:
    from plexapi.audio import Track
    from plexapi.library import LibrarySection
    from plexapi.server import PlexServer


class PlexOps(Static):
    @staticmethod
    def set_server_settings(
        plex_server: PlexServer,
    ) -> None:
        """
        Sets Plex Server Settings

        Args:
            plex_server (plexapi.server.PlexServer): A Plex Server instance

        Returns:
            None: This method does not return a value

        """
        server_settings = ServerSetting.get_all()

        for server_setting in server_settings:
            dropdown = server_setting.get_dropdown()
            is_from_server = False
            user_response = server_setting.get_default_selection()
            plex_setting = plex_server.settings.get(server_setting.get_name())
            if plex_setting:
                user_response = plex_setting.value
                is_from_server = True

                dropdown = PlexOps.override_dropdown_default(
                    dropdown=dropdown, value=user_response
                )
            response = Prompt.confirm_library_setting(
                library_setting=server_setting.to_dto(
                    is_from_server=is_from_server
                ),
            )
            plex_setting.set(response.user_response)

        plex_server.settings.save()

    @staticmethod
    def set_library_settings(
        section: LibrarySection,
        settings: list[LibrarySettingDTO],
    ) -> None:
        """
        Sets Library Settings
        Logs a warning if setting doesn't exist

        Args:
            settings (LibrarySettingDTO): The Setting to apply to this Library

        Returns:
            None: This method does not return a value
        """
        for setting in settings:
            if setting.is_from_server:
                name = setting.name
                plex_setting = None
                try:
                    server_settings = section.settings()
                    for server_setting in server_settings:
                        if server_setting and server_setting.id == name:
                            plex_setting = server_setting
                except NotFound:
                    description = (
                        f"{Icons.WARNING} Could not load library setting "
                        f"{name}\n"
                        f"Skipping -> {name}"
                    )
                    PlexUtilLogger.get_logger().warning(description)
                    continue
                if plex_setting:
                    response = plex_setting.value

                    if setting.is_dropdown:
                        dropdown = [
                            DropdownItemDTO(
                                display_name=x.display_name,
                                value=x.value,
                                is_default=x.value == response,
                            )
                            for x in setting.dropdown
                        ]
                        response = 0
                    else:
                        dropdown = setting.dropdown

                    server_setting = LibrarySettingDTO(
                        name=setting.name,
                        display_name=setting.display_name,
                        description=setting.description,
                        user_response=response,
                        is_toggle=setting.is_toggle,
                        is_value=setting.is_value,
                        is_dropdown=setting.is_dropdown,
                        dropdown=dropdown,
                        is_from_server=True,
                    )
                    response = Prompt.confirm_library_setting(server_setting)
                else:
                    description = (
                        f"{Icons.WARNING} Could not load library setting "
                        f"{name}\n"
                        f"Skipping -> {name}"
                    )
                    PlexUtilLogger.get_logger().warning(description)
                    continue
            else:
                response = Prompt.confirm_library_setting(setting)

            try:
                section.editAdvanced(**{response.name: response.user_response})
            except NotFound:
                description = (
                    f"{Icons.WARNING} Library Setting not accepted "
                    f"by the server: {response.name}\n"
                    f"Skipping -> {response.name}:{response.user_response}"
                )
                PlexUtilLogger.get_logger().warning(description)
                continue

    @staticmethod
    def override_dropdown_default(
        dropdown: list[DropdownItemDTO], value: bool | int | str
    ) -> list[DropdownItemDTO]:
        dropdown_no_default = []
        dropdown_default = []
        if dropdown:
            for item in dropdown:
                new_item = DropdownItemDTO()
                if item.is_default:
                    new_item = DropdownItemDTO(
                        display_name=item.display_name,
                        value=item.value,
                        is_default=False,
                    )
                else:
                    new_item = item
                dropdown_no_default.append(new_item)

            for item in dropdown_no_default:
                new_item = DropdownItemDTO()
                if item.value == value:
                    new_item = DropdownItemDTO(
                        display_name=item.display_name,
                        value=item.value,
                        is_default=True,
                    )
                else:
                    new_item = item
                dropdown_default.append(new_item)

        return dropdown_default

    @staticmethod
    def get_song_dto(track: Track) -> SongDTO:
        """
        Maps a Track to a SongDTO

        Args:
            track (Track): The Track to map
        Returns:
            SongDTO: The Track mapped to a SongDTO
        """
        locations = track.locations
        if locations:
            location = locations[0]
            file = Path(location).stem
            artist, title = file.split(" - ", 1)
        else:
            artist = track.grandparentTitle
            title = track.title

        return SongDTO(artist=artist, title=title)

    @staticmethod
    def get_track(song_dto: SongDTO, tracks: list[Track]) -> Track:
        """
        Returns the Track that matches the provided SongDTO

        Args:
            song_dto (SongDTO): The Song to find
            tracks (list[Track]): Where to look for the SongDTO
        Returns:
            Track: The found Track
        Raises:
            PlexMediaMissingError: if SongDTO does not match any of the Tracks
        """
        for track in tracks:
            locations = track.locations
            if locations:
                location = locations[0]
                file = Path(location).stem
                artist, title = file.split(" - ", 1)
            else:
                artist = track.grandparentTitle
                title = track.title
            if artist == song_dto.artist and title == song_dto.title:
                return track
        raise PlexMediaMissingError
