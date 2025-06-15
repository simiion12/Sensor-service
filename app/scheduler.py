import asyncio
from datetime import datetime, time as dt_time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models import Device
import logging

logger = logging.getLogger(__name__)


async def reset_daily_coffee_count():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(Device).values(numbers_of_coffee=4)
            )
            await db.commit()
            logger.info(f"Reset coffee count for all devices to 4. Affected rows: {result.rowcount}")
    except Exception as e:
        logger.error(f"Error resetting daily coffee count: {e}")


async def calculate_seconds_until_midnight():
    now = datetime.now()
    midnight = datetime.combine(now.date().replace(day=now.day + 1), dt_time(0, 0, 0))
    return (midnight - now).total_seconds()


async def daily_scheduler():
    logger.info("Starting daily scheduler for coffee count reset")

    # Wait until midnight for first reset
    seconds_until_midnight = await calculate_seconds_until_midnight()
    logger.info(f"Waiting {seconds_until_midnight:.0f} seconds until midnight for first reset")
    await asyncio.sleep(seconds_until_midnight)

    while True:
        await reset_daily_coffee_count()
        # Wait 24 hours (86400 seconds) until next reset
        await asyncio.sleep(86400)


def start_scheduler():
    asyncio.create_task(daily_scheduler())