from discord import Message, Embed
from bson.objectid import ObjectId
from src.database.database import database
from src.utils.logger import logger
from src.base.config import config
from traceback import format_exc

PAGE_ITEM_COUNT = 20


async def autoresponse_handler(message: Message):
    content = message.content

    if message.channel.id in config.blacklists["autoresponse_channels"]:
        return False

    trigger_doc = database.triggers.find_one({"message": content})
    if not trigger_doc:
        return None

    response_doc = database.responses.find_one({"name": trigger_doc["response_name"]})
    if not response_doc:
        return None

    embed = Embed(color=config.colors["primary"], description=response_doc["message"])
    await message.reply(embed=embed)


async def response_add(*args):
    name, *message_list = args
    message = " ".join(message_list)
    assert name, "Name arg not included"
    assert message, "Message arg not included"
    logger.debug(f"Creating response for name: {name}")

    response_doc = database.responses.find_one({"name": name})
    try:
        if response_doc:
            logger.debug(f"Found response for `{name}`")
            return "Response already exists."
        else:
            logger.debug(f"Response not found for `{name}`, creating entry")
            ack = database.responses.insert_one({"name": name, "message": message})
            return f"Response created, id: `{ack.inserted_id}`"
    except Exception as e:
        format_exc()
        logger.error(f"An error has occured: {e}")
        raise e


async def response_delete(*args):
    name = args[0]
    logger.debug(f"Deleting response with name: {name}")

    response_doc = database.responses.find_one({"name": name})
    if response_doc:
        logger.debug(f"Response found for name: {name}")
        ack = database.responses.delete_one({"name": name})
        return f"Deleted response for name: `{name}`"
    else:
        return f"Response not found for name: `{name}`"


async def responses_get(*args: tuple):
    page = 0 if not args else args[0]
    logger.info(f"Getting responses, page: {page}")

    response_docs = list(
        database.responses.find({}).skip(page * PAGE_ITEM_COUNT).limit(PAGE_ITEM_COUNT)
    )
    responses_fmt = [
        f"{config.emojis['bullet']} **{response_doc['name']}** - `{response_doc['_id']}`\n> {response_doc['message']}"
        for response_doc in response_docs
    ]
    responses_str = "\n\n".join(responses_fmt)
    return responses_str


async def trigger_add(*args):
    response_name, *message_list = args
    message = " ".join(message_list)
    assert response_name, "Response_name arg not included"
    assert message, "Message arg not included"
    logger.debug(f"Creating trigger for response: {response_name}")

    response_doc = database.triggers.find_one({"message": message})
    try:
        if response_doc:
            logger.debug(f"Found trigger for response: `{response_name}`")
            return "Trigger already exists."
        else:
            logger.debug(
                f"Trigger not found for response: `{response_name}`, creating entry"
            )
            ack = database.triggers.insert_one(
                {"response_name": response_name, "message": message}
            )
            return f"Trigger created, id: `{ack.inserted_id}`"
    except Exception as e:
        format_exc()
        logger.error(f"An error has occured: {e}")
        raise e


async def trigger_delete(*args):
    trigger_id = ObjectId(args[0])
    logger.debug(f"Deleting trigger with trigger_id: {trigger_id}")

    trigger_doc = database.triggers.find_one({"_id": trigger_id})
    if trigger_doc:
        logger.debug(f"Trigger found with trigger_id: {trigger_id}")
        ack = database.triggers.delete_one({"_id": trigger_id})
        return f"Deleted trigger with id: `{trigger_id}`"
    else:
        return f"Trigger not found with id: `{trigger_id}`"


async def triggers_get(*args: tuple):
    page = 0 if not args else args[0]
    logger.info(f"Getting triggers, page: {page}")

    trigger_docs = list(
        database.triggers.find({}).skip(page * PAGE_ITEM_COUNT).limit(PAGE_ITEM_COUNT)
    )
    triggers_fmt = [
        f"{config.emojis['bullet']} **{response_doc['response_name']}** - `{response_doc['_id']}`\n> {response_doc['message']}"
        for response_doc in trigger_docs
    ]
    triggers_str = "\n\n".join(triggers_fmt)
    return triggers_str
