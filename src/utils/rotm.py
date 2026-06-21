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

# # Dev
# EMOJI_MAP = {
#     # Achievements
#     "Bronze": "<:bronze:1517322772009713704>",
#     "Silver": "<:silver:1517322774857912360>",
#     "Gold": "<:gold:1517322773024866405>",
#     "Platinum": "<:platinum:1517322773725188227>",
#     # Level 1 collectibles
#     "Banner of Peace": "<:banner_of_peace:1517322813441179708>",
#     "E-mart Sign": "<:e_mart_sign:1517322816297373706>",
#     "Explosives": "<:explosives:1517322819636039760>",
#     "Enderian Orb": "<:enderian_orb:1517322818633859162>",
#     "Cityscape": "<:cityscape:1517322814229581975>",
#     "Mountain Empire Painting": "<:mountain_empire_painting:1517322826036805644>",
#     "Faction Castle": "<:faction_castle:1517322820491939952>",
#     "Lonely Windmill": "<:lonely_windmill:1517322824123940874>",
#     "SNAD": "<:snad:1517322833921970286>",
#     "Joined Worlds": "<:joined_worlds:1517322823167639643>",
#     "Mysterious Sign": "<:mysterious_sign:1517322827521331280>",
#     "Pagoda": "<:pagoda:1517322828850925759>",
#     "Submerged House": "<:submerged_house:1517322835729584320>",
#     "Pyramid": "<:pyramid:1517322831250198780>",
#     "Autumn Tree": "<:autumn_tree:1517322812673495110>",
#     "Earth": "<:earth:1517322817287225406>",
#     "Megabed": "<:megabed:1517322824992423946>",
#     "Cyberpunk Car": "<:cyberpunk_car:1517322815148392650>",
#     "Steampunk Clock": "<:steampunk_clock:1517322834840649820>",
#     "Ship": "<:ship:1517322832416079912>",
#     "Grimscrap": "<:grimscrap:1517322821410492557>",
#     "Incendium Biomes": "<:incendium_biomes:1517322822345555978>",
#     # Level 2 collectibles
#     "Bike Ride": "<:bike_ride:1517323145827192933>",
#     "High School": "<:high_school:1517323161497239712>",
#     "Drivers License": "<:drivers_license:1517323154203349032>",
#     "First Relationship": "<:first_relationship:1517323156367347927>",
#     "Job Application": "<:job_application:1517323164072284202>",
#     "Leaving Home": "<:leaving_home:1517323164953346261>",
#     "Lockdown": "<:lockdown:1517323165909520434>",
#     "Grieving": "<:grieving:1517323158800175266>",
#     "Battleaxe": "<:battleaxe:1517323143772114974>",
#     "Brain": "<:brain:1517323147056119838>",
#     "Branch": "<:branch:1517323148306153623>",
#     "Childhood Drawing": "<:childhood_drawing:1517323151166541897>",
#     "Crown": "<:crown:1517323153020420097>",
#     "Engagement Ring": "<:engagement_ring:1517323155338813329>",
#     "Flight": "<:flight:1517323157222985860>",
#     "Glasses": "<:glasses:1517323157986349247>",
#     "Heartbreak": "<:heartbreak:1517323159651483738>",
#     "Height Chart": "<:height_chart:1517323160607916052>",
#     "Identity": "<:identity:1517323162864324668>",
#     "Paint Bucket": "<:paint_bucket:1517323166987452478>",
#     "Potion": "<:potion:1517323167805341797>",
#     "Wave": "<:wave:1517323168992198676>",
# }

# Prod
EMOJI_MAP = {
    # Achievements
    "Bronze": "<:bronze:1518356316983136326>",
    "Silver": "<:silver:1518356320955138224>",
    "Gold": "<:gold:1518356317784375357>",
    "Platinum": "<:platinum:1518356319298523137>",
    # Level 1 collectibles
    "Banner of Peace": "<:banner_of_peace:1518356348037758986>",
    "E-mart Sign": "<:e_mart_sign:1518356350927765726>",
    "Explosives": "<:explosives:1518356354660827186>",
    "Enderian Orb": "<:enderian_orb:1518356353431769318>",
    "Cityscape": "<:cityscape:1518356349279277227>",
    "Mountain Empire Painting": "<:mountain_empire_painting:1518356363737301042>",
    "Faction Castle": "<:faction_castle:1518356357131014234>",
    "Lonely Windmill": "<:lonely_windmill:1518356361807794186>",
    "SNAD": "<:snad:1518356368271216814>",
    "Joined Worlds": "<:joined_worlds:1518356360570343585>",
    "Mysterious Sign": "<:mysterious_sign:1518356364840276190>",
    "Pagoda": "<:pagoda:1518356365746376955>",
    "Submerged House": "<:submerged_house:1518356370804445295>",
    "Pyramid": "<:pyramid:1518356366626918601>",
    "Autumn Tree": "<:autumn_tree:1518356347316604978>",
    "Earth": "<:earth:1518356352282398860>",
    "Megabed": "<:megabed:1518356362525016255>",
    "Cyberpunk Car": "<:cyberpunk_car:1518356350009213039>",
    "Steampunk Clock": "<:steampunk_clock:1518356369416126474>",
    "Ship": "<:ship:1518356367415705660>",
    "Grimscrap": "<:grimscrap:1518356358381047859>",
    "Incendium Biomes": "<:incendium_biomes:1518356359521767484>",
    # Level 2 collectibles
    "Bike Ride": "<:bike_ride:1518356391193215076>",
    "High School": "<:high_school:1518356403100581978>",
    "Drivers License": "<:drivers_license:1518356395660148868>",
    "First Relationship": "<:first_relationship:1518356397526356119>",
    "Job Application": "<:job_application:1518356404925239386>",
    "Leaving Home": "<:leaving_home:1518356406653419660>",
    "Lockdown": "<:lockdown:1518356407487954954>",
    "Grieving": "<:grieving:1518356399858389072>",
    "Battleaxe": "<:battleaxe:1518356390463148144>",
    "Brain": "<:brain:1518356392086601768>",
    "Branch": "<:branch:1518356393109749891>",
    "Childhood Drawing": "<:childhood_drawing:1518356394024108113>",
    "Crown": "<:crown:1518356394896658616>",
    "Engagement Ring": "<:engagement_ring:1518356396679102584>",
    "Flight": "<:flight:1518356397916557376>",
    "Glasses": "<:glasses:1518356398977581167>",
    "Heartbreak": "<:heartbreak:1518356400852570323>",
    "Height Chart": "<:height_chart:1518356401649356972>",
    "Identity": "<:identity:1518356403863949442>",
    "Paint Bucket": "<:paint_bucket:1518356408800907325>",
    "Potion": "<:potion:1518356409551683737>",
    "Wave": "<:wave:1518356410474303748>",
}

rotm = ROTM(ROTMAPI_KEY, ROTM_URI)

if __name__ == "__main__":
    PLAYER = "ThisIsRoc"
    res = rotm.get_collectibles(PLAYER)
    print(res)
