from __future__ import annotations

from dataclasses import field
from typing import TYPE_CHECKING, cast

from plexutil.core.prompt import Prompt
from plexutil.enums.library_setting import LibrarySetting
from plexutil.plex_util_logger import PlexUtilLogger
from plexutil.util.query_builder import QueryBuilder

if TYPE_CHECKING:
    from pathlib import Path

    from plexapi.audio import Track
    from plexapi.library import MusicSection
    from plexapi.server import PlexServer

    from plexutil.dto.bootstrap_paths_dto import BootstrapPathsDTO
from plexutil.core.library import Library
from plexutil.enums.agent import Agent
from plexutil.enums.language import Language
from plexutil.enums.library_type import LibraryType
from plexutil.enums.scanner import Scanner
from plexutil.enums.user_request import UserRequest
from plexutil.exception.library_op_error import LibraryOpError


class MusicLibrary(Library):
    def __init__(
        self,
        plex_server: PlexServer,
        user_request: UserRequest,
        bootstrap_paths_dto: BootstrapPathsDTO,
        locations: list[Path] = field(default_factory=list),
        agent: Agent = Agent.get_default(LibraryType.MUSIC),
        scanner: Scanner = Scanner.get_default(LibraryType.MUSIC),
        name: str = LibraryType.MUSIC.get_display_name(),
        language: Language = Language.get_default(),
    ) -> None:
        super().__init__(
            supported_requests=[
                UserRequest.CREATE,
                UserRequest.UPDATE,
                UserRequest.DELETE,
                UserRequest.DISPLAY,
                UserRequest.MODIFY,
            ],
            plex_server=plex_server,
            name=name,
            library_type=LibraryType.MUSIC,
            agent=agent,
            scanner=scanner,
            locations=locations,
            language=language,
            user_request=user_request,
            bootstrap_paths_dto=bootstrap_paths_dto,
        )

    def download(self) -> None:
        raise NotImplementedError

    def upload(self) -> None:
        raise NotImplementedError

    def add_item(self) -> None:
        raise NotImplementedError

    def remove_item(self) -> None:
        raise NotImplementedError

    def update(self) -> None:
        super().update()

    def modify(self) -> None:
        super().modify()

    def display(self, expect_input: bool = False) -> None:
        super().display(expect_input=expect_input)

    def delete(self) -> None:
        return super().delete()

    def exists(self) -> bool:
        return super().exists()

    def create(self) -> None:
        """
        Creates a Music Library

        Returns:
            None: This method does not return a value

        Raises:
            LibraryOpError: If Library already exists
            or when failure to create a Query
        """
        super().assign_name()
        super().error_if_exists()
        super().assign_locations()
        super().assign_scanner()
        super().assign_agent()
        super().assign_language()

        library_settings = [
            x.to_dto() for x in LibrarySetting.get_all(self.library_type)
        ]

        prefs = {}
        for setting in library_settings:
            response = Prompt.confirm_library_setting(setting)
            prefs[setting.name] = response.user_response

        part = ""
        query_builder = QueryBuilder(
            "/library/sections",
            name=self.name,
            the_type="music",
            agent=self.agent.get_value(),
            scanner=self.scanner.get_value(),
            language=self.language.get_value(),
            location=self.locations,
            prefs=prefs,
        )
        part = query_builder.build()

        description = f"Query: {part}"
        PlexUtilLogger.get_logger().debug(description)

        # This posts a music library
        if part:
            op_type = "CREATE"

            self.log_library(operation=op_type, is_info=False, is_debug=True)

            self.plex_server.query(
                part,
                method=self.plex_server._session.post,
            )
            description = f"Successfully created: {self.name}"
            PlexUtilLogger.get_logger().debug(description)
        else:
            description = "Malformed Music Query"
            raise LibraryOpError(
                op_type="CREATE",
                library_type=self.library_type,
                description=description,
            )

    def query(self) -> list[Track]:
        """
        Returns all tracks for the current LibrarySection

        Returns:
            list[plexapi.audio.Track]: Tracks from the current Section
        """
        op_type = "QUERY"
        self.log_library(operation=op_type, is_info=False, is_debug=True)
        return cast("MusicSection", self.get_section()).searchTracks()
