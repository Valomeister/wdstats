from sqlalchemy import select, func, or_, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Match, MatchPlayer

VICTORIES_STMT = (
    func.count(Match.id).filter(
        or_(
            and_(
                Match.game_mode.in_(["soloShowdown", "duoShowdown", "trioShowdown"]),
                MatchPlayer.trophy_change > 0
            ),
            and_(
                Match.game_mode.notin_(["soloShowdown", "duoShowdown", "trioShowdown"]),
                or_(
                    and_(Match.result == 1, MatchPlayer.team == 1),
                    and_(Match.result == -1, MatchPlayer.team == -1)
                )
            ),

        )
    ).label('victories')
)

DRAW_STMT = (
    func.count(Match.id).filter(
        or_(
            and_(
                Match.game_mode.in_(["soloShowdown", "duoShowdown", "trioShowdown"]),
                or_(
                    MatchPlayer.trophy_change == 0,
                    MatchPlayer.trophy_change.is_(None) # todo add "UNKNOWN_STMT" for sd where trophy_change is None
                )
            ),
            and_(
                Match.game_mode.notin_(["soloShowdown", "duoShowdown", "trioShowdown"]),
                Match.result == 0
            ),

        )
    ).label('draws')
)

LOSSES_STMT  = (
    func.count(Match.id).filter(
        or_(
            and_(
                Match.game_mode.in_(["soloShowdown", "duoShowdown", "trioShowdown"]),
                MatchPlayer.trophy_change < 0
            ),
            and_(
                Match.game_mode.notin_(["soloShowdown", "duoShowdown", "trioShowdown"]),
                or_(
                    and_(Match.result == -1, MatchPlayer.team == 1),
                    and_(Match.result == 1, MatchPlayer.team == -1)
                )
            ),

        )
    ).label('losses')
)

class StatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(
            self,
            player_tag: str,
            game_type: str | None = None
    ):
        filters = [
            MatchPlayer.player_tag == player_tag
        ]

        if game_type is not None:
            filters.append(
                Match.game_type == game_type
            )

        stmt = (
            select(
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(*filters)
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

    async def get_ladder_stats_by_trophy_ranges(self, player_tag):
        trophy_range = (
            func.least(func.floor(MatchPlayer.trophies / 200), 15)
            .label('start')
        )

        stmt = (
            select(
                trophy_range,
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(
                and_(
                    MatchPlayer.player_tag == player_tag,
                    Match.game_type == 'ranked',
                    MatchPlayer.trophies < 3000
                )
            )
            .group_by(trophy_range)
            .order_by(trophy_range)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def get_stats_by_modes(
        self,
        player_tag,
        game_type: str | None = None
    ):
        filters = [
            MatchPlayer.player_tag == player_tag
        ]
        if game_type:
            filters.append(Match.game_type == game_type)

        stmt = (
            select(
                Match.game_mode,
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(*filters)
            .group_by(Match.game_mode)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def get_top_brawlers(
            self,
            player_tag,
            game_type: str | None = None,
            lim=3):
        filters = [MatchPlayer.player_tag == player_tag]
        if game_type:
            filters.append(Match.game_type == game_type)

        stmt = (
            select(
                MatchPlayer.brawler,
                func.count(Match.id).label('matches'),
                VICTORIES_STMT,
                DRAW_STMT,
                LOSSES_STMT
            )
            .join(MatchPlayer)
            .where(*filters)
            .group_by(MatchPlayer.brawler)
            .order_by(func.count(MatchPlayer.brawler).desc())
            .limit(lim)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def get_top_brawlers_by_modes(
        self,
        player_tag,
        game_type: str | None = None,
        lim=3
    ):
        filters = [
            MatchPlayer.player_tag == player_tag
        ]
        if game_type:
            filters.append(Match.game_type == game_type)

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
            .where(*filters)
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

    async def get_matches(self, player_tag, limit, offset=0):
        player = MatchPlayer

        relative_result = (
            case(
                (
                    Match.game_mode.in_(["soloShowdown", "duoShowdown", "trioShowdown"]),
                    Match.result
                ),
                else_=case(
                    (
                        and_(
                            Match.result == 1,
                            player.team == 1
                        ),
                        1
                    ),
                    (
                        and_(
                            Match.result == -1,
                            player.team == -1
                        ),
                        1
                    ),
                    (
                        Match.result == 0,
                        0
                    ),
                    else_=-1
                )
            )
        ).label("result")

        is_star_player = (
            (Match.star_player == player_tag)
            .label('is_star_player')
        )

        stmt = (
            select(
                Match.match_time,
                Match.game_mode,
                Match.game_type,
                is_star_player,
                relative_result,
                player.trophies,
                player.brawler,
                player.trophy_change
            )
            .join(player)
            .where(
                player.player_tag == player_tag
            )
            .order_by(
                Match.match_time.desc()
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def count_matches(self, player_tag):
        stmt = (
            select(
                func.count(MatchPlayer.id)
            )
            .where(
                MatchPlayer.player_tag == player_tag
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar()

    async def get_detailed_matches(self, player_tag, limit, offset=0):
        player = MatchPlayer

        relative_result = (
            case(
                (
                    and_(
                        Match.result == 1,
                        player.team == 1
                    ),
                    1
                ),
                (
                    and_(
                        Match.result == -1,
                        player.team == -1
                    ),
                    1
                ),
                (
                    Match.result == 0,
                    0
                ),
                else_=-1
            )
        ).label("result")

        is_star_player = (
            (Match.star_player == player_tag)
            .label("is_star_player")
        )

        stmt = (
            select(
                Match,
                relative_result,
                is_star_player,
                player.trophies,
                player.brawler,
            )
            .join(player)
            .where(
                player.player_tag == player_tag
            )
            .options(
                selectinload(Match.players)
                .load_only(
                    MatchPlayer.player_tag,
                    MatchPlayer.brawler,
                    MatchPlayer.team,
                    MatchPlayer.player_nickname,
                    MatchPlayer.trophies,
                    MatchPlayer.trophy_change
                )
            )
            .order_by(
                Match.match_time.desc()
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)

        return result.all()