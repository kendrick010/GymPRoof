import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

from utils.commands import bot_commands
from utils.db import db_init

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register the slash command tree
        await self.tree.sync()
        

bot = MyBot()

# Shared helper function for processing image commands
async def process_image_helper(interaction: discord.Interaction, file: discord.Attachment, command_name: str, color: discord.Color):
    if not file.content_type.startswith("image/"):
        await interaction.response.send_message(
            "R u dumb? Upload an image...", ephemeral=True
        )
        return

    try:
        # Defer the response to allow processing
        await interaction.response.defer()

        # Create a common embed
        embed = discord.Embed(
            title=f"{command_name.capitalize()} Proof",
            description=f"**File**: `{file.filename}`\n"
                        f"**Size**: `{file.size / 1024:.2f} KB`\n",
            color=color
        )
        embed.set_image(url=file.url)

        # Send the embed with the image preview
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"An error occurred while processing the `{command_name}` command: {e}", ephemeral=True)

# Dynamically register slash commands
for command_name, command_package in bot_commands.items():
    @bot.tree.command(name=command_name, description=command_package.get_criteria("description"))
    async def command_handler(interaction: discord.Interaction, file: discord.Attachment):
        # All bot commands require an image upload...
        await process_image_helper(interaction, file, command_name, command_package.get_criteria("color"))

@bot.tree.command(name="help", description="Displays all available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot Commands",
        color=discord.Color.yellow()
    )
    
    for command, command_package in enumerate(bot_commands):
        embed.add_field(
            name=f"/{command}",
            value=command_package.get_criteria("description"),
            inline=False
        )
    
    # Footer and additional details
    embed.set_footer(text="Use '/' to start typing a command!")
    
    # Send the embed
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Run the bot
load_dotenv()
db_init()
bot.run(os.environ.get('BOT_TOKEN'))
