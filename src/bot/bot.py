import os

from cogwatch import watch
from discord import Intents, CustomActivity
from discord.ext.commands import AutoShardedBot

from src.base.config import config
from src.bot.tasks.sync import sync_roles
from src.utils.logger import logger


class Bot(AutoShardedBot):
    """Main bot class"""

    def __init__(self, **options) -> None:
        intents = Intents.default()
        intents.guild_messages = True
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="g.", intents=intents, **options)

    async def load_extensions(self):
        """Loads all the extensions / cogs in the ./cogs folder"""
        for f in os.listdir("./src/bot/cogs"):
            if f.endswith(".py"):
                await self.load_extension("src.bot.cogs." + f[:-3])
                logger.info(f"Successfully loaded cog: {f[:-3]}")

    async def start(self):
        """Starts the bot"""
        try:
            logger.info("Starting the bot")
            await super().start(config.token, reconnect=True)
        except Exception as e:
            raise Exception(f"Bot failed to startup: {e}")

    async def setup_hook(self) -> None:
        """Hook for when the bot is being set up, used to load all the extensions"""
        await self.load_extensions()
        await self.tree.sync()

    @watch(path="src/bot/cogs", colors=True)
    async def on_ready(self):
        """Called when the bot is ready"""
        try:
            activity: str = config.bot_activity
            activity = activity.replace("{shard_count}", str(self.shard_count))
            logger.debug(f"Activity: {activity}")
            custom_activity = CustomActivity(activity)
            await self.change_presence(
                status=config.bot_status, activity=custom_activity
            )
            logger.info("Set status completed")
        except Exception as e:
            logger.error(f"Error setting presence: {e}")

        # Finish
        logger.info("Bot is ready")

        # Start tasks
        # TODO make this more dynamic by using the same logic from cog loading
        sync_roles.start(self)
