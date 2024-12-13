import os
from dotenv import load_dotenv
from datetime import datetime

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.commands import CommandPackage, bot_commands
from utils.db import (db_init, 
                      add_streak, 
                      summarize_streak, 
                      punish_user,
                      get_users, 
                      get_balance, 
                      change_balance)


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register the slash command tree
        await self.tree.sync()


scheduler = AsyncIOScheduler()
bot = MyBot()

async def send_streak_summary(interaction: discord.Interaction, user: discord.User, color: discord.Color):
    balance = get_balance(user_name=user.name)
    summary = summarize_streak(user_name=user.name)
    enum_summary = f"{user.mention}\n**Balance**: {balance}\n\n"
    
    started, routines = set(), set(bot_commands.keys())
    for command, week_streak in summary:
        enum_summary += f"**{command}**: `{week_streak}`\n"
        started.add(command)

    routines = routines.difference(started)
    for routine in routines:
        enum_summary += f"**{routine}**: `0`\n"

    # Create and send the embed
    embed = discord.Embed(
        title="Current Week's Streak",
        description=enum_summary,
        color=color
    )
    
    await interaction.followup.send(embed=embed)

async def validate_streak_deadline(command_package: CommandPackage):
    channel_id = int(os.environ.get('BOT_CHANNEL'))
    channel = bot.get_channel(channel_id)

    # Punish users who have not completed deadlines
    all_users = get_users()
    description = f"**Guess who missed their streak!**\n\n"
    for user in all_users:
        flag = punish_user(user_name=user, command_package=command_package)

        if flag: description += f"@{user}\n"

    embed = discord.Embed(
        title=f"❌ {command_package.command_name.capitalize()} Deadline",
        description=description,
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Remember to check your new balance")

    await channel.send(embed=embed)

# Shared helper function for processing image commands
async def process_image_helper(interaction: discord.Interaction, file: discord.Attachment, command_package: CommandPackage):
    if not file.content_type.startswith("image/"):
        await interaction.response.send_message(
            "R u dumb? Upload an image...", ephemeral=True
        )
        return
    
    user = interaction.user
    command_name = command_package.command_name
    color = command_package.get_member("color")
    local_datetime = datetime.now().strftime('%A, %B %d, %Y')

    add_streak(user_name=user.name, command_package=command_package)

    try:
        # Defer the response to allow processing
        await interaction.response.defer()

        # Send the embed with the image preview
        embed = discord.Embed(
            title=f"✅ {command_name.capitalize()} Proof",
            description=f"**Date**: {local_datetime}",
            color=color
        )
        embed.set_image(url=file.url)

        await interaction.followup.send(embed=embed)

        # Send streak summary (reusing the helper function)
        await send_streak_summary(interaction, user, color)

    except Exception as e:
        await interaction.followup.send(f"An error occurred while processing the `{command_name}` command: {e}", ephemeral=True)

# Dynamically register slash commands using factory
for command_name, command_package in bot_commands.items():

    def create_command_handler(command_name, command_package):
        @bot.tree.command(name=command_name, description=command_package.get_member("description"))
        async def command_handler(interaction: discord.Interaction, file: discord.Attachment):
            # All bot commands require an image upload...
            await process_image_helper(interaction, file, command_package)

        return command_handler

    create_command_handler(command_name, command_package)

@bot.event
async def on_ready():
    for _, command_package in bot_commands.items():
        deadline = command_package.get_member("deadline")
        cron_trigger = CronTrigger(**deadline)

        # Add job to the scheduler
        scheduler.add_job(
            validate_streak_deadline,
            cron_trigger,
            args=[command_package],
        )
    
    scheduler.start()

@bot.tree.command(name="streak", description="Shows current streak")
async def streak_command(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer()
    
    # Send the streak summary for the user
    color = discord.Color.teal()

    await send_streak_summary(interaction, user, color)

@bot.tree.command(name="balance", description="Change balance")
async def balance_command(interaction: discord.Interaction, user: discord.Member, balance: int):
    change_balance(user_name=user.name, new_balance=balance)

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

# Run the bot
load_dotenv()
db_init()
bot.run(os.environ.get('BOT_TOKEN'))
