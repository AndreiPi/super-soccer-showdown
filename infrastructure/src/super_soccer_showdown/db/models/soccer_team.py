from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base
from super_soccer_showdown.db.models.enums import UniverseEnum


class SoccerTeam(Base):
    __tablename__ = "soccer_team"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    universe: Mapped[UniverseEnum] = mapped_column(sa.Enum(UniverseEnum), nullable=False)

    starwars_players: Mapped[list["StarWarsTeamComposition"]] = relationship(
        "StarWarsTeamComposition",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    pokemon_players: Mapped[list["PokemonTeamComposition"]] = relationship(
        "PokemonTeamComposition",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    as_starwars_in_matches: Mapped[list["SoccerMatch"]] = relationship(
        "SoccerMatch",
        back_populates="starwars_team",
        foreign_keys="SoccerMatch.starwars_team_id",
    )
    as_pokemon_in_matches: Mapped[list["SoccerMatch"]] = relationship(
        "SoccerMatch",
        back_populates="pokemon_team",
        foreign_keys="SoccerMatch.pokemon_team_id",
    )
