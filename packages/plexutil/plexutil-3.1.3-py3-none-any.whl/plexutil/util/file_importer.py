from __future__ import annotations

import ctypes.wintypes
import json
import os
import platform
from datetime import UTC, datetime, timedelta
from pathlib import Path

import toml

if platform.system() == "Windows":
    import win32evtlog  # pyright: ignore # noqa: PGH003
    import win32evtlogutil  # pyright: ignore # noqa: PGH003

import yaml

from plexutil.dto.bootstrap_paths_dto import BootstrapPathsDTO
from plexutil.plex_util_logger import PlexUtilLogger
from plexutil.static import Static


class FileImporter(Static):
    encoding = "utf-8"

    @staticmethod
    def get_project_root() -> Path:
        """
        Gets the root of this project

        Returns:
            pathlib.Path: The project's root
        """
        return Path(__file__).parent.parent.parent

    @staticmethod
    def get_logging_config(logging_config_path: Path) -> dict:
        with logging_config_path.open(
            "r", errors="strict", encoding=FileImporter.encoding
        ) as file:
            return yaml.safe_load(file)

    @staticmethod
    def get_pyproject() -> dict:
        return toml.load(
            FileImporter.get_project_root().parent / "pyproject.toml"
        )

    @staticmethod
    def get_jwt(location: Path) -> tuple[str, str]:
        with location.open(encoding=FileImporter.encoding) as file:
            data = json.load(file)
            return (data["token"], data["X-Plex-Client-Identifier"])

    @staticmethod
    def save_jwt(location: Path, token: str, client_dentifier: str) -> None:
        data = {}
        data["token"] = token
        data["X-Plex-Client-Identifier"] = client_dentifier
        with location.open(
            "w", errors="strict", encoding=FileImporter.encoding
        ) as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    @staticmethod
    def bootstrap() -> BootstrapPathsDTO:
        try:
            home_folder = Path()
            system = platform.system()

            if system == "Windows":
                csidl_personal = 5
                shgfp_type_current = 0

                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(  # pyright: ignore # noqa: PGH003
                    None, csidl_personal, None, shgfp_type_current, buf
                )
                home_folder = buf.value or ""
                if not home_folder:
                    description = "Could not locate Documents folder"
                    raise FileNotFoundError(description)

            elif system == "Linux":
                home_folder = os.getenv("HOME") or ""
                session = os.getenv("XDG_SESSION_TYPE") or ""
                session = session.lower()

            else:
                description = f"Unsupported OS: {system}"
                raise OSError(description)

            plexutil_dir = Path(home_folder) / "plexutil"
            auth_dir = plexutil_dir / "auth"
            log_dir = plexutil_dir / "log"

            plexutil_dir.mkdir(exist_ok=True)
            auth_dir.mkdir(exist_ok=True)
            log_dir.mkdir(exist_ok=True)

            # Delete logs older than 30 days
            for log_file in log_dir.iterdir():
                if not log_file.is_file():
                    continue
                log_date = datetime.fromtimestamp(
                    log_file.stat().st_ctime, tz=UTC
                )
                log_limit_date = datetime.now(tz=UTC) - timedelta(days=30)
                if log_date < log_limit_date:
                    log_file.unlink()

            log_config_file_path = (
                FileImporter.get_project_root()
                / "plexutil"
                / "config"
                / "log_config.yaml"
            )

            log_config = FileImporter.get_logging_config(log_config_file_path)

            PlexUtilLogger(log_dir, log_config)

            description = f"Bootstrap successful. Dir -> {plexutil_dir!s}"
            PlexUtilLogger.get_logger().debug(description)

            return BootstrapPathsDTO(
                auth_dir=auth_dir,
                log_dir=log_dir,
                private_key_dir=auth_dir / "private.key",
                public_key_dir=auth_dir / "public.key",
                token_dir=auth_dir / "token.json",
                plexutil_playlists_db_dir=Path.cwd() / "playlists.db",
            )

        except Exception as e:
            if platform.system() == "Windows":
                win32evtlogutil.ReportEvent(  # pyright: ignore # noqa: PGH003
                    "plexutil",
                    eventID=1,
                    eventType=win32evtlog.EVENTLOG_ERROR_TYPE,  # pyright: ignore # noqa: PGH003
                    strings=[""],
                )
            elif platform.system() == "Linux":
                import syslog  # noqa: PLC0415

                syslog.syslog(str(e))
            raise
