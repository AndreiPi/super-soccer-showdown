from __future__ import annotations

import sqlalchemy as sa
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base
from super_soccer_showdown.db.models.enums import PositionEnum

if TYPE_CHECKING:
    from super_soccer_showdown.db.models.pokemon_data import PokemonData
    from super_soccer_showdown.db.models.soccer_team import SoccerTeam


class PokemonTeamComposition(Base):
    __tablename__ = "pokemon_team_composition"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("soccer_team.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("pokemon_data.pokeapi_id"), nullable=False)
    position: Mapped[PositionEnum] = mapped_column(
        sa.Enum(
            PositionEnum,
            name="positionenum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    team: Mapped["SoccerTeam"] = relationship("SoccerTeam", back_populates="pokemon_players")
    player: Mapped["PokemonData"] = relationship("PokemonData", back_populates="team_participation")
