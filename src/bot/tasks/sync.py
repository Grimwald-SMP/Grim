import os
import json
from datetime import datetime
from discord.ext import tasks
from discord import AutoShardedClient, Guild, errors
from src.base.config import config
from src.utils.logger import logger
from traceback import print_exc

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
backup_dir = os.path.join(base_path, "backups", "roles")


async def backup_roles(guild: Guild):
    logger.info("Backing up member roles to json")
    roles_map = sorted(
        [(name, role["id"]) for name, role in config.synced_roles.items()],
        key=lambda x: x[0],
    )

    # Hold a dict of members with their roles
    # user_id: {
    #   roles: [
    #       {name, id}
    #   ]
    # }
    members = {}

    # Iterate for members in guilds
    for member in guild.members:
        # Skip if bot
        if member.bot:
            continue

        roles = []
        # Iterate for role in the roles map
        for name, role_id in roles_map:
            # If the member has the role, add it to the roles
            if member.get_role(role_id):
                roles.append({"name": name, "id": role_id})

        # Add the roles to the members
        members[member.id] = roles

    logger.info("Dumping json")
    now = datetime.now()
    name = now.strftime("ROLES__%Y-%m-%d-%H-%M.json")
    path = os.path.join(backup_dir, name)

    with open(path, "w", encoding="utf8") as f:
        json.dump(members, f, indent=4)


@tasks.loop(seconds=config.role_sync_delay)
async def sync_roles(bot: AutoShardedClient):
    try:
        logger.info("Role sync starting...")

        # Get members
        guild = bot.get_guild(config.home_server)
        await backup_roles(guild)
        members = guild.members
        assert members, "Members is none"
        logger.debug(f"Syncing roles for {len(members)} members")

        # Get current time
        now = datetime.now().replace(tzinfo=None)

        # Map roles and sort
        roles_map = sorted(
            [(role["days"], role["id"]) for _, role in config.synced_roles.items()],
            key=lambda x: x[0],
        )

        for member in members:
            # Skip if bot
            if member.bot:
                continue

            # Get time in server
            joined_at = member.joined_at.replace(tzinfo=None)
            member_for = now - joined_at
            days_in_server = max(0, member_for.days)  # Set any negative values to 0
            logger.debug(f"Sync {member.name} | {days_in_server} days")

            # Get role according to time in the server
            earned_role_id = None
            for days, role in roles_map:
                # If member in server longer than req, set earned role to that role
                if days_in_server >= days:
                    earned_role_id = role
                    continue

                # Else break the loop
                break

            # Check if member already has role
            existing_role = member.get_role(earned_role_id)
            if existing_role:
                logger.debug(f"\[/] {existing_role.name}")
                continue

            # Remove the other roles
            for _, role_id in roles_map:
                old_role = member.get_role(role_id)
                if old_role:
                    logger.debug(f"\[-] {old_role.name}")
                    await member.remove_roles(old_role, reason=f"Sync role - Rem")

            # Give the member the role
            earned_role = guild.get_role(earned_role_id)
            await member.add_roles(earned_role, reason="Sync role - Add")
            logger.info(f"\[+] {earned_role.name}")
        logger.info("Role sync completed...")
    except Exception as e:
        if isinstance(e, errors.Forbidden):
            logger.warn(f"Could not edit roles for {member.name}")
        else:
            print_exc()

        logger.error(f"An error has occured: {e}")
