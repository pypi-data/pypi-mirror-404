from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from plexutil.core.prompt import Prompt
from plexutil.enums.agent import Agent
from plexutil.enums.language import Language
from plexutil.enums.library_setting import LibrarySetting
from plexutil.enums.scanner import Scanner
from plexutil.enums.user_request import UserRequest
from plexutil.exception.library_illegal_state_error import (
    LibraryIllegalStateError,
)
from plexutil.exception.library_poll_timeout_error import (
    LibraryPollTimeoutError,
)
from plexutil.exception.library_section_missing_error import (
    LibrarySectionMissingError,
)
from plexutil.plex_util_logger import PlexUtilLogger
from plexutil.util.icons import Icons
from plexutil.util.plex_ops import PlexOps

if TYPE_CHECKING:
    from plexapi.audio import Track
    from plexapi.library import (
        LibrarySection,
    )
    from plexapi.server import Playlist, PlexServer
    from plexapi.video import Movie, Show

    from plexutil.dto.bootstrap_paths_dto import BootstrapPathsDTO

from alive_progress import alive_bar

from plexutil.enums.library_type import LibraryType
from plexutil.exception.library_op_error import LibraryOpError


class Library(ABC):
    def __init__(
        self,
        supported_requests: list[UserRequest],
        plex_server: PlexServer,
        name: str,
        library_type: LibraryType,
        agent: Agent,
        scanner: Scanner,
        locations: list[Path],
        language: Language,
        user_request: UserRequest,
        bootstrap_paths_dto: BootstrapPathsDTO,
    ) -> None:
        self.supported_requests = supported_requests
        self.plex_server = plex_server
        self.name = name
        self.library_type = library_type
        self.agent = agent
        self.scanner = scanner
        self.locations = locations
        self.language = language
        self.user_request = user_request
        self.bootstrap_paths_dto = bootstrap_paths_dto

    def do(self) -> None:
        match self.user_request:
            case UserRequest.CREATE:
                self.create()
            case UserRequest.DELETE:
                self.display(expect_input=True)
                self.delete()
            case UserRequest.DOWNLOAD:
                self.display(expect_input=True)
                self.download()
            case UserRequest.UPLOAD:
                self.display(expect_input=True)
                self.upload()
            case UserRequest.DISPLAY:
                self.display(expect_input=False)
            case UserRequest.UPDATE:
                self.display(expect_input=True)
                self.update()
            case UserRequest.MODIFY:
                self.display(expect_input=True)
                self.modify()
                self.update()
            case UserRequest.ADD_TO_PLAYLIST:
                self.display(expect_input=True)
                self.add_item()
            case UserRequest.REMOVE_FROM_PLAYLIST:
                self.display(expect_input=True)
                self.remove_item()

    @abstractmethod
    def download(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def upload(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_item(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_item(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self) -> None:
        section = self.get_section()
        section.update()
        section.refresh()

    @abstractmethod
    def modify(self) -> None:
        settings = LibrarySetting.get_all(self.library_type)

        self.assign_language(default=self.language, is_from_server=True)
        self.get_section().edit(
            agent=self.agent.get_value(),
            scanner=self.scanner.get_value(),
            language=self.language.get_value(),
        )

        PlexOps.set_library_settings(
            section=self.get_section(),
            settings=[x.to_dto(is_from_server=True) for x in settings],
        )

    @abstractmethod
    def create(self) -> None:
        """
        Creates a Library
        Logs a warning if a specific Library Setting is rejected by the server

        Returns:
            None: This method does not return a value

        Raises:
            LibraryOpError: If Library already exists
        """
        self.assign_name()
        self.error_if_exists()
        self.assign_locations()
        self.assign_scanner()
        self.assign_agent()
        self.assign_language()

        op_type = "CREATE"

        self.log_library(operation=op_type, is_info=False, is_debug=True)

        self.plex_server.library.add(
            name=self.name,
            type=self.library_type.get_value(),
            agent=self.agent.get_value(),
            scanner=self.scanner.get_value(),
            location=[str(x) for x in self.locations],
            language=self.language.get_value(),
        )

        library_settings = [
            x.to_dto() for x in LibrarySetting.get_all(self.library_type)
        ]

        PlexOps.set_library_settings(
            section=self.get_section(),
            settings=library_settings,
        )

        self.get_section().refresh()

    def assign_language(
        self,
        default: Language = Language.get_default(),
        is_from_server: bool = False,
    ) -> None:
        """
        Ask user for Library Language, or use Default in none provided

        Returns:
            None: This method does not return a value.
        """
        self.language = (
            Prompt.confirm_language(
                default=default, is_from_server=is_from_server
            )
            or Language.get_default()
        )

    def assign_locations(self) -> None:
        """
        Ask user for Library Locations, or use CWD in none provided

        Returns:
            None: This method does not return a value.
        Raises:
            LibraryOpError: If any location not isBrowsable()
        """
        description = (
            "Type Locations for this Library, separated by comma\n"
            "i.e /storage/media/tv,/storage/media/more_tv"
        )
        locations = Prompt.confirm_text(
            title="Locations",
            description=description,
            question="",
        )
        if locations:
            for location in locations:
                is_browsable = self.plex_server.isBrowsable(location)
                if not is_browsable:
                    description = (
                        f"Plex Server cannot find the location: {location!s}\n"
                        f"Consider rebooting the server "
                    )
                    raise LibraryOpError(
                        op_type="ASSIGN LOCATIONS",
                        library_type=self.library_type,
                        description=description,
                    )
            self.locations = [Path(location) for location in locations]
        else:
            self.locations = [Path.cwd()]

    def assign_name(self) -> None:
        """
        Ask user for a Library Name or set a Default Name
        if none provided

        Returns:
            None: This method does not return a value.
        """
        text = Prompt.confirm_text(
            "Library Name",
            "Library requires a name",
            "What should the library name be",
        )
        self.name = text[0] if text else self.library_type.get_display_name()

    def assign_scanner(self) -> None:
        """
        Prompt user for a Scanner

        Returns:
            None: This method does not return a value.
        """
        self.scanner = Scanner.get_default(self.library_type)

    def assign_agent(self) -> None:
        """
        Prompt user for an Agent

        Returns:
            None: This method does not return a value.
        """
        self.agent = Agent.get_default(self.library_type)

    @abstractmethod
    def delete(self) -> None:
        """
        Generic Library Delete

        Returns:
            None: This method does not return a value.

        Raises:
            LibraryOpError: If Library isn't found

        """
        op_type = "DELETE"
        self.log_library(operation=op_type, is_info=False, is_debug=True)

        if self.exists():
            self.get_section().delete()
        else:
            description = f"Does not exist: {self.name}"
            raise LibraryOpError(
                op_type=op_type,
                description=description,
                library_type=self.library_type,
            )

    @abstractmethod
    def exists(self) -> bool:
        """
        Generic LibrarySection Exists

        Returns:
            bool: If LibrarySection exists

        """
        library = f"{self.name} | {self.library_type.get_value()}"

        try:
            self.get_section()
        except LibrarySectionMissingError:
            description = f"Does not exist: {library}"
            PlexUtilLogger.get_logger().debug(description)
            return False

        description = f"Exists: {library}"
        PlexUtilLogger.get_logger().debug(description)
        return True

    @abstractmethod
    def display(self, expect_input: bool = False) -> None:
        sections = self.get_sections()

        selected_section = Prompt.confirm_library_section(
            sections=sections,
            library_type=self.library_type,
            expect_input=expect_input,
        )

        if expect_input:
            self.name = selected_section.title
            self.agent = Agent.get_from_str(
                candidate=selected_section.agent,
                library_type=self.library_type,
            )
            self.scanner = Scanner.get_from_str(
                candidate=selected_section.scanner,
                library_type=self.library_type,
            )
            self.language = Language.get_from_str(selected_section.language)
            self.locations = [
                Path(location) for location in selected_section.locations
            ]

    def error_if_exists(self) -> None:
        op_type = "ERROR IF EXISTS"

        if self.exists():
            description = (
                f"{self.library_type.get_display_name()} with name "
                f"{self.name} already exists"
            )
            raise LibraryOpError(
                op_type=op_type,
                library_type=self.library_type,
                description=description,
            )

    def poll(
        self,
        requested_attempts: int = 0,
        expected_count: int = 0,
        interval_seconds: int = 0,
    ) -> None:
        """
        Performs a query based on the supplied parameters

        Args:
            requested_attempts (int): Amount of times to poll
            expected_count (int): Polling terminates when reaching this amount
            interval_seconds (int): timeout before making a new attempt

        Returns:
            None: This method does not return a value

        Raises:
            LibraryPollTimeoutError: If expected_count not reached
        """
        current_count = len(self.query())
        init_offset = abs(expected_count - current_count)
        time_start = time.time()

        debug = (
            f"\n{Icons.BANNER_LEFT}POLL BEGIN{Icons.BANNER_RIGHT}\n"
            f"Attempts: {requested_attempts!s}\n"
            f"Interval: {interval_seconds!s}\n"
            f"Current count: {current_count!s}\n"
            f"Expected count: {expected_count!s}\n"
            f"Net change: {init_offset!s}\n"
        )

        PlexUtilLogger.get_logger().debug(debug)

        with alive_bar(init_offset) as bar:
            attempts = 0
            display_count = 0
            offset = init_offset

            while attempts < requested_attempts:
                updated_current_count = len(self.query())
                offset = abs(updated_current_count - current_count)
                current_count = updated_current_count

                for _ in range(offset):
                    display_count = display_count + 1
                    bar()

                if current_count == expected_count:
                    break

                if current_count > expected_count:
                    time_end = time.time()
                    time_complete = time_end - time_start
                    description = (
                        f"Expected {expected_count!s} items in the library "
                        f"but Plex Server has {current_count!s}\n"
                        f"Failed in {time_complete:.2f}s\n"
                        f"{Icons.BANNER_LEFT}POLL END{Icons.BANNER_RIGHT}\n"
                    )
                    raise LibraryIllegalStateError(description)

                time.sleep(interval_seconds)
                attempts = attempts + 1
                if attempts >= requested_attempts:
                    time_end = time.time()
                    time_complete = time_end - time_start
                    description = (
                        "Did not reach the expected"
                        f"library count: {expected_count!s}\n"
                        f"Failed in {time_complete:.2f}s\n"
                        f"{Icons.BANNER_LEFT}POLL END{Icons.BANNER_RIGHT}\n"
                    )
                    raise LibraryPollTimeoutError(description)

        time_end = time.time()
        time_complete = time_end - time_start
        debug = (
            f"Reached expected: {expected_count!s} in {time_complete:.2f}s\n"
            f"{Icons.BANNER_LEFT}POLL END{Icons.BANNER_RIGHT}\n"
        )

        PlexUtilLogger.get_logger().debug(debug)

    @abstractmethod
    def query(self) -> list[Track] | list[Show] | list[Movie] | list[Playlist]:
        raise NotImplementedError

    def log_library(
        self,
        operation: str,
        is_info: bool = True,
        is_debug: bool = False,
        is_console: bool = False,
    ) -> None:
        """
        Private logging template to be used by methods of this class

        Args:
            opration (str): The type of operation i.e. CREATE DELETE
            is_info (bool): Should it be logged as INFO
            is_debug (bool): Should it be logged as DEBUG
            is_console (bool): Should it be logged with console handler

        Returns:
            None: This method does not return a value.
        """
        if self.exists():
            library_id = self.get_section().key or "NONE"
        else:
            library_id = "NONE"
        info = (
            f"\n{Icons.BANNER_LEFT}{self.library_type.get_display_name()} "
            f"| {operation} | BEGIN{Icons.BANNER_RIGHT}\n"
            f"ID: {library_id}\n"
            f"Name: {self.name}\n"
            f"Agent: {self.agent.get_value()}\n"
            f"Scanner: {self.scanner.get_value()}\n"
            f"Locations: {self.locations!s}\n"
            f"Language: {self.language.get_value()}\n"
            f"{Icons.BANNER_LEFT}{self.library_type.get_display_name()} "
            f"| {operation} | END{Icons.BANNER_RIGHT}\n"
        )
        if not is_console:
            if is_info:
                PlexUtilLogger.get_logger().info(info)
            if is_debug:
                PlexUtilLogger.get_logger().debug(info)
        else:
            PlexUtilLogger.get_console_logger().info(info)

    def get_section(self) -> LibrarySection:
        """
        Gets an up-to-date Plex Server Library Section
        Gets the first occuring Section, does not have conflict resolution

        Returns:
            LibrarySection: A current LibrarySection

        Raises:
            LibrarySectionMissingError: If no library of the same
            type and name exist
        """
        filtered_sections = self.get_sections()

        for filtered_section in filtered_sections:
            if filtered_section.title == self.name:
                return filtered_section

        if self.name:
            description = f"Library not found: {self.name}"
        else:
            description = "Missing Library Name"
        raise LibrarySectionMissingError(description)

    def get_sections(self) -> list[LibrarySection]:
        """
        Gets an up-to-date list of all Sections for this LibraryType

        Returns:
            list[LibrarySection]: A current list of all Sections
            for this LibraryType

        """
        time.sleep(1)  # Slow devices need more time
        sections = self.plex_server.library.sections()

        description = (
            f"Section to find: {self.name} {self.library_type.get_value()}"
        )

        description = f"All Sections: {sections!s}"
        PlexUtilLogger.get_logger().debug(description)

        filtered_sections = [
            section
            for section in sections
            if LibraryType.is_eq(self.library_type, section)
        ]

        description = f"Filtered Sections: {filtered_sections!s}"
        PlexUtilLogger.get_logger().debug(description)
        return filtered_sections
