"""
Service for stats_repository.
Distinct session for each request for async (asyncio.gather(...))
"""
from collections import defaultdict

from db.session import SessionLocal
from image_generation.layout_config import REQUIRED_MODES
from repositories.stats_repository import StatsRepository


class StatsService:
    @staticmethod
    async def get_ranked_stats(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_stats(tag, 'soloRanked')

    @staticmethod
    async def get_ladder_stats(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_stats(tag, 'ranked')

    @staticmethod
    async def get_ranked_stats_by_ranks(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_ranked_stats_by_ranks(tag)

    @staticmethod
    async def get_ladder_stats_by_trophy_ranges(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_ladder_stats_by_trophy_ranges(tag)

    @staticmethod
    async def get_top_ranked_brawlers(tag, lim):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_top_brawlers(tag, game_type='soloRanked', lim=lim)

    @staticmethod
    async def get_top_ladder_brawlers(tag, lim):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_top_brawlers(tag, game_type='ranked', lim=lim)

    @staticmethod
    async def get_ranked_stats_by_modes(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            ranked_stats_by_modes = await repo.get_ranked_stats_by_modes(tag)

        ranked_stats_by_modes_dict = {i[0]: i[1:] for i in ranked_stats_by_modes}
        result = {
            mode: ranked_stats_by_modes_dict.get(mode, (0, 0, 0, 0))
            for mode in REQUIRED_MODES
        }

        return result

    @staticmethod
    async def get_top_ranked_brawlers_by_modes(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            top_ranked_brawlers_by_modes = await repo.get_top_ranked_brawlers_by_modes(tag, lim=3)

        top_brawlers_dict = defaultdict(list)

        for el in top_ranked_brawlers_by_modes:
            mode, brawler, stats = el[0], el[1], el[2:]
            top_brawlers_dict[mode].append([brawler, *stats])

        top_brawlers_dict = {
            mode: top_brawlers_dict.get(mode, [])
            for mode in REQUIRED_MODES
        }

        # fill in if there are fewer than 3 brawlers
        for mode, items in top_brawlers_dict.items():
            last_rank = items[-1][-1] if items else 0
            for i in range(last_rank + 1, 4):
                items.append(['PLACEHOLDER', 0, 0, 0, 0, i])

        return top_brawlers_dict

    @staticmethod
    async def get_overall_stats(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_stats(tag)

    @staticmethod
    async def get_matches(tag, limit, offset):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_matches(tag, limit=limit, offset=offset)

    @staticmethod
    async def count_matches(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.count_matches(tag)

    @staticmethod
    async def get_detailed_matches(tag, limit, offset):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_detailed_matches(tag, limit=limit, offset=offset)

