import os

import requests
from discord import app_commands, Interaction, Embed
from discord.ext.commands import Cog

from src.base.config import config
from src.bot.bot import Bot
from src.utils.checks import is_staff


class Whitelist(Cog):
    """Whitelist cog"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(name="whitelist", description="Whitelist a member")
    async def whitelist(self, ctx: Interaction, username: str, action: str = "add"):
        """Whitelist a member"""
        if not is_staff(ctx.user):
            await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if action not in ["add", "remove"]:
            await ctx.response.send_message("Invalid action", ephemeral=True)
            return
        action_verb = "added to" if action == "add" else "removed from"

        uri = f"{os.getenv('GRIMAPI_URI')}/whitelist"
        payload = {"username": username, "action": action}
        headers = {"Authorization": "Bearer " + os.getenv("GRIMAPI_KEY")}
        res = requests.post(uri, json=payload, headers=headers)

        if res.status_code != 204:
            await ctx.response.send_message(f"API error!", ephemeral=True)
            return

        embed = Embed(
            color=config.colors["primary"],
            description=f"`{username}` has been {action_verb} the Grimwald SMP.",
        )

        await ctx.response.send_message(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Whitelist(bot))
