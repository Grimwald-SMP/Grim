from discord import Embed

from src.base.config import config

no_user_perms_embed = Embed(
    color=config.colors["error"],
    description=f"{config.emojis['disabled']} You do not have the needed permissions to run this command.",
)

no_bot_perms_embed = Embed(
    color=config.colors["error"],
    description=f"{config.emojis['disabled']} I do not have the needed permissions to run this command.",
)


def create_error_embed(message: str):
    return Embed(
        color=config.colors["error"],
        description=f"{config.emojis['disabled']} {message}",
    )
