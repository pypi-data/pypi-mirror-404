from __future__ import annotations

from enum import Enum

from plexutil.enums.library_type import LibraryType
from plexutil.exception.library_unsupported_error import (
    LibraryUnsupportedError,
)
from plexutil.exception.user_error import UserError
from plexutil.plex_util_logger import PlexUtilLogger


# Evaluates file name/folder structure to identify media
# https://support.plex.tv/articles/200241548-scanners/
class Scanner(Enum):
    MOVIE = "Plex Movie"
    MOVIE_VIDEO = "Plex Video Files Scanner"
    MOVIE_LEGACY = "Plex Movie Scanner"
    TV = "Plex TV Series"
    TV_LEGACY = "Plex Series Scanner"
    MUSIC = "Plex Music"
    MUSIC_LEGACY = "Plex Music Scanner"

    @staticmethod
    def get_all() -> list[Scanner]:
        return list(Scanner)

    def is_deprecated(self) -> bool:
        """
        Based on: https://support.plex.tv/articles/200241548-scanners/

        Returns:
            bool: Is this a Legacy Scanner
        """
        deprecated = [
            Scanner.MOVIE_LEGACY,
            Scanner.TV_LEGACY,
            Scanner.MUSIC_LEGACY,
        ]
        return self in deprecated

    def is_compatible(self, library_type: LibraryType) -> bool:
        """
        Ensures this Scanner is compatible with the supplied LibraryType

        Args:
            library_type (LibraryType): Check compatibility with this Scanner

        Returns:
            bool: Is this Scanner compatible with the supplied LibraryType
        Raises:
            LibraryUnsupportedError: If supplied Library not Movie/TV/Music
        """
        if library_type is LibraryType.MOVIE:
            return (
                self is Scanner.MOVIE
                or self is Scanner.MOVIE_VIDEO
                or self is Scanner.MOVIE_LEGACY
            )
        elif library_type is LibraryType.TV:
            return self is Scanner.TV or self is Scanner.TV_LEGACY
        elif (
            library_type is LibraryType.MUSIC
            or library_type is LibraryType.MUSIC_PLAYLIST
        ):
            return self is Scanner.MUSIC or self is Scanner.MUSIC_LEGACY

        return False

    @staticmethod
    def get_from_str(candidate: str, library_type: LibraryType) -> Scanner:
        """
        Get a Scanner from its str representation
        Logs a Warning if the Scanner is deprecated

        Args:
            candidate (str): The likely Scanner
            library_type (LibraryType): To check compatibility with the Scanner

        Returns:
            Scanner: Matched from the candidate str

        Raises:
            UserError: If Scanner incompatible with the supplied LibraryType
                       If Scanner couldn't be determined from the candidate str
        """
        candidate = candidate.lower()
        for scanner in Scanner.get_all():
            if (
                candidate == scanner.get_label().lower()
                or candidate == scanner.get_value().lower()
            ):
                if not scanner.is_compatible(library_type):
                    description = (
                        f"Chosen Scanner ({scanner.get_label()}) "
                        f"is not compatible with a "
                        f"{library_type.value} Library"
                    )
                    raise UserError(description)

                if scanner.is_deprecated():
                    description = (
                        f"WARNING: Selected Deprecated Scanner: "
                        f"{scanner.get_label()}"
                    )
                    PlexUtilLogger.get_logger().warning(description)
                return scanner

        description = f"Scanner not found: {candidate}"
        raise UserError(description)

    @staticmethod
    def get_default(library_type: LibraryType) -> Scanner:
        """
        Gets the default Scanner for a supplied LibraryType

        Args:
            library_type (LibraryType): To determine default Scanner

        Returns:
            Scanner: The Default Scanner for the supplied LibraryType

        Raises:
            LibraryUnsupportedError: If LibraryType not Movie/TV/Music
        """
        if library_type is LibraryType.MOVIE:
            return Scanner.MOVIE
        elif library_type is LibraryType.TV:
            return Scanner.TV
        elif (
            library_type is LibraryType.MUSIC
            or library_type is LibraryType.MUSIC_PLAYLIST
        ):
            return Scanner.MUSIC
        else:
            op_type = "Scanner Get Default"
            raise LibraryUnsupportedError(op_type, library_type)

    def get_value(self) -> str:
        """
        Value is the canonical name of the Scanner in the Plex Server

        Returns:
            str: This Scanner canonical name
        """
        return self.value

    def get_label(self) -> str:
        """
        Label is the Display Name of the Scanner in the GUI

        Returns:
            str: The Scanner Display Name
        """
        return self.value
