from datetime import datetime

from discord import Color, Attachment, Embed

from .routine_commands import CommandPackage


class ViewManager:
    @staticmethod
    def get_help_embed(bot_commands: dict):
        embed = Embed(
            title="Bot Commands",
            color=Color.yellow()
        )
        for command, command_package in bot_commands.items():
            embed.add_field(
                name=f"/{command}",
                value=command_package.get_member("description"),
                inline=False
            )
        embed.add_field(name="/help", value="Displays all available commands", inline=False)
        embed.add_field(name="/streak", value="Shows current streak", inline=False)
        embed.set_footer(text="Use '/' to start typing a command!")
        
        return embed
    
    @staticmethod
    def get_routine_sent_embed(command_package: CommandPackage, file: Attachment):
        command_name = command_package.command_name
        command_color = command_package.get_member("color")
        local_datetime = datetime.now().strftime('%A, %B %d, %Y')

        embed = Embed(
            title=f"\U00002705 {command_name.capitalize()} Proof",
            description=f"**Date**: {local_datetime}",
            color=command_color
        )
        embed.set_image(url=file.url)
        
        return embed

    @staticmethod
    def get_streak_summary_embed(color: Color, description: str):
        embed = Embed(
            title="Current Week's Streak",
            description=description,
            color=color
        )
        
        return embed
    
    @staticmethod
    def get_deadline_embed(command_package: CommandPackage, description: str):
        command_name = command_package.command_name
        command_color = command_package.get_member("color")

        embed = Embed(
            title=f"\U0000274C {command_name.capitalize()} Deadline",
            description=description,
            color=command_color,
        )
        embed.set_footer(text="Remember to check your new balance!")
        
        return embed
