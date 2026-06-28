from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.util import parse_user_argument_for_enum

from db.session import SessionLocal
from db.models import User, Match, MatchPlayer, User, Account, UserAccount

from core.logging_config import setup_logging


logger = setup_logging('collector')

async def update_db(parsed_battlelog, request_tag):
    async with (SessionLocal() as session):
        async with session.begin():
            if not parsed_battlelog:
                logger.info(f'no parsed matches were provided for {request_tag}')
                return
            account = await session.scalar(
                select(Account)
                .where(Account.player_tag == request_tag)
            )
            stmt = (insert(Match)
                .values(
                    [
                        {
                            "match_time": battle['game_dt'],
                            "game_mode": battle['game_mode'],
                            "game_map": battle['game_map'],
                            "result": battle['result'],
                            "game_type": battle['game_type'],
                            "star_player": battle['star_player'],
                            "unique_hash": battle['unique_hash']
                        }
                        for battle in parsed_battlelog
                    ]
                )
                .on_conflict_do_update(
                    index_elements=["unique_hash"],
                    set_={
                        "unique_hash": Match.unique_hash,
                    },
                )
                .returning(
                    Match.id,
                    Match.unique_hash
                )
            )

            result = await session.execute(stmt)

            inserted_matches = result.all()

            match_ids = {
                unique_hash: match_id
                for match_id, unique_hash in inserted_matches
            }

            players = []

            for battle in parsed_battlelog:
                match_id = match_ids.get(battle['unique_hash'])

                if match_id is None:
                    continue

                for player in battle['players']:
                    players.append(
                        player | {'match_id': match_id}
                    )

            if players:
                stmt = (
                    insert(MatchPlayer)
                    .values(players)
                    .on_conflict_do_update(
                        index_elements=["match_id", "player_tag"],
                        set_={
                            "trophy_change": func.coalesce(
                                insert(MatchPlayer).excluded.trophy_change,
                                MatchPlayer.trophy_change,
                            )
                        },
                    )
                )

                await session.execute(stmt)

            account.last_match_saved = max(
                b['game_dt'] for b in parsed_battlelog
            )

            logger.info(f'added {len(inserted_matches)} matches for player {request_tag} ({account.nickname})')