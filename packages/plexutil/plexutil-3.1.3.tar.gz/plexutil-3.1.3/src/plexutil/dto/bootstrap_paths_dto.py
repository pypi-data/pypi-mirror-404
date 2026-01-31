from dataclasses import dataclass
from pathlib import Path


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class BootstrapPathsDTO:
    auth_dir: Path
    log_dir: Path
    public_key_dir: Path
    private_key_dir: Path
    token_dir: Path
    plexutil_playlists_db_dir: Path
