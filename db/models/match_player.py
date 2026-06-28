from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class MatchPlayer(Base):
    __tablename__ = 'match_players'

    id: Mapped[int] = mapped_column(primary_key=True)
    team: Mapped[int]
    player_tag: Mapped[str] = mapped_column(String(32))
    player_nickname: Mapped[str] = mapped_column(String(32))
    brawler: Mapped[str] = mapped_column(String(32))
    trophies: Mapped[int]
    match_id: Mapped[int] = mapped_column(ForeignKey('matches.id'))
    trophy_change: Mapped[int] = mapped_column(nullable=True)

    match: Mapped['Match'] = relationship(back_populates='players')

    def __repr__(self):
        return (
            f"MatchPlayer("
            f"tag='{self.player_tag}', "
            f"nick='{self.player_nickname}', "
            f"team={self.team}, "
            f"relative_result={self.match.result * self.team}"
            f"brawler='{self.brawler}'"
            f")"
        )