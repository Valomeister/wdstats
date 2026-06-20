from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Match, MatchPlayer

VICTORIES_STMT = (
    func.count(Match.id).filter(
        or_(
            and_(Match.result == 1, MatchPlayer.team == 1),
            and_(Match.result == -1, MatchPlayer.team == -1)
        )
    ).label('victories')
)
DRAW_STMT = (
    func.count(Match.id).filter(
        Match.result == 0
    ).label('draws')
)
LOSSES_STMT = (
    func.count(Match.id).filter(
        or_(
            and_(Match.result == -1, MatchPlayer.team == 1),
            and_(Match.result == 1, MatchPlayer.team == -1)
        )
    ).label('losses')
)

class StatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_ranked_stats(self, player_tag):
        stmt = (
            select(
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(
                and_(MatchPlayer.player_tag == player_tag, Match.game_type == 'soloRanked')
            )
        )

        result = await self.session.execute(stmt)

        return result.first()

    async def get_ranked_stats_by_ranks(self, player_tag):
        stmt = (
            select(
                MatchPlayer.trophies,
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(
                and_(MatchPlayer.player_tag == player_tag, Match.game_type == 'soloRanked')
            )
            .group_by(MatchPlayer.trophies)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def get_ranked_stats_by_modes(self, player_tag):
        stmt = (
            select(
                Match.game_mode,
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(
                and_(MatchPlayer.player_tag == player_tag, Match.game_type == 'soloRanked')
            )
            .group_by(Match.game_mode)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def get_top_ranked_brawlers(self, player_tag, lim=3):
        stmt = (
            select(
                MatchPlayer.brawler,
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(
                and_(MatchPlayer.player_tag == player_tag, Match.game_type == 'soloRanked')
            )
            .group_by(MatchPlayer.brawler)
            .order_by(func.count(MatchPlayer.brawler).desc())
            .limit(lim)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def get_top_ranked_brawlers_by_modes(self, player_tag, lim=3):
        stats_subq = (
            select(
                Match.game_mode,
                MatchPlayer.brawler,
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(
                and_(MatchPlayer.player_tag == player_tag, Match.game_type == 'soloRanked')
            )
            .group_by(Match.game_mode, MatchPlayer.brawler)
        ).subquery()

        ranked_subq = (
            select(
                stats_subq,
                func.row_number().over(
                    partition_by=stats_subq.c.game_mode,
                    order_by=stats_subq.c.matches.desc()
                ).label("rn")
            )
        ).subquery()

        stmt = (
            select(ranked_subq)
            .where(ranked_subq.c.rn <= 3)
            .order_by(ranked_subq.c.game_mode, ranked_subq.c.rn)
        )

        result = await self.session.execute(stmt)

        return result.all()

