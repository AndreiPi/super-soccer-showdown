from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base


class PokemonData(Base):
    __tablename__ = "pokemon_data"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    pokeapi_id: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    height_cm: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(sa.Float, nullable=False)
    power: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    team_participation: Mapped[list["PokemonTeamComposition"]] = relationship(
        "PokemonTeamComposition",
        back_populates="player",
        cascade="all, delete-orphan",
    )
