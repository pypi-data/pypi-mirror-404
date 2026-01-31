from __future__ import annotations

from enum import Enum

from plexutil.enums.library_type import LibraryType
from plexutil.exception.library_unsupported_error import (
    LibraryUnsupportedError,
)
from plexutil.exception.user_error import UserError
from plexutil.plex_util_logger import PlexUtilLogger


# Resolves Metadata after Scanner has identified the media
# https://support.plex.tv/articles/200241558-agents/
# (Value, MovieLabel, TVLabel if different from MovieLabel)
class Agent(Enum):
    # Music Only
    MUSIC = ("tv.plex.agents.music", "Plex Music")
    LASTFM = ("com.plexapp.agents.lastfm", "Last.fm")

    # TV Only
    TV = ("tv.plex.agents.series", "Plex Series")
    TVDB = ("com.plexapp.agents.thetvdb", "TheTVDB")

    # Movies Only
    MOVIE = ("tv.plex.agents.movie", "Plex Movie")
    IMDB = ("com.plexapp.agents.imdb", "Plex Movie (Legacy)")

    # Movies & TV
    TMDB = ("com.plexapp.agents.themoviedb", "The Movie Database")
    PERSONAL_MEDIA = (
        "com.plexapp.agents.none",
        "Personal Media",
        "Personal Media Shows",
        "Personal Media Artists",
    )

    # Global
    PLEX_PERSONAL_MEDIA = ("tv.plex.agents.none", "Plex Personal Media")

    @staticmethod
    def get_all() -> list[Agent]:
        return list(Agent)

    def is_deprecated(self) -> bool:
        """
        Based on: https://support.plex.tv/articles/200241558-agents/

        Returns:
            bool: Is this a Legacy Agent
        """
        deprecated = [
            Agent.TVDB,
            Agent.IMDB,
            Agent.TMDB,
            Agent.PERSONAL_MEDIA,
            Agent.LASTFM,
        ]
        return self in deprecated

    def is_compatible(self, library_type: LibraryType) -> bool:
        """
        Ensures this Agent is compatible with the supplied LibraryType

        Args:
            library_type (LibraryType): Check compatibility with this Agent

        Returns:
            bool: Is this Agent compatible with the supplied LibraryType
        Raises:
            LibraryUnsupportedError: If supplied Library not Movie/TV/Music
        """
        if library_type is LibraryType.MOVIE:
            return (
                self is Agent.MOVIE
                or self is Agent.IMDB
                or self is Agent.TMDB
                or self is Agent.PERSONAL_MEDIA
                or self is Agent.PLEX_PERSONAL_MEDIA
            )
        elif library_type is LibraryType.TV:
            return (
                self is Agent.TV
                or self is Agent.TVDB
                or self is Agent.TMDB
                or self is Agent.PERSONAL_MEDIA
                or self is Agent.PLEX_PERSONAL_MEDIA
            )

        elif (
            library_type is LibraryType.MUSIC
            or library_type is LibraryType.MUSIC_PLAYLIST
        ):
            return (
                self is Agent.MUSIC
                or self is Agent.LASTFM
                or self is Agent.PLEX_PERSONAL_MEDIA
            )
        return False

    @staticmethod
    def get_from_str(candidate: str, library_type: LibraryType) -> Agent:
        """
        Get an Agent from its str representation
        Logs a Warning if the Agent is deprecated

        Args:
            candidate (str): The likely Agent
            library_type (LibraryType): To ensure compatibility with the Agent

        Returns:
            Agent: Matched from the candidate str

        Raises:
            UserError: If Agent incompatible with the supplied LibraryType
                       If Agent could not be determined from the candidate str
        """
        candidate = candidate.lower()
        for agent in Agent.get_all():
            if (
                candidate == agent.get_label(library_type).lower()
                or candidate == agent.get_value().lower()
            ):
                if not agent.is_compatible(library_type):
                    description = (
                        f"Chosen Agent ({agent.get_label(library_type)}) "
                        f"is not compatible with a "
                        f"{library_type.value} Library"
                    )
                    raise UserError(description)

                if agent.is_deprecated():
                    description = (
                        f"WARNING: Selected Deprecated Agent: "
                        f"{agent.get_label(library_type)}"
                    )
                    PlexUtilLogger.get_logger().warning(description)
                return agent

        description = f"Agent not found: {candidate}"
        raise UserError(description)

    @staticmethod
    def get_default(library_type: LibraryType) -> Agent:
        """
        Gets the default Agent for a supplied LibraryType

        Args:
            library_type (LibraryType): To determine default Agent

        Returns:
            Agent: The Default Agent for the supplied LibraryType

        Raises:
            LibraryUnsupportedError: If LibraryType not Movie/TV/Music
        """
        if library_type is LibraryType.MOVIE:
            return Agent.MOVIE
        elif library_type is LibraryType.TV:
            return Agent.TV
        elif (
            library_type is LibraryType.MUSIC
            or library_type is LibraryType.MUSIC_PLAYLIST
        ):
            return Agent.MUSIC
        else:
            op_type = "Agent Get Default"
            raise LibraryUnsupportedError(op_type, library_type)

    def get_value(self) -> str:
        """
        Value is the canonical name of the Agent in the Plex Server

        Returns:
            str: This Agents canonical name
        """
        return self.value[0]

    def get_label(self, library_type: LibraryType) -> str:
        """
        Label is the Display Name of the Agent in the GUI

        Args:
            library_type (LibraryType): To determine the Display Name to pick

        Returns:
            str: The Agents Display Name

        Raises:
            LibraryUnsupportedError: If Agent.PERSONAL_MEDIA but
                                     LibraryType not Movie/TV/Music
        """
        if self is Agent.PERSONAL_MEDIA:
            if library_type is LibraryType.MOVIE:
                return self.value[1]
            elif library_type is LibraryType.TV:
                return self.value[2]
            elif library_type is LibraryType.MUSIC:
                return self.value[3]
            else:
                op_type = "Agent.PERSONAL_MEDIA Get Label"
                raise LibraryUnsupportedError(op_type, library_type)
        else:
            return self.value[1]
