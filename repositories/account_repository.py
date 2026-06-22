from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Account


class AccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tag(self, tag):
        result = await self.session.execute(
            select(Account)
            .where(Account.player_tag == tag)
        )

        return result.scalar_one_or_none()

    async def create(self, tag, nickname=None):
        account = Account(
            player_tag=tag,
            nickname=nickname
        )

        self.session.add(account)
        await self.session.commit()

        return account