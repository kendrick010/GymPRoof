import os
from dotenv import load_dotenv
from datetime import datetime

from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.commands import *
from utils.db import *


class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.reactions = True
        intents.messages = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register the slash command tree
        await self.tree.sync()

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
SERVER_ID = int(os.environ.get('SERVER_ID'))
RULES_CHANNEL = int(os.environ.get('RULES_CHANNEL'))
BOT_CHANNEL = int(os.environ.get('BOT_CHANNEL'))
RULES_MESSAGE_ID = int(os.environ.get('RULES_MESSAGE_ID'))

scheduler = AsyncIOScheduler()
bot = DiscordBot()

async def streak_summary_command(interaction: discord.Interaction, user: discord.User, color: discord.Color):
    user_id = str(user.id)

    balance = get_balance(user_id=user_id)
    streak_summary = summarize_streak(user_id=user_id)
    streak_summary = {routine: streak_count for routine, streak_count in streak_summary}
    opted_routines = get_opted_routines(user_id=user_id)

    enum_summary = f"{user.mention}\n**Balance**: {balance}\n\n"

    for routine in opted_routines:
        streak_count = streak_summary.get(routine, 0)
        enum_summary += f"**{routine}**: `{streak_count}`\n"

    # Create and send the embed
    embed = discord.Embed(
        title="Current Week's Streak",
        description=enum_summary,
        color=color
    )
    
    await interaction.followup.send(embed=embed)

async def validate_streak_deadline(command_package: CommandPackage):
    channel = bot.get_channel(RULES_MESSAGE_ID)

    # Punish users who have not completed routine deadline
    opted_users = get_opted_users(command_package=command_package)
    description = f"**Guess who missed their streak**\n\n"

    if not opted_users: return
    
    for user_id in opted_users:
        flag = punish_user(user_id=user_id, command_package=command_package)

        if flag: description += f"<@{user_id}>\n"

    embed = discord.Embed(
        title=f"\U0000274C {command_package.command_name.capitalize()} Deadline",
        description=description,
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Remember to check your new balance!")

    await channel.send(embed=embed)

# Shared handler for processing route commands
async def routine_command(interaction: discord.Interaction, file: discord.Attachment, command_package: CommandPackage):
    if not file.content_type.startswith("image/"):
        await interaction.response.send_message(
            "R u dumb? Upload an image...", ephemeral=True
        )
        return
    
    user = interaction.user

    command_name = command_package.command_name
    color = command_package.get_member("color")
    local_datetime = datetime.now().strftime('%A, %B %d, %Y')

    add_streak(user_id=user.id, command_package=command_package)

    try:
        # Defer the response to allow processing
        await interaction.response.defer()

        # Send the embed with the image preview
        embed = discord.Embed(
            title=f"\U00002705 {command_name.capitalize()} Proof",
            description=f"**Date**: {local_datetime}",
            color=color
        )
        embed.set_image(url=file.url)

        await interaction.followup.send(embed=embed)

        # Send streak summary (reusing the helper function)
        await streak_summary_command(interaction, user, color)

    except Exception as e:
        await interaction.followup.send(f"An error occurred while processing the `{command_name}` command: {e}", ephemeral=True)

async def routine_opt(payload: discord.RawReactionActionEvent, updater: Callable[[str, str], None]):
    if payload.channel_id != RULES_CHANNEL or payload.message_id != RULES_MESSAGE_ID:
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
    embed = discord.Embed(
        title="Bot Commands",
        color=discord.Color.yellow()
    )
    
    for command, command_package in bot_commands.items():
        embed.add_field(
            name=f"/{command}",
            value=command_package.get_member("description"),
            inline=False
        )

    embed.add_field(name=f"/help", value="Displays all available commands", inline=False)
    embed.add_field(name=f"/streak", value="Shows current streak", inline=False)
    
    # Footer and additional details
    embed.set_footer(text="Use '/' to start typing a command!")
    
    # Send the embed
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
            )
    
    scheduler.start()

    # Register new users to database
    guild = discord.utils.get(bot.guilds, id=SERVER_ID)
    members = await guild.fetch_members(limit=None).flatten()

    for member in members:
        if not member.bot:
            member_id = str(member.id)
            add_user(member_id)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    await routine_opt(payload=payload, updater=update_opted_routine)

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    await routine_opt(payload=payload, updater=drop_opted_routine)

# Run the bot
db_init()
bot.run(BOT_TOKEN)
