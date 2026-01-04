from src.base.config import config

def get_bar(value: int = 0, max_value = 5):
    """Creates a progress bar using emojis."""

    if value < 0 or value > max_value:
        raise ValueError("Value must be between 0 and max_value")
    elif max_value < 2:
        raise ValueError("Max value must be 2 or more")

    start = config.emojis["grim_bar_left"] if value > 0 else config.emojis["grim_bar_left_empty"]
    end = config.emojis["grim_bar_right"] if value == max_value else config.emojis["grim_bar_right_empty"]

    full = config.emojis["grim_bar_mid"] * (value - 1)
    empty = config.emojis["grim_bar_mid_empty"] * (max_value - value - 1)

    return start + full + empty + end