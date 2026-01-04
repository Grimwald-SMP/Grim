import os

from cogwatch import watch
from discord import Intents, CustomActivity
from discord.ext.commands import AutoShardedBot

from src.base.config import config
from src.bot.tasks.sync import sync_roles
from src.utils.logger import logger
from src.database.database import database

from src.bot.views.seasonpoll import PollView


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

    async def load_views(self):
        view_records = database.views.find({})
        for record in view_records:
            logger.info(f"Loading view `{record['view_type']}` with ID {record['message_id']}")
            if record["view_type"] == "seasonpoll":
                view = PollView(message_id=record["message_id"], state=record["state"])
                self.add_view(view, message_id=record["message_id"])


    async def start(self):
        """Starts the bot"""
        try:
            logger.info("Starting the bot")
            if not config.token:
                raise ValueError("Bot token is not set in the configuration.")
            await super().start(config.token, reconnect=True)
        except Exception as e:
            raise Exception(f"Bot failed to startup: {e}")

    async def setup_hook(self) -> None:
        """Hook for when the bot is being set up, used to load all the extensions"""
        await self.load_extensions()
        await self.tree.sync()
        await self.load_views()

    @watch(path="src/bot/cogs", colors=True)
    async def on_ready(self):
        """Called when the bot is ready"""
        try:
            if config.bot_status and config.bot_activity:
                activity: str = config.bot_activity
                activity = activity.replace("{shard_count}", str(self.shard_count))
                logger.debug(f"Activity: {activity}")
                custom_activity = CustomActivity(activity)
                await self.change_presence(
                    status=config.bot_status, activity=custom_activity
                )
                logger.info("Set status completed")
            else:
                logger.info("No bot status or activity set in configuration; skipping presence set.")
        except Exception as e:
            logger.error(f"Error setting presence: {e}")

        # Finish
        logger.info("Bot is ready")

        # Start tasks
        # TODO make this more dynamic by using the same logic from cog loading
        sync_roles.start(self)
