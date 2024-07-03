from src.base.config import config


def bool_to_string(bool_item: bool, true_str: str, false_str: str):
    return true_str if bool_item else false_str


def bool_to_status_emoji(bool_item: bool):
    return bool_to_string(
        bool_item=bool_item,
        true_str=config.emojis["enabled"],
        false_str=config.emojis["disabled"],
    )


def string_bool_to_bool(string: str) -> bool:
    if isinstance(string, bool):
        return string

    string = string.lower()
    match string:
        case "true" | "t" | "yes" | "y":
            return True
        case "false" | "f" | "no" | "n" | "":
            return False
        case _:
            return True
