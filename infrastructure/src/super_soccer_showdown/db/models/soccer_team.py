from __future__ import annotations

import sqlalchemy as sa
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base
from super_soccer_showdown.db.models.enums import UniverseEnum

if TYPE_CHECKING:
    from super_soccer_showdown.db.models.pokemon_team_composition import PokemonTeamComposition
    from super_soccer_showdown.db.models.soccer_match import SoccerMatch
    from super_soccer_showdown.db.models.starwars_team_composition import StarWarsTeamComposition
    from super_soccer_showdown.db.models.user import User


class SoccerTeam(Base):
    __tablename__ = "soccer_team"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    universe: Mapped[UniverseEnum] = mapped_column(
        sa.Enum(
            UniverseEnum,
            name="universeenum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    owner_user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("app_user.id"), nullable=False)
    owner_user: Mapped["User"] = relationship("User", back_populates="soccer_teams")
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
