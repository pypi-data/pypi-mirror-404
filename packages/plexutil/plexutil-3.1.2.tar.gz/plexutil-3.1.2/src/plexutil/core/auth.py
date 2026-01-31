import uuid
from importlib.metadata import PackageNotFoundError, version

from plexapi.myplex import MyPlexAccount, MyPlexJWTLogin, MyPlexResource

from plexutil.dto.bootstrap_paths_dto import BootstrapPathsDTO
from plexutil.exception.auth_error import AuthError
from plexutil.plex_util_logger import PlexUtilLogger
from plexutil.static import Static
from plexutil.util.file_importer import FileImporter
from plexutil.util.icons import Icons


class Auth(Static):
    @staticmethod
    def get_resources(
        bootstrap_paths_dto: BootstrapPathsDTO,
    ) -> list[MyPlexResource]:
        """
        Login to Plex and returns a list of all the available Plex Resources
        (Servers and Clients)

        *Deletes existing keys/token and terminates early if unable to refresh
        existing token

        Args:
            bootstrap_paths_dto (BootstrapPathsDTO): Used to locate auth dir

        Returns:
            list[MyPlexResource]: Plex Resources
        """
        private_key_path = bootstrap_paths_dto.private_key_dir
        public_key_path = bootstrap_paths_dto.public_key_dir
        token_path = bootstrap_paths_dto.token_dir

        try:
            plexutil_version = version("plexutil")

        except PackageNotFoundError:
            pyproject = FileImporter.get_pyproject()
            plexutil_version = pyproject["project"]["version"]

        headers = {}
        headers["X-Plex-Client-Identifier"] = f"{uuid.uuid4()!s}"
        headers["X-Plex-Product"] = f"Plexutil {plexutil_version} via Plexapi"
        headers["X-Plex-Version"] = plexutil_version

        if (
            not private_key_path.exists()
            or not public_key_path.exists()
            or not token_path.exists()
        ):
            description = "Auth corrupt or not initialized"
            PlexUtilLogger.get_logger().debug(description)
            jwt_login = MyPlexJWTLogin(oauth=True, headers=headers)
            jwt_login.generateKeypair(
                keyfiles=(f"{private_key_path!s}", f"{public_key_path!s}"),
                overwrite=True,
            )
            jwt_login.run()
            url = jwt_login.oauthUrl()
            description = (
                f"\n{Icons.BANNER_LEFT}Login{Icons.BANNER_RIGHT}\n"
                f"Login {Icons.CHEVRON_RIGHT} {url}\n"
            )
            PlexUtilLogger.get_console_logger().info(description)
            jwt_login.waitForLogin()
            token = jwt_login.jwtToken

            if isinstance(token, str):
                description = "Successful Login. Saving Token..."
                PlexUtilLogger.get_logger().debug(description)
                FileImporter.save_jwt(
                    bootstrap_paths_dto.token_dir,
                    token,
                    headers["X-Plex-Client-Identifier"],
                )
            else:
                description = "Did not receive a token"
                raise AuthError(description)

        description = "Auth exists"
        PlexUtilLogger.get_logger().debug(description)
        token, _ = FileImporter.get_jwt(bootstrap_paths_dto.token_dir)
        account = MyPlexAccount(token=token)
        resources = account.resources()
        description = f"Available Resources: {resources}"
        PlexUtilLogger.get_logger().debug(description)
        return resources
