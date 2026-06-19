from sqlalchemy import select

from db.models import Account
from db.session import SessionLocal
from collector.parser import get_raw_from_api, parse_battlelog
from collector.api import BrawlAPI, api_context
from collector.db_updater import update_db

from dotenv import load_dotenv
import os

from core.logging_config import setup_logging


logger = setup_logging('collector')

load_dotenv()
API_TOKEN = os.getenv('BS_API_TOKEN')

async def parse_and_update_player(api_client, request_tag):
    code, raw_json = await get_raw_from_api(api_client, request_tag)
    if code != 200:
        logger.warning(f'Could not get matches of player {request_tag}: {code}, {raw_json}')
        return

    parsed_battlelog = parse_battlelog(raw_json, request_tag)

    await update_db(parsed_battlelog, request_tag)

async def collect_all_accounts():
    """
    This function is used to update all registered brawl accounts repeatedly
    """
    logger.info(f'started collecting all accounts')
    async with SessionLocal() as session:
        accounts = (
            await session.scalars(
                select(Account)
            )
        ).all()

    logger.info(f'{len(accounts)} accounts to collect')

    async with api_context(API_TOKEN) as api_client:
        for account in accounts:
            try:
                await parse_and_update_player(api_client, account.player_tag)
            except Exception as exc:
                logger.exception(f'Failed to collect player {account.player_tag}')


async def collect_account(player_tag):
    """
    This function is used to update a specific brawl account
    """
    logger.info(f'started collecting account of player {player_tag}')
    async with api_context(API_TOKEN) as api_client:
        try:
            await parse_and_update_player(api_client, player_tag)
        except Exception as exc:
            logger.exception(f'Failed to collect player {player_tag}')
            raise


