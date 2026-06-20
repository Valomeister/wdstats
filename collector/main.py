import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collector.service import collect_all_accounts
from core.logging_config import setup_logging


logger = setup_logging("collector")


async def main():

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        collect_all_accounts,
        trigger="interval",
        minutes=20,
        next_run_time=datetime.now()
    )

    scheduler.start()

    logger.info("collector scheduler started")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())