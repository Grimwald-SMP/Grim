from traceback import format_exc
from discord import app_commands, Interaction, Embed, User
from discord.ext.commands import GroupCog
from src.utils.logger import logger
from src.base.config import config
from src.bot.bot import Bot
from src.utils.embeds import create_error_embed
from src.utils.timezone import set_timezone, get_timezone

import pytz
from datetime import datetime


class Timezones(GroupCog, name="timezone", description="Timezone commands"):
    """Timezones cog"""

    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name="get", description="Get a person's timezone")
    async def get(self, ctx: Interaction, user: User):
        """Get a person's timezone.

        Args:
            user (User): The person to get the timezone of
        """
        await ctx.response.defer()

        tz = await get_timezone(user.id)
        if tz is None:
            embed = create_error_embed(f"{user.mention} has not set their timezone.")
            return await ctx.edit_original_response(embed=embed)
        if tz is False:
            embed = create_error_embed(
                f"{user.mention} does not exist in the database."
            )
            return await ctx.edit_original_response(embed=embed)

        try:
            dt = datetime.now(pytz.utc)
            loc_dt = dt.astimezone(tz)  # Convert UTC time to user's timezone
            fmt = "%H:%M:%S"
            fmt_tz = loc_dt.strftime(fmt)
        except Exception as e:
            embed = create_error_embed(f"An error occurred: {str(e)}")
            return await ctx.edit_original_response(embed=embed)

        embed = Embed(
            color=config.colors["primary"],
            description=f"It is `{fmt_tz}` for {user.mention}.",
        )
        embed.set_footer(text=f"They are in the {tz.zone} timezone.")

        await ctx.edit_original_response(embed=embed)

    @app_commands.command(name="set", description="Get a person's timezone")
    async def set(self, ctx: Interaction, timezone: str):
        """Set your timezone

        Args:
            timezone(str): The timezone to set
        """
        # Defer as this involves db operations
        await ctx.response.defer()

        try:
            tz = pytz.timezone(timezone)
            res = await set_timezone(ctx.user.id, timezone)
            logger.debug(f"TZ CMD RES: {res}")
        except pytz.UnknownTimeZoneError:
            embed = create_error_embed(f"`{timezone}` is an unknown timezone.")
            return await ctx.edit_original_response(embed=embed)
        except Exception as e:
            logger.error(f"An error has occured\n{format_exc()}")
            raise e

        dt = datetime.now()

        embed = Embed(
            color=config.colors["primary"],
            description=f"{config.emojis['enabled']} Set your timezone to {tz.zone}.",
        )

        await ctx.edit_original_response(embed=embed)

    @app_commands.command(name="help", description="Get help with timezones.")
    async def set(self, ctx: Interaction):
        embed = Embed(
            color=config.colors["primary"],
            title="Timezone Help",
            description=f"\
While timezone codes like `GMT` and `MST` \
work, they tend to have issues. Instead, use \
timezone identifiers in the format of `[country]/[city]`\n\
{config.emojis['bullet']} For a list of supported timezones, view the [TZ Identifer list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).",
        )

        await ctx.response.send_message(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Timezones(bot))
