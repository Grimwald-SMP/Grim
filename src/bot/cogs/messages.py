from discord import app_commands, Message, Embed
from discord.ext.commands import Cog
from src.base.config import config
from src.bot.bot import Bot
from src.utils.logger import logger
from src.utils.responses import (
    autoresponse_handler,
    response_add,
    response_delete,
    responses_get,
    trigger_add,
    trigger_delete,
    triggers_get,
)
from src.utils.embeds import create_error_embed
from traceback import format_exc


sudo_commands = {
    "response_add": {
        "function": response_add,
        "description": "Add a response",
        "usage": "args: `<name> <*message>`",
    },
    "response_delete": {
        "function": response_delete,
        "description": "Delete a response",
        "usage": "args: `<name>`",
    },
    "responses_get": {
        "function": responses_get,
        "description": "Get all responses",
        "usage": "args: `[page]`",
    },
    "trigger_add": {
        "function": trigger_add,
        "description": "Add a trigger",
        "usage": "args: `<response_name> <message>`",
    },
    "trigger_delete": {
        "function": trigger_delete,
        "description": "Delete a trigger",
        "usage": "args: `<trigger_id>`",
    },
    "triggers_get": {
        "function": triggers_get,
        "description": "Get all triggers",
        "usage": "args: `[page]`",
    },
}


class Messages(Cog):
    """Message cog"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: Message):
        """On message sent, run this"""
        content: str = message.content

        if content.startswith(config.sudo_prefix):
            if message.author.id in config.sudo_users:
                cmd_parts = content.split(" ")
                cmd = cmd_parts[1]
                args = cmd_parts[2:]

                if cmd in sudo_commands:
                    logger.info(f"Running cmd: {cmd}")
                    try:
                        response_msg = await sudo_commands[cmd]["function"](*args)
                    except Exception as e:
                        format_exc()
                        logger.error(f"An error has occured: {e}")
                        embed = create_error_embed("Something went wrong.")
                        await message.channel.send(embed=embed)
                        raise e
                else:
                    embed = create_error_embed("Command not found.")
                    await message.channel.send(embed=embed)

                embed = Embed(description=response_msg, color=config.colors["primary"])
                await message.channel.send(embed=embed)

        autoresponse_res = await autoresponse_handler(message)


async def setup(bot: Bot):
    await bot.add_cog(Messages(bot))
