import discord
from discord import Interaction
from src.utils.logger import logger
from src.utils.embeds import no_bot_perms_embed


async def create_and_delete_invite(ctx: Interaction):
    bot_permissions = ctx.channel.permissions_for(ctx.guild.me)
    # logger.debug(f"Permissions: {bot_permissions}")

    has_inv_perm = bot_permissions.create_instant_invite
    logger.debug(f"Can create inv: {has_inv_perm}")

    if not has_inv_perm:
        logger.debug("Bot does not have create_instant_invite permission.")
        return await ctx.followup(embed=no_bot_perms_embed, ephemeral=True)

    try:
        invites = await ctx.guild.invites()
        # logger.debug(f"Invites: {invites}")

        bot_invites = [
            # I spent 3hrs debugging this because I thought the api was `ctx.bot.id`...
            invite
            for invite in invites
            if invite.inviter.id == ctx.client.user.id
        ]
        logger.debug(f"My invites: {bot_invites}")

        if not bot_invites:
            logger.debug("Bot has no invites to delete.")
        else:
            for bot_invite in bot_invites:
                try:
                    await bot_invite.delete()
                    logger.debug(f"Deleted invite with code {bot_invite.code}")
                except discord.HTTPException as error:
                    logger.error(
                        f"Error deleting invite with code {bot_invite.code}: {error}"
                    )

        logger.debug(f"Invite channel: {ctx.channel.name}")
        invite = await ctx.channel.create_invite(max_age=0)
        logger.debug(f"Invite: {invite}")

        return invite

    except discord.HTTPException as error:
        logger.error(f"Error fetching invites: {error}")
