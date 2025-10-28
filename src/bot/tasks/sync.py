import json
import os
from datetime import datetime
from typing import Any, Optional, Sequence

from discord import AutoShardedClient, Guild, Member, errors
from discord.ext import tasks

from src.base.config import config
from src.utils.logger import logger
from src.utils.lurkr import Lurkr
from src.utils.synced_role_definition import SyncedRoleDefinition

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BACKUP_DIR = os.path.join(BASE_PATH, "backups", "roles")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_role_map(synced_roles: dict[str, dict]) -> list[SyncedRoleDefinition]:
    """Convert synced role config to a list of RoleDefinition objects, sorted by days."""
    roles: list[SyncedRoleDefinition] = [
        SyncedRoleDefinition(
            days_required=role["days"],
            role_id=role["id"],
            level=role.get("level"),
            extra_roles=role.get("extras"),
            days_override=role.get("days_override"),
        )
        for role in synced_roles.values()
    ]
    sorted_roles = sorted(roles, key=lambda r: r.days_required)
    logger.debug(
        "Built role map: "
        + ", ".join(f"{r.days_required}d→{r.role_id}" for r in sorted_roles)
    )
    return sorted_roles


def calculate_days_in_server(member: Member, now: datetime) -> int:
    """Return the number of full days a member has been in the server."""
    joined_at = member.joined_at.replace(tzinfo=None)
    return max(0, (now - joined_at).days)


async def backup_roles(guild: Guild) -> None:
    """Back up current guild member roles to a JSON file."""
    logger.info("   Backing up member roles...")

    os.makedirs(BACKUP_DIR, exist_ok=True)

    members: dict[int, list[dict[str, Any]]] = {}
    count = 0

    for member in guild.members:
        if member.bot:
            continue

        roles = [
            {"name": name, "id": role["id"]}
            for name, role in config.synced_roles.items()
            if member.get_role(role["id"])
        ]
        members[member.id] = roles
        count += 1

    filename = datetime.now().strftime("ROLES__%Y-%m-%d-%H-%M.json")
    filepath = os.path.join(BACKUP_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(members, f, indent=2)

    logger.info(f"   Role backup saved → {filepath} ({count} members saved)")


def find_earned_role(days: int, roles: Sequence[SyncedRoleDefinition], level: int = None) -> Optional[int]:
    """Return the role ID that matches a member’s days in the server."""
    earned = None
    for role in roles:
        if days >= role.days_required:
            if role.level is not None and level:
                if level < role.level and days < role.days_override:
                    break
            earned = role.role_id
        else:
            break
    return earned


async def update_member_roles(
        member: Member,
        earned_role_id: int,
        roles: Sequence[SyncedRoleDefinition],
        guild: Guild,
) -> None:
    """Sync a member's roles."""
    # Make sure the role exists
    earned_role = guild.get_role(earned_role_id)
    if not earned_role:
        logger.warning(f"{member.name}: earned role not found.")
        return

    # Get the target role's definition
    target_role_def = None
    for role in roles:
        if role.role_id == earned_role_id:
            target_role_def = role
    if not target_role_def:
        logger.warning(f"{member.name}: target role definition not found.")
        return

    # Get the member's current roles
    member_roles = [role.id for role in member.roles]
    desired_role_ids = [earned_role_id]
    if target_role_def.extra_roles:
        desired_role_ids.extend(target_role_def.extra_roles)

    # Find roles to remove
    roles_to_remove = []
    for role in roles:
        # Skip if target role or extra
        if role.role_id in desired_role_ids:
            continue

        # Check if the member has the role
        if role.role_id in member_roles:
            role = guild.get_role(role.role_id)
            roles_to_remove.append(role)

    # Find roles to add
    roles_to_add = []
    for role_id in desired_role_ids:
        if role_id not in member_roles:
            role = guild.get_role(role_id)
            roles_to_add.append(role)

    # Log changes
    remove_log = ", ".join(f"[-]{r.name}" for r in roles_to_remove) if roles_to_remove else ""
    add_log = ", ".join(f"[+]{r.name}" for r in roles_to_add) if roles_to_add else ""
    if remove_log or add_log:
        logger.info(f"{member.name}: " + " | ".join(filter(None, [remove_log, add_log])))
    else:
        logger.debug(f"{member.name}: roles up-to-date for earned role {earned_role_id}.")

    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Sync roles - remove")
    if roles_to_add:
        await member.add_roles(*roles_to_add, reason="Sync roles - add")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Task
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@tasks.loop(seconds=config.role_sync_delay)
async def sync_roles(bot: AutoShardedClient) -> None:
    """Periodically sync member roles based on time in the server."""
    if config.dev:
        return

    current_member: Optional[Member] = None

    try:
        logger.info("   Starting role sync...")
        guild = bot.get_guild(config.home_server)
        if not guild:
            raise ValueError("Home guild not found")

        # await backup_roles(guild)

        now = datetime.now().replace(tzinfo=None)
        role_map = build_role_map(config.synced_roles)
        members = [m for m in guild.members if not m.bot]
        total = len(members)

        logger.info(f"Found {total} members to process.")

        for index, member in enumerate(members, start=1):
            current_member = member
            days = calculate_days_in_server(member, now)
            level = Lurkr(guild.id).get_user_level(member.id)

            logger.debug(f"[{index}/{total}] {member.name} — {days} days in server — level {level}")

            earned_role_id = find_earned_role(days, role_map, level)
            await update_member_roles(member, earned_role_id, role_map, guild)

        logger.info("   Role sync completed successfully.")

    except errors.Forbidden:
        if current_member:
            logger.warning(f"   Permission error while editing roles for {current_member.name}")
    except Exception as e:
        logger.exception(f"   Error during role sync: {e}")
