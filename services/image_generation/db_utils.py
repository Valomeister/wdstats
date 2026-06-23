import asyncio
from collections import defaultdict

from db.session import SessionLocal
from repositories.stats_repository import StatsRepository

REQUIRED_MODES = {"brawlBall", "gemGrab", "heist", "hotZone", "knockout", "bounty"}

async def get_ranked_stats(tag):
    async with SessionLocal() as session:
        repo = StatsRepository(session)
        return await repo.get_stats(tag, 'soloRanked')

async def get_ranked_stats_by_ranks(tag):
    async with SessionLocal() as session:
        repo = StatsRepository(session)
        return await repo.get_ranked_stats_by_ranks(tag)

async def get_top_ranked_brawlers(tag, lim):
    async with SessionLocal() as session:
        repo = StatsRepository(session)
        return await repo.get_top_ranked_brawlers(tag, lim=lim)

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

async def get_top_ranked_brawlers_by_modes(tag):
    async with SessionLocal() as session:
        repo = StatsRepository(session)
        top_ranked_brawlers_by_modes =  await repo.get_top_ranked_brawlers_by_modes(tag, lim=3)

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

async def get_overall_stats(tag):
    async with SessionLocal() as session:
        repo = StatsRepository(session)
        return await repo.get_stats(tag)

async def get_matches(tag):
    async with SessionLocal() as session:
        repo = StatsRepository(session)
        return await repo.get_matches(tag, limit=10000000) # arbitrary large limit to fetch all

async def fetch_data_for_main_ranked(tag):
    ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers = await asyncio.gather(
        get_ranked_stats(tag),
        get_ranked_stats_by_ranks(tag),
        get_top_ranked_brawlers(tag, lim=5),
    )

    return ranked_stats, ranked_stats_by_ranks, top_ranked_brawlers

async def fetch_data_for_ranked_by_modes(tag):
    ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes = await asyncio.gather(
        get_ranked_stats(tag),
        get_ranked_stats_by_modes(tag),
        get_top_ranked_brawlers_by_modes(tag),
    )

    return ranked_stats, ranked_stats_by_modes, top_ranked_brawlers_by_modes

async def fetch_data_for_ranked_by_brawlers(tag):
    ranked_stats, top_ranked_brawlers = await asyncio.gather(
        get_ranked_stats(tag),
        get_top_ranked_brawlers(tag, lim=1000), # arbitrary lim grater than the amount of brawlers
    )

    return ranked_stats, top_ranked_brawlers

async def fetch_data_for_matches(tag):
    overall_stats, matches = await asyncio.gather(
        get_overall_stats(tag),
        get_matches(tag), # arbitrary lim grater than the amount of brawlers
    )

    return overall_stats, matches
