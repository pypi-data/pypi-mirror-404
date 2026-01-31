from plexutil.dto.song_dto import SongDTO
from plexutil.model.song_entity import SongEntity


class SongMapper:
    def get_dto(self, song_entity: SongEntity) -> SongDTO:
        name = str(song_entity.name).split(" - ")
        return SongDTO(
            artist=str(name[0]),
            title=str(name[1]),
        )

    def get_entity(self, song_dto: SongDTO) -> SongEntity:
        return SongEntity(name=str(song_dto))
