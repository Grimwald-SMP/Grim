import os
import time
import requests

# from src.utils.logger import logger
from rich import print


class ROTM:
    """ROTM API Wrapper"""

    def __init__(self, api_key: str, api_uri: str):
        self.api_key = api_key
        self.api_uri = api_uri
        self.players_cache = []
        self.player_last_fetched = 0

    async def players(self):
        if self.players_cache is None or time.time() - self.player_last_fetched > 120:
            self.players_cache = self.get_players()
            self.players_last_fetched = time.time()

        return self.players_cache

    def _get(self, path: str, params: dict = {}) -> dict:
        """Internal function for HTTP requests to the API

        Args:
            path (str): API path including the starting `/` (`/players`)
            params (dict, optional): Request parameters. Defaults to `{}`.

        Raises:
            Exception: API error

        Returns:
            dict: json result of the request
        """
        headers = {
            "User-Agent": "Grimwald-SMP/Grim (jadenlabs@proton.me)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

        res = requests.get(self.api_uri + path, params=params, headers=headers)
        if res.status_code == 200:
            return res.json()

        raise Exception(f"Error when accessing {path}: params={params} - res={res}")

    def get_players(self) -> list[str]:
        """Gets all of the registered players

        Returns:
            list[str]: A list of player usernames
        """
        return self._get("/players").get("players", [])

    def get_collectibles(self, username: str) -> dict:
        """Get the collectibles of a player

        Args:
            username (str): The player's username

        Returns:
            dict: `{player, collectibles, missing_collectibles}`
            - collectibles include `{name, level, players_with}`
        """
        return self._get(f"/collectibles/{username}")

    def get_achievements(self, username: str) -> dict:
        """Get the achievements of a player

        Args:
            username (str): The player's username

        Returns:
            dict: `{player, achievements, missing_achievements}`
            - achievements include `{name, description, rarity, players_with}`
        """
        return self._get(f"/achievements/{username}")

    def get_all_stats(self) -> dict:
        """Get the global stats

        Returns:
            dict: `{total_games_played, total_achievement_score, max_achievement_score, levels, achievements}`
            - achievements include `{name, description, rarity, players_with}`
            - levels include `{level, total_deaths, total_completions, collectibles_found, collectibles_available}`
        """
        return self._get("/stats").get("stats", {})

    def get_stats(self, username: str) -> dict:
        """Get the stats of a player

        Args:
            username (str): The player's username

        Returns:
            dict: `{games_played, total_door_toggles, achievement_score, max_achievement_score, levels, achievements}`
            - achievements include `{name, description, rarity, players_with}`
            - levels include `{level, total_deaths, total_completions, collectibles_found, collectibles_available}`
        """
        return self._get(f"/stats/{username}").get("stats", {})


# ROTMAPI_KEY = os.environ.get("ROTMAPI_KEY")
# ROTM_URI = os.environ.get("ROTM_URI")

ROTMAPI_KEY="477b7291e9bd856b5739e9c53c685e5a292df9da7f2984b42d5a9885caad658e"
ROTM_URI="https://rotm.grimwald.xyz/api"

if ROTM_URI is None or ROTMAPI_KEY is None:
    raise Exception("`ROTMAPI_KEY` or `ROTM_URI` not found in env.")

EMOJI_MAP = {
    # Achievements
    "Bronze": "<:bronze:1517322772009713704>",
    "Silver": "<:silver:1517322774857912360>",
    "Gold": "<:gold:1517322773024866405>",
    "Platinum": "<:platinum:1517322773725188227>",
    # Level 1 collectibles
    "Banner of Peace": "<:banner_of_peace:1517322813441179708>",
    "E-mart Sign": "<:e_mart_sign:1517322816297373706>",
    "Explosives": "<:explosives:1517322819636039760>",
    "Enderian Orb": "<:enderian_orb:1517322818633859162>",
    "Cityscape": "<:cityscape:1517322814229581975>",
    "Mountain Empire Painting": "<:mountain_empire_painting:1517322826036805644>",
    "Faction Castle": "<:faction_castle:1517322820491939952>",
    "Lonely Windmill": "<:lonely_windmill:1517322824123940874>",
    "SNAD": "<:snad:1517322833921970286>",
    "Joined Worlds": "<:joined_worlds:1517322823167639643>",
    "Mysterious Sign": "<:mysterious_sign:1517322827521331280>",
    "Pagoda": "<:pagoda:1517322828850925759>",
    "Submerged House": "<:submerged_house:1517322835729584320>",
    "Pyramid": "<:pyramid:1517322831250198780>",
    "Autumn Tree": "<:autumn_tree:1517322812673495110>",
    "Earth": "<:earth:1517322817287225406>",
    "Megabed": "<:megabed:1517322824992423946>",
    "Cyberpunk Car": "<:cyberpunk_car:1517322815148392650>",
    "Steampunk Clock": "<:steampunk_clock:1517322834840649820>",
    "Ship": "<:ship:1517322832416079912>",
    "Grimscrap": "<:grimscrap:1517322821410492557>",
    "Incendium Biomes": "<:incendium_biomes:1517322822345555978>",
    # Level 2 collectibles
    "Bike Ride": "<:bike_ride:1517323145827192933>",
    "High School": "<:high_school:1517323161497239712>",
    "Drivers License": "<:drivers_license:1517323154203349032>",
    "First Relationship": "<:first_relationship:1517323156367347927>",
    "Job Application": "<:job_application:1517323164072284202>",
    "Leaving Home": "<:leaving_home:1517323164953346261>",
    "Lockdown": "<:lockdown:1517323165909520434>",
    "Grieving": "<:grieving:1517323158800175266>",
    "Battleaxe": "<:battleaxe:1517323143772114974>",
    "Brain": "<:brain:1517323147056119838>",
    "Branch": "<:branch:1517323148306153623>",
    "Childhood Drawing": "<:childhood_drawing:1517323151166541897>",
    "Crown": "<:crown:1517323153020420097>",
    "Engagement Ring": "<:engagement_ring:1517323155338813329>",
    "Flight": "<:flight:1517323157222985860>",
    "Glasses": "<:glasses:1517323157986349247>",
    "Heartbreak": "<:heartbreak:1517323159651483738>",
    "Height Chart": "<:height_chart:1517323160607916052>",
    "Identity": "<:identity:1517323162864324668>",
    "Paint Bucket": "<:paint_bucket:1517323166987452478>",
    "Potion": "<:potion:1517323167805341797>",
    "Wave": "<:wave:1517323168992198676>",
}

rotm = ROTM(ROTMAPI_KEY, ROTM_URI)

if __name__ == "__main__":
    PLAYER = "ThisIsRoc"
    res = rotm.get_collectibles(PLAYER)
    print(res)
