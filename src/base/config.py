import os
from types import SimpleNamespace

import yaml
from dotenv import load_dotenv


def load_config(yaml_path) -> dict:
    with open(yaml_path, "r", encoding="UTF-8") as file:
        data = yaml.safe_load(file)
    return data


class Config:
    def __init__(self, yaml_path: str, env_path: str = ".env"):
        # .env Loading
        load_dotenv(dotenv_path=env_path)
        self.token = os.getenv("TOKEN")
        self.mongo_uri = os.getenv("MONGO_URI")

        # Yaml Loading
        self.config_dict = load_config(yaml_path)
        self.namespace = SimpleNamespace(**self.config_dict)
        vars(self).update(vars(self.namespace))


config = Config("./config.yaml", ".env")
