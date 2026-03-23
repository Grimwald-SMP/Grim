import asyncio
import os

import aiohttp
from discord import app_commands, Interaction, Embed
from discord.ext.commands import Cog

from src.base.config import config
from src.bot.bot import Bot
from src.utils.logger import logger

modrinth_token = os.getenv("MODRINTH_TOKEN")
BASE_MODRINTH_URL = "https://api.modrinth.com/v2/"
HEADERS = {
    "Authorization": modrinth_token,
    "User-Agent": "jadenlabs/grim/0.1.0 (jadenlabs@proton.me)",
}

MOD_NAMES = [
    "adventure-platform",
    "AnvilNeverTooExpensive",
    "ArmorPoser",
    "BetterMultiplayerSleep",
    "bluemap",
    "carbonchat",
    "Chunky",
    "cloth-config",
    "entityculling",
    "fabric-api",
    "fabric-language-kotlin",
    "FabricProxy-Lite",
    "fsit",
    "instamine_deepslate",
    "InvView",
    "itemswapper",
    "jei",
    "ledger",
    "lithium",
    "LuckPerms",
    "servux",
    "shulkerboxtooltip",
    "spark",
    "vanish"
]


async def http_get(session, *args, **kwargs):
    async with session.get(*args, **kwargs) as res:
        return await res.json()


async def search_project(session, name: str):
    url = f"{BASE_MODRINTH_URL}search?query={name}"
    data = await http_get(session, url, headers=HEADERS)
    results = data.get("hits", [])

    match = next((hit for hit in results if hit["slug"].lower() == name.lower()), None)
    res = match or (results[0] if results else None)
    if res is None:
        logger.warning(f"No results found for {name}")
    return res


async def check_mods(version: str, mods: list = None):
    async with aiohttp.ClientSession() as session:
        tasks = [search_project(session, name) for name in MOD_NAMES]
        mod_results = await asyncio.gather(*tasks)

        result = []

        for mod in mod_results:
            if mod is None:
                continue

            title: str = mod["title"]
            versions: list = mod["versions"]
            latest_version = versions[-1]
            has_req_version = version in versions

            result.append(
                {"title": title, "latest_version": latest_version, "has_req_version": has_req_version}
            )

        return result


class ModTracking(Cog):
    """ModTracking cog"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(name="check-mods", description="Track the servers mods")
    async def check_mods(self, ctx: Interaction, version: str):
        """Check if the server's mods are updated to the given version"""

        try:
            mod_list = await check_mods(version)

            lines = [f"`{'🟢' if mod['has_req_version'] else '🔴'}` {mod['latest_version']} - {mod['title']}" for mod in
                     mod_list]
            mods_fmt = "\n".join(lines)

            embed = Embed(
                color=config.colors["primary"],
                title=f"Mod tracking for {version}",
                description=mods_fmt,
            )
            embed.set_footer(text="Data pulled from Modrinth", icon_url="https://media.beehiiv.com/cdn-cgi/image/fit=scale-down,format=auto,onerror=redirect,quality=80/uploads/publication/logo/a49f8e1b-3835-4ea1-a85b-118c6425ebc3/Modrinth_Dark_Logo.png")

            await ctx.response.send_message(embed=embed)
        except Exception as e:
            print("An error has occurred:", e)

    @app_commands.command(name="check-mod", description="Check a mod on modrinth")
    async def check_mod(self, ctx: Interaction, name: str, version: str = config.modcheck["default_version"]):
        """Check a mod on modrinth against a version"""

        try:
            async with aiohttp.ClientSession() as session:
                mod = await search_project(session, name)
                if mod is None:
                    return None

            title: str = mod["title"]
            versions: list = mod["versions"]
            latest_version = versions[-1]
            has_req_version = version in versions

            embed = Embed(
                title=f"`{'🟢' if has_req_version else '🔴'}` {title} - {version}",
                description=f"""\
Latest: `{latest_version}`
Description:
> {mod.get("description", "none")}
Downloads: `{mod.get("downloads", 0)}`
""",
                color=0x00FF00 if has_req_version else 0xFF0000,
            )
            embed.set_thumbnail(url=mod["icon_url"])
            embed.set_footer(text="Data pulled from Modrinth", icon_url="https://media.beehiiv.com/cdn-cgi/image/fit=scale-down,format=auto,onerror=redirect,quality=80/uploads/publication/logo/a49f8e1b-3835-4ea1-a85b-118c6425ebc3/Modrinth_Dark_Logo.png")

            await ctx.response.send_message(embed=embed)
        except Exception as e:
            print("An error has occurred:", e)


async def setup(bot: Bot):
    await bot.add_cog(ModTracking(bot))
