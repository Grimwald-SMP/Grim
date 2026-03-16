from discord import Member
from discord.ext.commands import bot

from src.base.config import config

def is_staff(member: Member):
    if member.guild_permissions.administrator:
        return True
    elif member.id in config.sudo_users:
        return True
    elif member.get_role(config.roles["staff"]) is not None:
        return True

    return False