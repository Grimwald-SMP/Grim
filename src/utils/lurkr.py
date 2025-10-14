import os
import requests

class Lurkr:
    def __init__(self, guild_id: int, url: str = "https://api.lurkr.gg/v2"):
        self.url = url
        self.guild_id = guild_id
        self.api_key = os.getenv("LURKR_API_KEY")
        self.headers = {"X-API-Key": self.api_key}

    def get_user_level(self, user_id: int) -> int:
        response = requests.get(f"{self.url}/levels/{self.guild_id}/users/{user_id}", headers=self.headers)
        data = response.json()
        try:
            level = data["level"]["level"]
        except KeyError:
            level = 0

        return level