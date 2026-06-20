from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime

from db.base import Base


class Match(Base):
    __tablename__ = 'matches'

    id: Mapped[int] = mapped_column(primary_key=True)
    match_time: Mapped[datetime]
    game_mode: Mapped[str] = mapped_column(String(32))
    game_map: Mapped[str] = mapped_column(String(32))
    result: Mapped[int]
    game_type: Mapped[str] = mapped_column(String(32))
    unique_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    players: Mapped[List['MatchPlayer']] = relationship(back_populates='match')
