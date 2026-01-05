from discord import CategoryChannel, ForumChannel, app_commands, Interaction, Embed, Member
from discord.ext.commands import Cog

from src.base.config import config
from src.bot.bot import Bot
from src.bot.views.seasonpoll import PollView, get_poll_embed
from src.database.database import database
from src.utils.checks import is_staff
from src.utils.logger import logger


class SeasonPoll(Cog):
    """SeasonPoll cog"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(
        name="send-seasonpoll",
        description="Post the new season poll in the current channel.",
    )
    async def send_seasonpoll(self, ctx: Interaction):
        """Posts the new season poll."""
        if not isinstance(ctx.user, Member):
            raise ValueError("ctx.user must be of the Member type")
        if not is_staff(ctx.user):
            await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            embed = get_poll_embed()
            view = PollView(message_id=-1, state={})

            if isinstance(ctx.channel, (ForumChannel, CategoryChannel)):
                raise ValueError("Cannot sent a message to a Forum or Category channel.")
            elif ctx.channel is None:
                raise ValueError("Channel not found.")

            await ctx.response.send_message("Posting season poll...", ephemeral=True)
            message = await ctx.channel.send(embed=embed, view=view)

            database.views.insert_one(
                {
                    "message_id": message.id,
                    "channel_id": ctx.channel_id,
                    "state": view.state,
                    "view_type": "seasonpoll",
                }
            )
        except Exception as e:
            logger.error(f"Error sending season poll: {e}")

    @app_commands.command(
        name="active-seasonpolls", description="List all active season polls.",
    )
    async def active_seasonpolls(self, ctx: Interaction):
        """Lists all active season polls."""
        if not isinstance(ctx.user, Member):
            raise ValueError("ctx.user must be of the Member type")
        if not is_staff(ctx.user):
            await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        view_records = database.views.find({"view_type": "seasonpoll"})
        if not view_records:
            await ctx.response.send_message("No active season polls found.", ephemeral=True)
            return

        embed = Embed(
            color=config.colors["primary"],
            title="Active Season Polls",
            description="Here are the currently active season polls."
        )

        for record in view_records:
            message_link = f"https://discord.com/channels/{ctx.guild_id}/{record['channel_id']}/{record['message_id']}"
            embed.add_field(
                name=f"Poll in <#{record['channel_id']}>",
                value=f"Message ID: `{record['message_id']}` [link]({message_link})",
                inline=False
            )

        await ctx.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="remove-seasonpolls",
        description="Remove all season poll records from the database.",
    )
    async def remove_seasonpolls(self, ctx: Interaction):
        """Removes all season poll records from the database."""
        if not isinstance(ctx.user, Member):
            raise ValueError("ctx.user must be of the Member type")
        if not is_staff(ctx.user):
            await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        result = database.views.delete_many({"view_type": "seasonpoll"})
        await ctx.response.send_message(f"Removed {result.deleted_count} season poll records from the database.",
                                        ephemeral=True)

    @app_commands.command(
        name="clear-seasonpoll-votes",
        description="Clear all votes for the season poll.",
    )
    async def clear_seasonpoll_votes(self, ctx: Interaction):
        """Clears all votes for the season poll."""
        if not isinstance(ctx.user, Member):
            raise ValueError("ctx.user must be of the Member type")
        if not is_staff(ctx.user):
            await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        result = database.votes.delete_many({"polltype": "seasonpoll"})
        await ctx.response.send_message(f"Cleared {result.deleted_count} votes from the season poll.", ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(SeasonPoll(bot))
