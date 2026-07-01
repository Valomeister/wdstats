"""
Service for stats_repository.
Distinct session for each request for async (asyncio.gather(...))
"""
import json
import os
from collections import defaultdict

from dotenv import load_dotenv

from db.session import SessionLocal
from image_generation.layout_config import REQUIRED_MODES
from repositories.stats_repository import StatsRepository

import redis.asyncio as redis


load_dotenv()


redis_client = redis.from_url(
    os.getenv('REDIS_URL'),
    decode_responses=False
)

CACHE_TTL = 120


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
            ranked_stats_by_modes = await repo.get_stats_by_modes(tag, 'soloRanked')

        ranked_stats_by_modes_dict = {i[0]: i[1:] for i in ranked_stats_by_modes}
        result = {
            mode: ranked_stats_by_modes_dict.get(mode, (0, 0, 0, 0))
            for mode in REQUIRED_MODES
        }

        return result

    @staticmethod
    async def get_ladder_stats_by_modes(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            ladder_stats_by_modes = await repo.get_stats_by_modes(tag, 'ranked')

        ladder_stats_by_modes_dict = {i[0]: i[1:] for i in ladder_stats_by_modes}

        return ladder_stats_by_modes_dict

    @staticmethod
    async def get_top_ranked_brawlers_by_modes(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            top_ranked_brawlers_by_modes = await repo.get_top_brawlers_by_modes(tag, 'soloRanked', lim=3)

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
    async def get_top_ladder_brawlers_by_modes(tag):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            top_ranked_brawlers_by_modes = await repo.get_top_brawlers_by_modes(tag, 'ranked', lim=3)

        top_brawlers_dict = defaultdict(list)

        for el in top_ranked_brawlers_by_modes:
            mode, brawler, stats = el[0], el[1], el[2:]
            top_brawlers_dict[mode].append([brawler, *stats])

        # fill in if there are fewer than 3 brawlers
        for mode, items in top_brawlers_dict.items():
            last_rank = items[-1][-1] if items else 0
            for i in range(last_rank + 1, 4):
                items.append(['PLACEHOLDER', 0, 0, 0, 0, i])

        return top_brawlers_dict

    @staticmethod
    async def get_overall_stats(tag):
        key = f'overall_stats:{tag}'

        cached_overall_stats = await redis_client.get(key)

        if cached_overall_stats is not None:
            print("returning cache for get_overall_stats()")
            return json.loads(cached_overall_stats)
        print("returning from db for get_overall_stats()")

        async with SessionLocal() as session:
            repo = StatsRepository(session)
            stats = await repo.get_stats(tag)

            await redis_client.set(
                key,
                json.dumps(list(stats)),
                ex=CACHE_TTL
            )

            return stats

    @staticmethod
    async def get_matches(tag, limit, offset):
        async with SessionLocal() as session:
            repo = StatsRepository(session)
            return await repo.get_matches(tag, limit=limit, offset=offset)

    @staticmethod
    async def count_matches(tag):
        key = f'matches_count:{tag}'

        cached_matches_count = await redis_client.get(key)

        if cached_matches_count is not None:
            print("returning cache for count_matches()")
            return int(cached_matches_count)
        print("returning from db for count_matches()")

        async with SessionLocal() as session:
            repo = StatsRepository(session)
            count = await repo.count_matches(tag)

            await redis_client.set(
                key,
                count,
                ex=CACHE_TTL
            )

            return count

    @staticmethod
    async def get_detailed_matches(tag, limit, offset):
        keys = [
            f"detailed_matches:{tag}:{i}"
            for i in range(offset, offset + limit)
        ]

        cached_matches = await redis_client.mget(keys)

        if all(cached_matches):
            print("returning cache for get_detailed_matches()")

            return [
                json.loads(item)
                for item in cached_matches
            ]
        print("returning from db for get_detailed_matches()")

        async with SessionLocal() as session:
            repo = StatsRepository(session)
            padding = 9
            padded_offset = max(0, offset - padding)
            padded_limit = padding * 2 + 1

            matches = await repo.get_detailed_matches(tag, limit=padded_limit, offset=padded_offset)
            matches = [serialize_match(match) for match in matches]

            pipe = redis_client.pipeline()

            for i, match in enumerate(matches):
                key = (
                    f"detailed_matches:{tag}:{padded_offset + i}"
                )

                await pipe.set(
                    key,
                    json.dumps(match),
                    ex=CACHE_TTL
                )

            await pipe.execute()

            return matches


def serialize_match(row):
    match, *extra = row

    return [
        {
            "id": match.id,
            "match_time": match.match_time.isoformat(),
            "game_type": match.game_type,
            "game_mode": match.game_mode,
            "game_map": match.game_map,
            "result": match.result,

            "players": [
                {
                    "player_tag": p.player_tag,
                    "brawler": p.brawler,
                    "team": p.team,
                    "player_nickname": p.player_nickname,
                    "trophies": p.trophies,
                    "trophy_change": p.trophy_change,
                }
                for p in match.players
            ],
        },
        *extra
    ]