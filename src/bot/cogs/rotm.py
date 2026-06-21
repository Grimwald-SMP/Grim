from discord import app_commands, Interaction, Embed, User, File
from discord.ext.commands import GroupCog

from src.base.config import config
from src.bot.bot import Bot
from src.utils.rotm import rotm, EMOJI_MAP
from src.utils.logger import logger


async def username_autocomplete(
    ctx: Interaction, current: str
) -> list[app_commands.Choice[str]]:
    usernames = await rotm.players()
    choices = [
        app_commands.Choice(name=username, value=username)
        for username in usernames
        if username.lower().startswith(current.lower())
    ][:25]
    return choices


class ROTM(GroupCog, name="rotm", description="ROTM commands"):
    """ROTM cog"""

    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="profile", description="View your ROTM profile")
    @app_commands.autocomplete(username=username_autocomplete)
    async def profile(self, ctx: Interaction, username: str):
        try:
            await ctx.response.defer(ephemeral=False)

            stats = rotm.get_stats(username)

            # Format achievements
            achievement_data: list[dict] = stats.get("achievements", [])
            achievement_str = format_achievement_stats(achievement_data)

            achievement_message = f"""\
            Total Score: `{stats.get("achievement_score", 0)} of {stats.get("max_achievement_score", 0)}`
            {achievement_str}
            """

            # Format levels
            level_data: list[dict] = stats.get("levels", [])
            level_str = format_level(level_data)

            # print(stats)

            embed = Embed(
                title=f"{username}'s ROTM Profile",
                description=f"Games Played: `{stats.get("games_played", 0)}`",
                color=config.colors["primary"],
            )
            embed.add_field(name="Achievements", value=achievement_message, inline=True)
            embed.add_field(name="Levels", value=level_str, inline=True)

            await ctx.edit_original_response(embed=embed)
        except Exception as e:
            logger.exception("Error when running command", e)

    @app_commands.command(
        name="achievements", description="View your ROTM achievements"
    )
    @app_commands.autocomplete(username=username_autocomplete)
    async def achievements(self, ctx: Interaction, username: str):
        try:
            await ctx.response.defer(ephemeral=False)

            achievements: dict = rotm.get_achievements(username)
            achievements_obtained: list[dict] = achievements["achievements"]
            achievements_missing: list[dict] = achievements["missing_achievements"]
            achievements_map = map_achievements(achievements_obtained)

            embed = Embed(
                title=f"{username}'s Achievements",
                description=f"Achievements Obtained: `{len(achievements_obtained)}`\nAchievements Missing: `{len(achievements_missing)}`",
                color=config.colors["primary"],
            )
            embed = add_achievements_to_embed(achievements_map, embed)

            await ctx.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("Error when running command", e)

    @app_commands.command(
        name="collectibles", description="View your ROTM collectibles"
    )
    @app_commands.autocomplete(username=username_autocomplete)
    async def collectibles(self, ctx: Interaction, username: str):
        try:
            await ctx.response.defer(ephemeral=False)

            collectibles: dict = rotm.get_collectibles(username)
            collectibles_obtained: list[dict] = collectibles["collectibles"]
            collectibles_missing: list[dict] = collectibles["missing_collectibles"]
            collectibles_map = map_collectibles(collectibles_obtained)
            missing_collectibles_map = map_collectibles(collectibles_missing)

            embed = Embed(
                title=f"{username}'s Collectibles",
                color=config.colors["primary"],
            )
            embed = add_collectibles_to_embed(
                collectibles_map, missing_collectibles_map, embed
            )

            await ctx.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("Error when running command", e)

    @app_commands.command(
        name="global-stats", description="View the ROTM global-stats"
    )
    async def global_stats(self, ctx: Interaction):
        try:
            await ctx.response.defer(ephemeral=False)

            global_stats: dict = rotm.get_all_stats()
            achievement_data: list[dict] = global_stats.get("achievements", [])
            achievement_str = format_achievement_stats(achievement_data)

            achievement_message = f"""\
            Total Score: `{global_stats.get("total_achievement_score", 0)} of {global_stats.get("max_achievement_score", 0)}`
            {achievement_str}
            """

            level_data: list[dict] = global_stats.get("levels", [])
            level_str = format_global_level(level_data)

            embed = Embed(
                title=f"Global Stats",
                description=f"Stats across all players\nGames Played: `{global_stats.get("total_games_played", 0)}`",
                color=config.colors["primary"],
            )
            embed.add_field(name="Achievements", value=achievement_message, inline=True)
            embed.add_field(name="Levels", value=level_str, inline=True)

            await ctx.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("Error when running command", e)


def format_achievement_stats(achievement_data):
    achievement_map = {
        "Platinum": (None, None),
        "Gold": (None, None),
        "Silver": (None, None),
        "Bronze": (None, None),
    }

    for achievement in achievement_data:
        rarity = achievement["rarity"]
        available = achievement["available"]
        earned = achievement["earned"]
        achievement_map[rarity] = (available, earned)

    achievement_str = "\n".join(
        [
            f"{EMOJI_MAP.get(rarity)} {rarity}: `{earned} of {available}`"
            for rarity, (available, earned) in achievement_map.items()
        ]
    )

    return achievement_str


def format_global_level(level_data):
    level_strs = []

    for level in level_data:
        if level["level"] not in ["Level 1", "Level 2"]:
            continue
        level_strs.append(f"""\
**{level['level']}** - Collectibles: `{level.get('collectibles_found', 0)} of {level.get('collectibles_available', 0)}`
- `{level.get('total_completions', 0)}` Completions with `{level.get('total_deaths', 0)}` Deaths\
        """)

    return "\n".join(level_strs)


def format_level(level_data):
    level_strs = []

    for level in level_data:
        if level["level"] not in ["Level 1", "Level 2"]:
            continue
        level_strs.append(f"""\
**{level['level']}** - Collectibles: `{level.get('collectibles_found', 0)} of {level.get('collectibles_available', 0)}`  
- `{level.get('completions', 0)}` Completions with `{level.get('deaths', 0)}` Deaths\
        """)

    return "\n".join(level_strs)


def map_achievements(achievements: list[dict]):
    achievement_map = {
        "Platinum": [],
        "Gold": [],
        "Silver": [],
        "Bronze": [],
    }

    for achievement in achievements:
        achievement_map[achievement["rarity"]].append(
            {
                "name": achievement["name"],
                "description": achievement["description"],
                "players_with": achievement["players_with"],
            }
        )

    return achievement_map


def add_achievements_to_embed(achievement_map: dict, embed: Embed) -> Embed:
    for rarity, achievements in achievement_map.items():
        if len(achievements) == 0:
            continue

        field_lines = []
        for achievement in achievements:
            field_lines.append(f"- {achievement['name']}")

        field_value = "\n".join(field_lines)
        embed.add_field(
            name=f"{EMOJI_MAP[rarity]} {rarity}", value=field_value, inline=True
        )

    return embed


def map_collectibles(collectibles: list[dict]) -> dict:
    collectibles_map = {
        "Level 1": [],
        "Level 2": [],
    }

    for collectible in collectibles:
        collectibles_map[collectible["level"]].append(
            {
                "emoji": EMOJI_MAP[collectible["name"]],
                "name": collectible["name"],
            }
        )

    return collectibles_map


def add_collectibles_to_embed(
    collectibles_map: dict, missing_collectibles_map: dict, embed: Embed
) -> Embed:
    for level, collectibles in collectibles_map.items():
        missing_collectibles = missing_collectibles_map[level]

        collectibles_lines = []
        for collectible in collectibles:
            collectibles_lines.append(f"{collectible['emoji']}")

        num_missing = len(missing_collectibles)
        num_obtained = len(collectibles)
        num_total = num_missing + num_obtained

        embed.add_field(
            name=f"{level}  · `({num_obtained}/{num_total})`",
            value="".join(collectibles_lines),
            inline=False,
        )
    return embed


async def setup(bot: Bot):
    await bot.add_cog(ROTM(bot))
