from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime

from db.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    player_tag: Mapped[str] = mapped_column(
        unique=True,
        index=True
    )

    nickname: Mapped[str | None]

    last_match_saved: Mapped[datetime | None]

    users: Mapped[list["User"]] = relationship(
        secondary="user_accounts",
        back_populates="accounts"
    )
