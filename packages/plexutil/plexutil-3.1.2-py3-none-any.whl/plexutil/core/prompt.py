from __future__ import annotations

import argparse
import os
import platform
import sys
from argparse import RawTextHelpFormatter
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, cast

from plexutil.exception.device_error import DeviceError
from plexutil.graphical.selection_window import SelectionWindow

if TYPE_CHECKING:
    from plexapi.audio import Audio, Playlist
    from plexapi.library import (
        LibrarySection,
        MovieSection,
        MusicSection,
        ShowSection,
    )
    from plexapi.myplex import MyPlexResource
    from plexapi.video import Movie, Show

    from plexutil.core.library import Library
    from plexutil.dto.song_dto import SongDTO

from plexutil.dto.dropdown_item_dto import DropdownItemDTO
from plexutil.dto.library_setting_dto import LibrarySettingDTO
from plexutil.enums.agent import Agent
from plexutil.enums.language import Language
from plexutil.enums.library_type import LibraryType
from plexutil.enums.scanner import Scanner
from plexutil.enums.user_request import UserRequest
from plexutil.exception.unexpected_argument_error import (
    UnexpectedArgumentError,
)
from plexutil.plex_util_logger import PlexUtilLogger
from plexutil.static import Static
from plexutil.util.file_importer import FileImporter
from plexutil.util.icons import Icons


class Prompt(Static):
    @staticmethod
    def confirm_user_request() -> UserRequest:
        """
        Receives initial user input with a request or --version
        Issues early termination if --version is requested

        Returns:
            UserRequest: Based on user's input
        """
        parser = argparse.ArgumentParser(
            description="Plexutil", formatter_class=RawTextHelpFormatter
        )

        request_help_str = "Supported Requests: \n"

        for request in UserRequest.get_all():
            request_help_str += "-> " + request.value + "\n"

        parser.add_argument(
            "request",
            metavar="Request",
            type=str,
            nargs="?",
            help=request_help_str,
        )

        parser.add_argument(
            "-v",
            "--version",
            action="store_true",
            help=("Displays version"),
        )

        args, unknown = parser.parse_known_args()

        if unknown:
            raise UnexpectedArgumentError(unknown)

        request = args.request
        is_version = args.version

        if is_version:
            plexutil_version = ""

            try:
                plexutil_version = version("plexutil")

            except PackageNotFoundError:
                pyproject = FileImporter.get_pyproject()
                plexutil_version = pyproject["project"]["version"]

            debug = "Received a User Request: version"
            PlexUtilLogger.get_logger().debug(debug)
            PlexUtilLogger.get_logger().info(plexutil_version)
            sys.exit(0)

        debug = f"Received a User Request: {request or None}"
        PlexUtilLogger.get_logger().debug(debug)

        return UserRequest.get_user_request_from_str(request)

    @staticmethod
    def confirm_library_setting(
        library_setting: LibrarySettingDTO,
    ) -> LibrarySettingDTO:
        user_response = library_setting.user_response

        if library_setting.is_toggle:
            response = Prompt.__get_toggle_response(
                title=library_setting.display_name,
                description=library_setting.description,
                question=library_setting.display_name,
                default_selection=bool(library_setting.user_response),
                is_from_server=library_setting.is_from_server,
            )
            user_response = (
                int(response)
                if isinstance(library_setting.user_response, int)
                else bool(response)
            )

        elif library_setting.is_value:
            pass
        elif library_setting.is_dropdown:
            dropdown = library_setting.dropdown
            user_response = Prompt.draw_dropdown(
                title=library_setting.display_name,
                description=library_setting.description,
                dropdown=dropdown,
                is_multi_column=True,
                is_from_server=library_setting.is_from_server,
            ).value

        return LibrarySettingDTO(
            name=library_setting.name,
            display_name=library_setting.display_name,
            description=library_setting.description,
            is_toggle=library_setting.is_toggle,
            is_value=library_setting.is_value,
            is_dropdown=library_setting.is_dropdown,
            dropdown=library_setting.dropdown,
            user_response=user_response,
        )

    @staticmethod
    def confirm_language(
        default: Language = Language.get_default(),
        is_from_server: bool = False,
    ) -> Language:
        """
        Prompts user for a Language

        Args:
            default (Language): The Language to select by default
            is_from_server (bool): Is this selection from the server

        Returns:
            Language: The chosen Language
        """
        languages = Language.get_all()
        items = [
            DropdownItemDTO(
                display_name=language.get_display_name(),
                value=language,
                is_default=default is language,
            )
            for language in languages
        ]

        response = Prompt.draw_dropdown(
            title="Language Selection",
            description="Choose the Language",
            dropdown=items,
            is_multi_column=True,
            is_from_server=is_from_server,
        )

        return response.value

    @staticmethod
    def confirm_text(title: str, description: str, question: str) -> list[str]:
        """
        Prompts the user for text,
        expects one or multiple entries separated by ,

        Args:
            title (str): Top banner title
            description (str): Helpful text
            question (str): Question

        Returns:
            str: The User's response
        """
        return cast(
            "str",
            Prompt.__get_text_response(
                title=title,
                description=description,
                question=question,
            ),
        ).split(",")

    @staticmethod
    def confirm_scanner(library_type: LibraryType) -> Scanner:
        """
        Prompt user for a Scanner

        Returns:
            Scanner: The chosen Scanner
        """
        description = (
            "Scanners in Plex are the server components "
            "that go look at the media locations you specify "
            "for your libraries and then figure out:\n\n"
            "1. Whether the file is appropriate for that library "
            "(e.g. is it a TV episode for a TV library?)\n"
            "2. If it's the appropriate type, then which item is it "
            "(e.g. it's season 3, episode 7 of the show Futurama)\n\n"
        )

        scanners = Scanner.get_all()
        filtered_scanners = [
            scanner
            for scanner in scanners
            if scanner.is_compatible(library_type)
        ]
        dropdown = [
            DropdownItemDTO(
                display_name=filtered_scanner.get_label(),
                value=filtered_scanner,
                is_default=Scanner.get_default(library_type)
                is filtered_scanner,
            )
            for filtered_scanner in filtered_scanners
        ]
        user_response = Prompt.draw_dropdown(
            title="Scanner Selection",
            description=description,
            dropdown=dropdown,
        )

        return user_response.value

    @staticmethod
    def confirm_agent(library_type: LibraryType) -> None:
        """
        Prompt user for an Agent

        Returns:
            None: This method does not return a value.
        """
        description = (
            "Metadata Agents are the server component that's responsible \n"
            "for taking the information from the scanner and then acting on \n"
            "it to help bring in the rich metadata (plot summary, "
            "cast info, cover art, music album reviews, etc.) \n\n"
        )
        agents = Agent.get_all()
        filtered_agents = [
            agent for agent in agents if agent.is_compatible(library_type)
        ]
        dropdown = [
            DropdownItemDTO(
                display_name=filtered_agent.get_label(library_type),
                value=filtered_agent,
                is_default=Agent.get_default(library_type) is filtered_agent,
            )
            for filtered_agent in filtered_agents
        ]
        user_response = Prompt.draw_dropdown(
            "Agent Selection", description, dropdown=dropdown
        )
        return user_response.value

    @staticmethod
    def confirm_library(
        user_request: UserRequest,
        libraries: list[Library],
        is_multi_column: bool = False,
        expect_input: bool = True,
        is_from_server: bool = False,
    ) -> Library:
        """
        Prompts user for a Library Selection

        Args:
            user_request (UserRequest): Required to filter the compatible
            library to display
            dropdown (list[Library]): The libraries to consider
            is_multi_column (bool): Display the dropdown in multiple columns
            expect_input (bool): Prompt the user for a response
            is_from_server (bool): is default_selection an existing value
            from the plex server?

        Returns:
            Library: The selected Library
            DropdownItemDTO: The selected item or the default in the dropdown
        """
        dropdown = [
            DropdownItemDTO(
                display_name=library.library_type.get_display_name(),
                value=library,
                is_default=library.library_type is LibraryType.get_default(),
            )
            for library in libraries
            if user_request in library.supported_requests
        ]

        return Prompt.draw_dropdown(
            title="Library Type",
            description=f"Choose a Library Type to {user_request.value}",
            dropdown=dropdown,
            is_multi_column=is_multi_column,
            expect_input=expect_input,
            is_from_server=is_from_server,
        ).value

    @staticmethod
    def confirm_library_section(
        library_type: LibraryType,
        expect_input: bool,
        sections: list[LibrarySection],
    ) -> LibrarySection:
        dropdown = []
        for section in sections:
            if library_type is LibraryType.MOVIE:
                media_count = len(
                    cast("list[MovieSection]", section.searchMovies())
                )
                display_name = f"{section.title} ({media_count!s} Movies)"
            elif library_type is LibraryType.TV:
                media_count = len(
                    cast("list[ShowSection]", section.searchShows())
                )
                display_name = f"{section.title} ({media_count!s} Shows)"
            elif (
                library_type is LibraryType.MUSIC
                or library_type is LibraryType.MUSIC_PLAYLIST
            ):
                media_count = len(
                    cast("list[MusicSection]", section.searchTracks())
                )
                display_name = f"{section.title} ({media_count!s} Tracks)"

            dropdown.append(
                DropdownItemDTO(display_name=display_name, value=section)
            )

        library_type_name = library_type.get_display_name()

        return Prompt.draw_dropdown(
            title=f"{library_type_name}",
            description=f"Displaying Available {library_type_name} Libraries",
            dropdown=dropdown,
            expect_input=expect_input,
        ).value

    @staticmethod
    def confirm_playlist(
        library_type: LibraryType,
        playlists: list[Playlist],
        expect_input: bool,
    ) -> Playlist:
        dropdown = []

        for playlist in playlists:
            media_count = len(playlist.items())
            display_name = f"{playlist.title} ({media_count!s} items)"
            dropdown.append(
                DropdownItemDTO(display_name=display_name, value=playlist)
            )

        library_type_name = library_type.get_display_name()
        return Prompt.draw_dropdown(
            f"{library_type_name}",
            f"Displaying Available {library_type_name}",
            dropdown=dropdown,
            expect_input=expect_input,
        ).value

    @staticmethod
    def confirm_server(plex_resources: list[MyPlexResource]) -> MyPlexResource:
        """
        Prompts user for a Plex Media Server selection

        Args:
            plex_resources (list[MyPlexResource]): Plex resources,
            anything other than a Plex Media Server is filtered

        Returns:
            MyPlexResource: The chosen Plex Media Server
        """
        is_default = True
        dropdown = []
        for resource in plex_resources:
            if resource.product == "Plex Media Server":
                item = DropdownItemDTO(
                    display_name=f"{resource.name} ({resource.device})",
                    value=resource,
                    is_default=is_default,
                )
                is_default = False
                dropdown.append(item)

        return Prompt.draw_dropdown(
            title="Available Servers",
            description="Choose a server to connect to",
            dropdown=dropdown,
        ).value

    @staticmethod
    def confirm_plex_media(
        title: str,
        description: str,
        plex_media: list[Movie] | list[Show] | list[Audio],
    ) -> Movie | Show | Audio:
        """
        Prompts user for a Plex Media Server selection

        Args:
            title (str): Message to display at the top of the banner
            description (str): helpful message to display in banner body
            plex_media (list[Movie | Show | Audio]): The Media items to display

        Returns:
            Movie | Show | Audio: The chosen Plex Media
        """
        dropdown = [
            DropdownItemDTO(display_name=media.title, value=media)
            for media in plex_media
        ]
        return Prompt.draw_dropdown(
            title=title,
            description=description,
            dropdown=dropdown,
        ).value

    @staticmethod
    def draw_dropdown(
        title: str,
        description: str,
        dropdown: list[DropdownItemDTO],
        is_multi_column: bool = False,
        expect_input: bool = True,
        is_from_server: bool = False,
    ) -> DropdownItemDTO:
        """
        Draws a banner and a dropdown

        Args:
            title (str): Message to display at the top of the banner
            description (str): helpful message to display in banner body
            dropdown (list[DropdownItemDTO]): The items to display
            is_multi_column (bool): Display the dropdown in multiple columns
            expect_input (bool): Prompt the user for a response
            is_from_server (bool): is default_selection an existing value
            from the plex server?

        Returns:
            DropdownItemDTO: The selected item or the default in the dropdown
        """
        min_required_for_multi_column = 6
        if not dropdown:
            Prompt.__draw_banner(title=title, description=description)
            description = f"\n\n{Icons.WARNING} Nothing Available\n"
            PlexUtilLogger.get_console_logger().warning(description)
            return DropdownItemDTO()

        has_default = any(item.is_default for item in dropdown)
        if not has_default:
            dropdown[0] = DropdownItemDTO(
                display_name=dropdown[0].display_name,
                value=dropdown[0].value,
                is_default=True,
            )

        if len(dropdown) < min_required_for_multi_column:
            is_multi_column = False

        dropdown_count = 1
        columns_count = 1
        max_columns = 3 if is_multi_column else 1
        max_column_width = 25
        max_single_space = 10
        max_double_space = 100
        space = ""
        newline = "\n"
        star_space = 2 if expect_input else 0

        description = f"{description}\n\n"
        for item in dropdown:
            if item.is_default:
                offset = max_column_width - (
                    len(item.display_name) + star_space
                )
            else:
                offset = max_column_width - len(item.display_name)

            space = " " * offset
            if dropdown_count < max_single_space:
                number_format = f"[  {dropdown_count}] "
            elif dropdown_count < max_double_space:
                number_format = f"[ {dropdown_count}] "
            else:
                number_format = f"[{dropdown_count}] "

            if item.is_default and expect_input:
                display_name = f"{item.display_name} {Icons.STAR}"
            else:
                display_name = f"{item.display_name}"

            description = (
                f"{description}{number_format} -> {display_name}"
                f"{space if columns_count < max_columns else newline}"
            )

            dropdown_count = dropdown_count + 1
            columns_count = (
                1 if columns_count >= max_columns else columns_count + 1
            )

        if expect_input:
            return Prompt.__get_dropdown_response(
                title=title,
                description=description,
                dropdown=dropdown,
                is_from_server=is_from_server,
            )

        else:
            Prompt.__draw_banner(title=title, description=description)
            return DropdownItemDTO()

    @staticmethod
    def __draw_banner(
        title: str,
        description: str,
        question: str = "",
    ) -> None:
        """
        Draws a banner

        Args:
            title (str): Message to display at the top of the banner
            description (str): helpful message to display in banner body
            default_selection (bool): The value to display as Default/Current
            is_current (bool): is default_selection an existing value
            from the plex server?
            question (str): The question, ? (y/n) is appended after it
            if default_selection is a bool

        Returns:
            None: This method does not return a value
        """
        question = question.replace("?", "")
        question = f"\n{question}?" if question else "\n"

        banner = (
            f"\n{Icons.BANNER_LEFT} {title} {Icons.BANNER_RIGHT}\n"
            f"\n{description}"
            f"{question}"
        )

        PlexUtilLogger.get_console_logger().info(banner)

    @staticmethod
    def __get_toggle_response(
        title: str,
        description: str,
        question: str,
        default_selection: bool = False,
        is_from_server: bool = False,
    ) -> bool:
        """
        Prompt user for a y/n response
        Returns default_selection if user response not recognized

        Args:
            title (str): Message to display at the top of the banner
            description (str): helpful message to display in banner body
            question (str): The question, ? (y/n) is appended after it
            default_selection (bool): The default value
            is_from_server (bool): is default_selection an existing value
            from the plex server?

        Returns:
            bool: yes/no selection from user or
            str: The text input by the ser or
            int: The index chosen by the user
            bool or str or int: default_selection if user input nor recognized
        """
        Prompt.__draw_banner(
            title=title,
            description=description,
            question=question,
        )
        if default_selection:
            description = f"\nAnswer ({Icons.STAR}y/n) {Icons.CHEVRON_RIGHT}"
        else:
            description = f"\nAnswer (y/{Icons.STAR}n) {Icons.CHEVRON_RIGHT}"

        response = input(description).strip().lower()

        description = f"{question}? User chose: {response}"
        PlexUtilLogger.get_logger().debug(description)

        if response in {"y", "yes"}:
            return True
        elif response in {"n", "no"}:
            return False
        else:
            if is_from_server:
                description = (
                    f"{Icons.WARNING} Did not understand your input: "
                    f"{response} | Setting Remains Unchanged "
                    f"({'y' if default_selection else 'n'})"
                )
            else:
                description = (
                    f"{Icons.WARNING} Did not understand your input: "
                    f"{response} | Proceeding with default "
                    f"({'y' if default_selection else 'n'})"
                )
            PlexUtilLogger.get_logger().warning(description)
            return default_selection

    @staticmethod
    def __get_text_response(
        title: str,
        description: str,
        question: str,
        is_multi_value: bool = False,
    ) -> str:
        """
        Prompt user for a text response

        Args:
            title (str): Message to display at the top of the banner
            description (str): helpful message to display in banner body
            question (str): The question, ? (y/n) is appended after it
            is_multi_value (bool): Suggest user to separate values w/ comma

        Returns:
            str: The text input by the user
        """
        Prompt.__draw_banner(
            title=title,
            description=description,
            question=question,
        )
        if is_multi_value:
            description = (
                f"\nEnter text (For multiple values, "
                f"separate with comma i.e text1,text2) {Icons.CHEVRON_RIGHT}"
            )
        else:
            description = f"\nEnter text {Icons.CHEVRON_RIGHT}"
        response = input(description).strip()

        description = f"{question}? User chose: {response}"
        PlexUtilLogger.get_logger().debug(description)

        return response

    @staticmethod
    def __get_dropdown_response(
        title: str,
        description: str,
        dropdown: list[DropdownItemDTO],
        is_from_server: bool = False,
    ) -> DropdownItemDTO:
        """
        Prompt user for a dropdown response

        Args:
            title (str): Message to display at the top of the banner
            description (str): helpful message to display in banner body
            dropdown (list[DropdownItemDTO]): The items to display
            is_current (bool): is default_selection an existing value
            from the plex server?

        Returns:
            DropdownItemDTO: The selection from the user or the default
        """
        Prompt.__draw_banner(
            title=title,
            description=description,
        )
        response = ""
        dropdown_length = len(dropdown)
        default_item = next(x for x in dropdown if x.is_default)

        description = f"Pick (1-{dropdown_length!s}) {Icons.CHEVRON_RIGHT} "
        response = input(description).strip()

        if response.isdigit():
            int_response = int(response)
            if int_response > 0 and int_response <= dropdown_length:
                response = dropdown[int_response - 1]
                description = f"{title} | User chose: {response.display_name}"
                PlexUtilLogger.get_logger().debug(description)
                return response

        if is_from_server:
            description = (
                f"{Icons.WARNING} Did not understand your input: "
                f"{response} | Setting Remains Unchanged "
                f"({default_item.display_name})"
            )
        else:
            description = (
                f"{Icons.WARNING} Did not understand your input: "
                f"{response} | Proceeding with default "
                f"({default_item.display_name})"
            )
        PlexUtilLogger.get_logger().warning(description)
        return default_item

    @staticmethod
    def graphical_confirm_songs(
        songs: list[SongDTO],
        playlist_name: str,
        command: str,
    ) -> list[SongDTO]:
        Prompt.__halt_non_interactive()
        items = [
            DropdownItemDTO(display_name=str(song), value=song)
            for song in songs
        ]
        window = SelectionWindow(
            items=items,
            items_label="Songs",
            recipient_label=playlist_name,
            command=command,
        )
        window.start()
        return [x.value for x in window.get_selections()]

    @staticmethod
    def __halt_non_interactive() -> None:
        system = platform.system()

        if system == "Windows":
            return
        elif system == "Linux":
            session = os.getenv("XDG_SESSION_TYPE") or ""
            if session.startswith(("wayland", "x11")):
                return
            else:
                description = f"Not a graphical session: {session}"
                raise DeviceError(description)
        else:
            description = f"Unsupported system: {system}"
            raise DeviceError(description)
