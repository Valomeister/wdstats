from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int]
    tg_username: Mapped[str | None] = mapped_column(String(64))

    accounts: Mapped[list["Account"]] = relationship(
        secondary="user_accounts",
        back_populates="users"
    )

