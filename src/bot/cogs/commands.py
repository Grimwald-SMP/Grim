from discord import Interaction, AppCommandType
from discord.ext.commands import Cog, CheckFailure

from src.bot.bot import Bot
from src.utils.embeds import no_user_perms_embed
from src.utils.logger import logger


class Commands(Cog):
    """Commands Events"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        logger.error(f"An error has occured: {error}")

        if isinstance(error, CheckFailure):
            await ctx.send(embed=no_user_perms_embed)

    @Cog.listener()
    async def on_app_command_completion(
            self, ctx: Interaction, command: AppCommandType
    ):
        from_message = f"${ctx.guild.id}" if ctx.guild else "in DM"
        logger.info(f"{command.name} done {from_message} @{ctx.user.id}")


async def setup(bot: Bot):
    await bot.add_cog(Commands(bot))
