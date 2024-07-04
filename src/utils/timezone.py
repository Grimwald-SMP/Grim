import pytz
from datetime import datetime
from src.database.database import database
from src.utils.logger import logger
from traceback import format_exc


async def set_timezone(user_id: int, timezone: str) -> bool:
    assert user_id is not None, "User ID is none"
    assert timezone is not None, "Timezone is none"

    logger.debug(f"Timezone set, user {user_id} to `{timezone}`")
    user_doc = database.users.find_one({"_id": user_id})
    try:
        if user_doc:
            logger.info(f"Found doc for user {user_id}, updating...")
            ack = database.users.find_one_and_update(
                {"_id": user_id}, {"$set": {"timezone": timezone}}
            )
            return True
        else:
            logger.info(f"Doc not found for user {user_id}, creating...")
            ack = database.users.insert_one({"_id": user_id, "timezone": timezone})
            return True
    except Exception as e:
        format_exc()
        logger.error(f"An error has occured: {e}")
        raise e


async def get_timezone(user_id: int):
    assert user_id is not None, "User ID is none"

    logger.debug(f"Get timezone for {user_id}")
    user_doc = database.users.find_one({"_id": user_id})
    if not user_doc:
        return False

    timezone = user_doc.get("timezone", None)
    if timezone is None:
        return None

    return pytz.timezone(timezone)
