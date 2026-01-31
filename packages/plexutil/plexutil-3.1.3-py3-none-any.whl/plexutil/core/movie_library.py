from __future__ import annotations

from dataclasses import field
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from pathlib import Path

    from plexapi.library import MovieSection
    from plexapi.server import PlexServer
    from plexapi.video import Movie

    from plexutil.dto.bootstrap_paths_dto import BootstrapPathsDTO
from plexutil.core.library import Library
from plexutil.enums.agent import Agent
from plexutil.enums.language import Language
from plexutil.enums.library_type import LibraryType
from plexutil.enums.scanner import Scanner
from plexutil.enums.user_request import UserRequest


class MovieLibrary(Library):
    def __init__(
        self,
        plex_server: PlexServer,
        user_request: UserRequest,
        bootstrap_paths_dto: BootstrapPathsDTO,
        locations: list[Path] = field(default_factory=list),
        language: Language = Language.get_default(),
        agent: Agent = Agent.get_default(LibraryType.MOVIE),
        scanner: Scanner = Scanner.get_default(LibraryType.MOVIE),
        name: str = LibraryType.MOVIE.get_display_name(),
    ) -> None:
        super().__init__(
            supported_requests=[
                UserRequest.CREATE,
                UserRequest.DELETE,
                UserRequest.DISPLAY,
                UserRequest.UPDATE,
                UserRequest.MODIFY,
            ],
            plex_server=plex_server,
            name=name,
            library_type=LibraryType.MOVIE,
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

    def create(self) -> None:
        super().create()

    def query(self) -> list[Movie]:
        """
        Returns all movies for the current LibrarySection

        Returns:
            list[plexapi.video.Movie]: Movies from the current Section
        """
        op_type = "QUERY"
        self.log_library(operation=op_type, is_info=False, is_debug=True)
        return cast("MovieSection", self.get_section()).searchMovies()

    def delete(self) -> None:
        return super().delete()

    def exists(self) -> bool:
        return super().exists()
