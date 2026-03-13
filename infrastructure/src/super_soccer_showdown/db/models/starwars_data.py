from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base


class StarWarsData(Base):
    __tablename__ = "starwars_data"

    swapi_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    height_cm: Mapped[float] = mapped_column(sa.Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(sa.Float, nullable=False)
    power: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    team_participation: Mapped[list["StarWarsTeamComposition"]] = relationship(
        "StarWarsTeamComposition",
        back_populates="player",
        cascade="all, delete-orphan",
    )
