from __future__ import annotations

from enum import Enum

from plexutil.dto.dropdown_item_dto import (
    DropdownItemDTO,
)
from plexutil.dto.library_setting_dto import LibrarySettingDTO
from plexutil.enums.library_type import LibraryType
from plexutil.util.icons import Icons


class LibrarySetting(Enum):
    ENABLE_CINEMA_TRAILERS = (
        "enableCinemaTrailers",
        "Enable Cinema Trailers",
        (
            f"Play Trailers automatically prior to the selected movie\n"
            f"{Icons.WARNING} Also needs to be enabled in the "
            f"client app\n"
        ),
        [LibraryType.MOVIE],
        True,
        False,
        False,
        [],
        0,
    )

    ORIGINAL_TITLES = (
        "originalTitles",
        "Original Titles",
        (
            "Use the original titles for all items "
            "regardless of the library language\n"
        ),
        [LibraryType.MOVIE, LibraryType.TV],
        True,
        False,
        False,
        [],
        0,
    )

    LOCALIZED_ARTWORK = (
        "localizedArtwork",
        "Prefer artwork based on library language",
        "Use localized posters when available\n",
        [LibraryType.MOVIE, LibraryType.TV],
        True,
        False,
        False,
        [],
        1,
    )

    USE_LOCAL_ASSETS = (
        "useLocalAssets",
        "Use local assets",
        (
            "When scanning this library, "
            "use local posters and artwork if present\n"
        ),
        [LibraryType.MOVIE, LibraryType.TV],
        True,
        False,
        False,
        [],
        1,
    )

    RESPECT_TAGS = (
        "respectTags",
        "Prefer local metadata",
        (
            "When scanning this library, prefer "
            "embedded tags and local files if present\n"
        ),
        [LibraryType.MOVIE, LibraryType.TV, LibraryType.MUSIC],
        True,
        False,
        False,
        [],
        0,
    )

    ENABLE_BIF_GENERATION = (
        "enableBIFGeneration",
        "Enable video preview thumbnails",
        (
            "Generate video preview thumbnails for items in this library "
            "when enabled in server settings\n"
        ),
        [LibraryType.MOVIE, LibraryType.TV],
        True,
        False,
        False,
        [],
        1,
    )

    RATINGS_SOURCE = (
        "ratingsSource",
        "Ratings Source",
        "Select a primary source for ratings\n",
        [LibraryType.MOVIE],
        False,
        False,
        True,
        [
            DropdownItemDTO(
                display_name="Rotten Tomatoes",
                value="rottentomatoes",
                is_default=True,
            ),
            DropdownItemDTO(display_name="IMDb", value="imdb"),
            DropdownItemDTO(
                display_name="The Movie Database", value="themoviedb"
            ),
        ],
        0,
    )

    SONIC_ANALYSIS = (
        "musicAnalysis",
        "Sonic Analysis",
        ("Analyze tracks for sonic features\n"),
        [LibraryType.MUSIC],
        True,
        False,
        False,
        [],
        # False,
        0,
    )

    ARTIST_BIOS = (
        "artistBios",
        "Artist Bios",
        ("Load artist biography data from the cloud\n"),
        [LibraryType.MUSIC],
        True,
        False,
        False,
        [],
        # False,
        0,
    )

    ALBUM_REVIEWS = (
        "albumReviews",
        "Album Reviews and Critic Ratings",
        (
            "Load album reviews and critic ratings from the cloud. "
            "Might make you reconsider your taste in music\n"
        ),
        [LibraryType.MUSIC],
        True,
        False,
        False,
        [],
        # False,
        0,
    )

    POPULAR_TRACKS = (
        "popularTracks",
        "Popular Tracks",
        (
            "Load popular track data, which powers radio stations "
            "and the popular tracks area\n"
        ),
        [LibraryType.MUSIC],
        True,
        False,
        False,
        [],
        False,
        0,
    )

    FIND_LYRICS = (
        "useExternalLyrics",
        "Find Lyrics",
        ("Find lyrics for tracks in this library automatically\n"),
        [LibraryType.MUSIC],
        True,
        False,
        False,
        [],
        0,
    )

    CONCERTS = (
        "concerts",
        "Concerts",
        ("Load concert data for artists, in case you leave the house\n"),
        [LibraryType.MUSIC],
        True,
        False,
        False,
        [],
        0,
    )

    GENRES = (
        "genres",
        "Genres",
        "Where to automatically obtain genres for artists and albums\n",
        [LibraryType.MUSIC],
        False,
        False,
        True,
        [
            DropdownItemDTO(
                display_name="Embedded Tags", value=2, is_default=True
            ),
            DropdownItemDTO(display_name="Plex Music", value=1),
            DropdownItemDTO(display_name="None", value=0),
        ],
        0,
    )

    ALBUM_POSTERS = (
        "albumPosters",
        "Album Art",
        "Where to automatically obtain album cover art\n",
        [LibraryType.MUSIC],
        False,
        False,
        True,
        [
            DropdownItemDTO(
                display_name="Local Files Only", value=3, is_default=True
            ),
            DropdownItemDTO(display_name="Plex Music Only", value=2),
            DropdownItemDTO(
                display_name="Both Plex Music and Local Files", value=1
            ),
        ],
        0,
    )

    @staticmethod
    def get_all(library_type: LibraryType) -> list[LibrarySetting]:
        settings = list(LibrarySetting)
        return [
            x
            for x in settings
            if library_type in x.get_compatible_library_types()
        ]

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

    def get_compatible_library_types(self) -> list[LibraryType]:
        """
        The Library Types this setting can be applied to

        Returns:
            str: The Description
        """
        return self.value[3]

    def is_toggle(self) -> bool:
        """
        Is this a Setting a toggle

        Returns:
            bool: Is this a Setting a toggle
        """
        return self.value[4]

    def is_value(self) -> bool:
        """
        Is this a Setting a value i.e: 2

        Returns:
            bool: Is this a Setting a value
        """
        return self.value[5]

    def is_dropdown(self) -> bool:
        """
        Is this a Setting a Dropdown

        Returns:
            bool: Is this a Setting Dropdown
        """
        return self.value[6]

    def get_dropdown(self) -> list[DropdownItemDTO]:
        """
        Get the Dropdown items for this setting

        Returns:
            list[LibrarySettingDropdownItemDTO]: The Dropdown items
        """
        return self.value[7]

    def get_default_selection(self) -> bool | int | str:
        """
        Get the Default selection for this Setting

        Returns:
            bool | int | str: The Default selection
        """
        return self.value[8]

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
