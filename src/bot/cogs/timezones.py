from datetime import datetime, timedelta
from datetime import timezone as timez
from zoneinfo import ZoneInfo

from discord import app_commands, Interaction, Embed, User
from discord.ext.commands import GroupCog

from src.base.config import config
from src.bot.bot import Bot
from src.database.database import database


class Timezones(GroupCog, name="timezone", description="Timezone commands"):
    """Timezones cog"""

    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="set", description="Set your timezone")
    async def add(
        self,
        ctx: Interaction,
        timezone: str | None = None,
        utc_offset: int | None = None,
        current_time: str | None = None,
    ):
        """
        Add your timezone to the database.

        Parameters:
        timezone: str
            The name of the timezone to be added. Example: 'America/New_York'.
        utc_offset: int
            The UTC offset of your timezone, ex: -5 for EST.
        current_time: str
            The current time in your timezone. In the format of 'HH:MM' using 24 hr time.
        """

        try:
            tz = resolve_timezone(timezone, utc_offset, current_time)

            if tz is None:
                embed = Embed(
                    color=config.colors["error"],
                    description="Invalid timezone input. Use IANA code, UTC offset, or HH:MM.",
                )
                await ctx.response.send_message(embed=embed)
                return

            now = datetime.now(tz)
            fmt_tz = tzinfo_to_storage(tz)

            res = database.users.update_one(
                {"user_id": ctx.user.id}, {"$set": {"timezone": fmt_tz}}, upsert=True
            )
            print(res.upserted_id)

            embed = Embed(
                color=config.colors["primary"],
                title="Timezone Set",
                description=(
                    f"Set with value `{fmt_tz}`\n" f"-# Timezone: {now.tzname()}\n"
                ),
            )

            await ctx.response.send_message(embed=embed)

        except Exception as e:
            print("An error has occurred:", e)

    @app_commands.command(name="get", description="Get your timezone")
    async def get(self, ctx: Interaction, user: User | None = None):
        """Get your timezone"""
        user = user or ctx.user
        res = database.users.find_one({"user_id": user.id})
        if res is None:
            embed = Embed(
                color=config.colors["error"],
                description="You don't have a timezone set. Use `/timezone add` to set one.",
            )
            await ctx.response.send_message(embed=embed)
            return

        tz_str = res["timezone"] if res else None
        tz = storage_to_tzinfo(tz_str)
        now = datetime.now(tz)
        current_time = now.strftime("%H:%M %p")

        embed = Embed(
            color=config.colors["primary"],
            title=f"{user.display_name}'s Timezone",
            description=(
                f"Current time: `{current_time}`\n"
                f"-# Timezone: {now.tzname()}\n"
                f"-# Obtained at <t:{int(now.timestamp())}:t>"
            ),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.response.send_message(embed=embed)

    @app_commands.command(
        name="set-availability", description="Set the times when you're available"
    )
    async def set_availability(
        self,
        ctx: Interaction,
        start_time: str,
        end_time: str,
    ):
        """
        Set your availability times in your timezone.

        Parameters:
        start_time: str
            The start time of your availability in 'HH:MM' 24 hr format.
        end_time: str
            The end time of your availability in 'HH:MM' 24 hr format.
        """

        try:
            start_h, start_m = map(int, start_time.split(":"))
            end_h, end_m = map(int, end_time.split(":"))

            if not (0 <= start_h < 24 and 0 <= start_m < 60):
                raise ValueError("Invalid start time")
            if not (0 <= end_h < 24 and 0 <= end_m < 60):
                raise ValueError("Invalid end time")

            database.users.update_one(
                {"user_id": ctx.user.id},
                {
                    "$set": {
                        "availability": {
                            "start_time": f"{start_h:02d}:{start_m:02d}",
                            "end_time": f"{end_h:02d}:{end_m:02d}",
                        }
                    }
                },
                upsert=True,
            )

            embed = Embed(
                color=config.colors["primary"],
                title="Availability Set",
                description=(
                    f"Your availability has been set from `{start_h:02d}:{start_m:02d}` "
                    f"to `{end_h:02d}:{end_m:02d}` in your timezone."
                ),
            )

            await ctx.response.send_message(embed=embed)

        except ValueError:
            embed = Embed(
                color=config.colors["error"],
                description="Invalid time format. Please use 'HH:MM' in 24 hr format.",
            )
            await ctx.response.send_message(embed=embed)
        except Exception as e:
            print("An error has occurred:", e)

    @app_commands.command(
        name="availability-chart", description="Get a chart of user availabilities"
    )
    async def availability_chart(self, ctx: Interaction):
        """Get a chart of user availabilities."""

        try:
            res = database.users.find_one(
                {"user_id": ctx.user.id, "availability": {"$exists": True}}
            )

            availability = res["availability"] if res else None
            if not availability:
                await ctx.response.send_message("Unable to find availability data.")
                return

            def time_to_slot(t: str) -> int:
                hour, minute = map(int, t.split(":"))
                return hour * 2 + (1 if minute >= 30 else 0)

            start_slot = time_to_slot(availability["start_time"])
            end_slot = time_to_slot(availability["end_time"])

            bar = ""
            for slot in range(48):
                if start_slot <= slot < end_slot:
                    bar += "#"
                else:
                    bar += "-"

            header = "UTC |00----04----08----12----16----20----24"

            embed = Embed(
                color=config.colors["primary"],
                title="Availability Chart",
                description=f"```\n{header}\n    |{bar}\n```",
            )

            await ctx.response.send_message(embed=embed)

        except Exception as e:
            print("An error has occurred:", e)



async def setup(bot: Bot):
    await bot.add_cog(Timezones(bot))


def resolve_timezone(
    iana: str | None, utc_offset: int | None, current_time: str | None
):
    if iana:
        return ZoneInfo(iana)

    if utc_offset is not None:
        return timez(timedelta(hours=utc_offset))

    if current_time:
        try:
            h, m = map(int, current_time.split(":"))

            utc_now = datetime.now(timez.utc)

            user_today = utc_now.replace(tzinfo=None).replace(
                hour=h, minute=m, second=0, microsecond=0
            )

            diff = user_today - utc_now.replace(tzinfo=None)

            if diff < timedelta(hours=-12):
                diff += timedelta(days=1)
            elif diff > timedelta(hours=14):
                diff -= timedelta(days=1)

            return timez(diff)

        except ValueError:
            return None

    return None


def tzinfo_to_storage(tz) -> str:
    """
    Convert a tzinfo object into a normalized storage string.

    IANA: stored as the IANA name
    Fixed-offset: stored as 'UTC+/-HH:MM'
    """
    if isinstance(tz, ZoneInfo):
        return tz.key

    offset = tz.utcoffset(None)
    if offset is None:
        return "UTC"

    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def storage_to_tzinfo(stored_str: str):
    """
    Convert a stored timezone string back into a tzinfo object.

    IANA names -> ZoneInfo
    UTC offsets -> datetime.timezone
    """
    if not stored_str:
        return timez.utc

    stored_str = stored_str.strip()

    if stored_str.startswith("UTC"):
        if stored_str == "UTC":
            return timez.utc

        try:
            sign = 1 if stored_str[3] == "+" else -1
            hours, minutes = map(int, stored_str[4:].split(":"))
            offset = timedelta(hours=hours, minutes=minutes) * sign
            return timez(offset)
        except Exception:
            return timez.utc

    try:
        return ZoneInfo(stored_str)
    except Exception:
        return timez.utc


