from sqlalchemy import select

from db.session import SessionLocal
from db.models import User, Match, MatchPlayer, User, Account, UserAccount

from core.logging_config import setup_logging


logger = setup_logging('collector')

async def update_db(parsed_battlelog, request_tag):
    async with SessionLocal() as session:
        async with session.begin():
            account = await session.scalar(
                select(Account)
                .where(Account.player_tag == request_tag)
            )
            filtered_battlelog = [
                b for b in parsed_battlelog
                if account.last_match_saved is None or b['game_dt'] > account.last_match_saved
            ]

            if filtered_battlelog:
                matches = [
                    Match(
                        match_time=battle['game_dt'],
                        game_mode=battle['game_mode'],
                        game_map=battle['game_map'],
                        result=battle['result'],
                        game_type=battle['game_type'],
                        players=[
                            MatchPlayer(**p) for p in battle['players']
                        ]
                    )
                    for battle in filtered_battlelog
                ]

                session.add_all(matches)
                logger.info(f'adding {len(matches)} matches for player {request_tag}')

                account.last_match_saved = max(
                    b['game_dt'] for b in filtered_battlelog
                )
            else:
                logger.info(f'no new matches for player {request_tag}')