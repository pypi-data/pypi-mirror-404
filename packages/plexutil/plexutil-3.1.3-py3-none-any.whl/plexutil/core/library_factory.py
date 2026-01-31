from __future__ import annotations

from typing import TYPE_CHECKING

from plexutil.core.music_playlist import MusicPlaylist
from plexutil.core.prompt import Prompt

if TYPE_CHECKING:
    from plexapi.server import PlexServer

    from plexutil.core.library import Library
    from plexutil.dto.bootstrap_paths_dto import BootstrapPathsDTO
    from plexutil.enums.user_request import UserRequest

from plexutil.core.movie_library import MovieLibrary
from plexutil.core.music_library import MusicLibrary
from plexutil.core.tv_library import TVLibrary
from plexutil.static import Static


class LibraryFactory(Static):
    @staticmethod
    def get(
        plex_server: PlexServer,
        user_request: UserRequest,
        bootstrap_paths_dto: BootstrapPathsDTO,
    ) -> Library:
        """
        Prompts user for a LibraryType

        Args:
            plex_server (PlexServer): Used by Libraries
            user_request (UserRequest): Used by Libraries
            bootstrap_paths_dto (BootstrapPathsDTO): Used by Libraries

        Returns:
            Library: The initiazed Library chosen by the user
        """
        libraries = []
        libraries.append(
            MovieLibrary(
                plex_server=plex_server,
                user_request=user_request,
                bootstrap_paths_dto=bootstrap_paths_dto,
            )
        )
        libraries.append(
            TVLibrary(
                plex_server=plex_server,
                user_request=user_request,
                bootstrap_paths_dto=bootstrap_paths_dto,
            )
        )
        libraries.append(
            MusicLibrary(
                plex_server=plex_server,
                user_request=user_request,
                bootstrap_paths_dto=bootstrap_paths_dto,
            )
        )
        libraries.append(
            MusicPlaylist(
                plex_server=plex_server,
                user_request=user_request,
                bootstrap_paths_dto=bootstrap_paths_dto,
            )
        )
        return Prompt.confirm_library(
            user_request=user_request,
            libraries=libraries,
            is_multi_column=False,
            expect_input=True,
            is_from_server=False,
        )
