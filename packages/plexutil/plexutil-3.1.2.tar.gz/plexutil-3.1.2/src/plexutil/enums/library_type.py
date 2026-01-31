from __future__ import annotations

from enum import Enum

from plexapi.library import (
    LibrarySection,
    MovieSection,
    MusicSection,
    ShowSection,
)

from plexutil.exception.user_error import UserError


class LibraryType(Enum):
    MOVIE = ("movie", "Movies")
    TV = ("show", "TV Shows")
    MUSIC = ("music", "Music")
    MUSIC_PLAYLIST = ("audio", "Music Playlist")

    @staticmethod
    def get_all() -> list[LibraryType]:
        return list(LibraryType)

    @staticmethod
    def get_from_str(candidate: str) -> LibraryType:
        libs = LibraryType.get_all()
        for lib in libs:
            if lib.get_display_name().lower() == candidate.lower():
                return lib
        description = (
            f"Couldn't determine Library Type from: {candidate} | Available:\n"
        )
        for lib in libs:
            description = description + f"-> {lib.get_display_name()}\n"
        raise UserError(description)

    def get_value(self) -> str:
        return self.value[0]

    def get_display_name(self) -> str:
        return self.value[1]

    @staticmethod
    def get_default() -> LibraryType:
        return LibraryType.MOVIE

    @staticmethod
    def is_eq(
        library_type: LibraryType, library_section: LibrarySection
    ) -> bool:
        return (
            (
                isinstance(library_section, MovieSection)
                and library_type is LibraryType.MOVIE
            )
            or (
                isinstance(library_section, MusicSection)
                and library_type is LibraryType.MUSIC
            )
            or (
                isinstance(library_section, MusicSection)
                and library_type is LibraryType.MUSIC_PLAYLIST
            )
            or (
                isinstance(library_section, ShowSection)
                and library_type is LibraryType.TV
            )
        )

    @staticmethod
    def get_from_section(library_section: LibrarySection) -> LibraryType:
        match library_section:
            case MovieSection():
                return LibraryType.MOVIE
            case MusicSection():
                return LibraryType.MUSIC
            case ShowSection():
                return LibraryType.TV
            case _:
                return LibraryType.MUSIC
