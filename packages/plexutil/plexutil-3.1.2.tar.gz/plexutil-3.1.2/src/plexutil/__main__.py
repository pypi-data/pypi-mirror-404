import sys
import time

from plexapi.exceptions import Unauthorized

from plexutil.core.auth import Auth
from plexutil.core.library_factory import LibraryFactory
from plexutil.core.prompt import Prompt
from plexutil.enums.user_request import UserRequest
from plexutil.exception.bootstrap_error import BootstrapError
from plexutil.exception.library_illegal_state_error import (
    LibraryIllegalStateError,
)
from plexutil.exception.library_op_error import LibraryOpError
from plexutil.exception.library_poll_timeout_error import (
    LibraryPollTimeoutError,
)
from plexutil.exception.library_section_missing_error import (
    LibrarySectionMissingError,
)
from plexutil.exception.unexpected_argument_error import (
    UnexpectedArgumentError,
)
from plexutil.exception.user_error import UserError
from plexutil.plex_util_logger import PlexUtilLogger
from plexutil.util.file_importer import FileImporter
from plexutil.util.icons import Icons
from plexutil.util.plex_ops import PlexOps


def main() -> None:
    try:
        bootstrap_paths_dto = FileImporter.bootstrap()
        user_request = Prompt.confirm_user_request()
        try:
            plex_resources = Auth.get_resources(bootstrap_paths_dto)
        except Unauthorized:
            description = f"{Icons.WARNING} Reauthentication required\n"
            PlexUtilLogger.get_logger().warning(description)
            time.sleep(1)
            bootstrap_paths_dto.private_key_dir.unlink(missing_ok=True)
            bootstrap_paths_dto.public_key_dir.unlink(missing_ok=True)
            bootstrap_paths_dto.token_dir.unlink(missing_ok=True)
            plex_resources = Auth.get_resources(bootstrap_paths_dto)

        plex_server = Prompt.confirm_server(
            plex_resources=plex_resources
        ).connect()

        if user_request is UserRequest.SETTINGS:
            PlexOps.set_server_settings(plex_server=plex_server)
        else:
            library = LibraryFactory.get(
                user_request=user_request,
                plex_server=plex_server,
                bootstrap_paths_dto=bootstrap_paths_dto,
            )
            library.do()

    except SystemExit as e:
        if e.code == 0:
            description = "Successful System Exit"
            PlexUtilLogger.get_logger().debug(description)
        else:
            description = (
                f"\n{Icons.BANNER_LEFT}Unexpected Error"
                f"{Icons.BANNER_RIGHT}\n{e!s}"
            )
            PlexUtilLogger.get_logger().exception(description)
            raise

    except UserError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}User Error{Icons.BANNER_RIGHT}\n{e!s}"
        )
        PlexUtilLogger.get_logger().error(description)
        sys.exit(1)

    except LibraryIllegalStateError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}Library Illegal State Error"
            f"{Icons.BANNER_RIGHT}\n{e!s}"
        )
        PlexUtilLogger.get_logger().error(description)
        sys.exit(1)

    except LibraryOpError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}Library Operation Error"
            f"{Icons.BANNER_RIGHT}\n{e!s}"
        )
        PlexUtilLogger.get_logger().error(description)
        sys.exit(1)

    except LibraryPollTimeoutError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}Library Poll Tiemout Error"
            f"{Icons.BANNER_RIGHT}\n{e!s}"
        )
        PlexUtilLogger.get_logger().error(description)
        sys.exit(1)

    except LibrarySectionMissingError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}Library Not Found Error"
            f"{Icons.BANNER_RIGHT}\n{e!s}"
        )
        PlexUtilLogger.get_logger().error(description)
        sys.exit(1)

    except UnexpectedArgumentError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}User Argument Error{Icons.BANNER_RIGHT}\n"
            "These arguments are unrecognized: \n"
        )
        for argument in e.args[0]:
            description += "-> " + argument + "\n"
        PlexUtilLogger.get_logger().error(description)
        sys.exit(1)

    # No regular logger can be expected to be initialized
    except BootstrapError as e:
        description = (
            f"\n{Icons.BANNER_LEFT}Program Initialization Error"
            f"{Icons.BANNER_RIGHT}\n{e!s}"
        )
        e.args = (description,)
        raise

    except Exception as e:  # noqa: BLE001
        description = (
            f"\n{Icons.BANNER_LEFT}Unexpected Error{Icons.BANNER_RIGHT}\n{e!s}"
        )
        PlexUtilLogger.get_logger().exception(description)


if __name__ == "__main__":
    main()
