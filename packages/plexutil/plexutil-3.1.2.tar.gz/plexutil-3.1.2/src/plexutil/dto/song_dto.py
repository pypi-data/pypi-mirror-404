from dataclasses import dataclass


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class SongDTO:
    artist: str = ""
    title: str = ""

    def __str__(self) -> str:
        return f"{self.artist} - {self.title}"
