from db.session import SessionLocal

from repositories.stats_repository import StatsRepository

import asyncio




async def main():
    session = SessionLocal()
    stats_repo = StatsRepository(session)
    tag = '#2VP29CCVUQ'
    print(await stats_repo.get_stats(tag, 'ranked'))
    # print(await stats_repo.get_ranked_stats_by_ranks(tag))
    # print(await stats_repo.get_ranked_stats_by_modes(tag))
    # print(await stats_repo.get_top_ranked_brawlers(tag))
    # print(await stats_repo.get_top_ranked_brawlers_by_modes(tag))
    # print(await stats_repo.get_matches(tag, limit=20, offset=30))
    # print(await stats_repo.count_matches(tag))


    await session.close()

asyncio.run(main())