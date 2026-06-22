from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tg_with_accounts(self, tg_id):
        result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.accounts)
            )
            .where(User.tg_id == tg_id)
        )

        return result.scalar_one_or_none()

    async def create(self, tg_id, tg_username):
        user = User(
            tg_id=tg_id,
            tg_username=tg_username
        )

        self.session.add(user)
        await self.session.commit()

        return user