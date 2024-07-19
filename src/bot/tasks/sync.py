from datetime import datetime
from discord.ext import tasks
from discord import AutoShardedClient
from src.base.config import config
from src.utils.logger import logger
from traceback import format_exc

ROLE_SYNC_SEC = 24 * 60 * 60  # 24hrs

# Key: days to get role; Value: role id
ROLE_MAP = {
    7: 755080871480000593,
    30: 5080215536992347,
}


@tasks.loop(seconds=ROLE_SYNC_SEC)
async def sync_roles(bot: AutoShardedClient):
    try:
        logger.info("Role sync starting...")

        members = bot.get_guild(config.home_server).members
        assert members, "Members is none"

        logger.debug(f"Syncing roles for {len(members)} members")
        now = datetime.now().replace(tzinfo=None)

        for member in members:
            if member.bot:
                continue

            joined_at = member.joined_at.replace(tzinfo=None)
            member_for = now - joined_at
            logger.debug(f"{member.name} has been here for {member_for.days} days")

            # TODO: Implement role sync logic, wait for benny's approval on the idea first

    except Exception as e:
        format_exc()
        logger.error(f"An error has occured: {e}")
