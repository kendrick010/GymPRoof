from typing import Callable

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.routine_commands import CommandPackage, bot_commands, emoji_command_lookup
from utils.views import ViewManager
from utils.config import DiscordConfig
from utils.db import (
    add_streak,
    summarize_streak,
    punish_user,
    add_user,
    get_balance,
    update_balance,
    update_opted_routine,
    drop_opted_routine,
    get_opted_routines,
    get_opted_users
)


class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.reactions = True
        intents.messages = True
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register the slash command tree
        await self.tree.sync()

discord_config = DiscordConfig()
scheduler = AsyncIOScheduler()
bot = DiscordBot()

async def streak_summary_command(interaction: discord.Interaction, user: discord.User, color: discord.Color):
    user_id = str(user.id)

    balance = get_balance(user_id=user_id).get("user_balance")
    streak_summary = summarize_streak(user_id=user_id)
    opted_routines = get_opted_routines(user_id=user_id)

    description = f"{user.mention}\n**Balance**: {float(balance):.2f}\n\n"

    for routine in opted_routines:
        column_key = f"{routine}_days"
        streak_count = streak_summary.get(column_key, 0)
        description += f"**{routine}**: `{streak_count}`\n"

    # Create and send the embed
    summary_embed = ViewManager.get_streak_summary_embed(color, description)
    
    await interaction.followup.send(embed=summary_embed)

async def validate_streak_deadline(command_package: CommandPackage):
    channel = bot.get_channel(discord_config.bot_channel_id)

    # Punish users who have not completed routine deadline
    opted_users = get_opted_users(command_package=command_package)
    description = f"**Guess who missed their streak**\n\n"

    if not opted_users: return
    
    for user in opted_users:
        user_id = user.get("user_id")
        flag = punish_user(user_id=user_id, command_package=command_package)

        if flag: description += f"<@{user_id}>\n"

    deadline_embed = ViewManager.get_deadline_embed(command_package, description)

    await channel.send(embed=deadline_embed)

# Shared handler for processing route commands
async def routine_command(interaction: discord.Interaction, file: discord.Attachment, command_package: CommandPackage):
    if not file.content_type.startswith("image/"):
        await interaction.response.send_message(
            "R u dumb? Upload an image...", ephemeral=True
        )
        return
    
    user = interaction.user
    add_streak(user_id=user.id, command_package=command_package)

    try:
        # Defer the response to allow processing
        await interaction.response.defer()

        # Send the embed with the image preview
        routine_embed = ViewManager.get_routine_sent_embed(command_package=command_package, file=file)

        await interaction.followup.send(embed=routine_embed)

        # Send streak summary (reusing the helper function)
        await streak_summary_command(interaction, user, command_package.get_member("color"))

    except Exception as e:
        await interaction.followup.send(f"An error occurred while processing the `{command_name}` command: {e}", ephemeral=True)

async def routine_opt(payload: discord.RawReactionActionEvent, updater: Callable[[str, CommandPackage], None]):
    if payload.channel_id != discord_config.rules_channel_id or payload.message_id != discord_config.rules_message_id:
        return

    emoji = str(payload.emoji)
    user_id = payload.user_id
    command_package = emoji_command_lookup.get(emoji)

    updater(user_id=user_id, command_package=command_package)

def create_route_command_handler(command_name: str, command_package: CommandPackage):
    @bot.tree.command(name=command_name, description=command_package.get_member("description"))
    async def command_handler(interaction: discord.Interaction, file: discord.Attachment):
        # All bot commands require an image upload...
        await routine_command(interaction, file, command_package)

    return command_handler
    
# Dynamically register slash commands using factory
for command_name, command_package in bot_commands.items():
    create_route_command_handler(command_name, command_package)

@bot.tree.command(name="streak", description="Shows current streak")
async def streak_command(interaction: discord.Interaction, user: discord.Member):
    if user.bot: return

    await interaction.response.defer()
    
    # Send the streak summary for the user
    color = discord.Color.teal()

    await streak_summary_command(interaction, user, color)

@bot.tree.command(name="balance", description="Change balance")
async def balance_command(interaction: discord.Interaction, user: discord.Member, balance: float):
    update_balance(user_id=user.id, new_balance=balance)

    await interaction.response.send_message(f"Balance has been updated!.", ephemeral=True)

@bot.tree.command(name="help", description="Displays all available commands")
async def help_command(interaction: discord.Interaction):
    help_command_embed = ViewManager.get_help_embed(bot_commands)

    await interaction.response.send_message(embed=help_command_embed, ephemeral=True)

@bot.event
async def on_ready():
    # Suscribe routine deadline to schedular
    for command_package in bot_commands.values():
        deadline = command_package.get_member("deadline")

        if deadline:
            cron_trigger = CronTrigger(**deadline)

            # Add job to the scheduler
            scheduler.add_job(
                validate_streak_deadline,
                cron_trigger,
                args=[command_package],
                misfire_grace_time=60,
            )
    
    scheduler.start()

    # Register new users to database
    guild = discord.utils.get(bot.guilds, id=discord_config.server_id)
    async for member in guild.fetch_members(limit=None):
        if not member.bot:
            member_id = str(member.id)
            add_user(member_id)

    print("Schedulers and db setup complete")

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    await routine_opt(payload=payload, updater=update_opted_routine)

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    await routine_opt(payload=payload, updater=drop_opted_routine)

# Run the bot
bot.run(discord_config.bot_token)
