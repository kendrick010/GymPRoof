from typing import Callable
import discord

class CommandPackage:
    def __init__(self, command_name: str):
        self.command_name = command_name
        self.meta = {}

    def add_member(self, member_name: str, member_value):
        self.meta[member_name] = member_value

    def get_member(self, member_name: str):
        return self.meta.get(member_name)


class CommandPackageBuilder:
    def __init__(self, command_name: str):
        self.command_package = CommandPackage(command_name)

    def add_description(self, description: str):
        self.command_package.add_member("description", description)
        return self

    def add_color(self, color: discord.Color):
        self.command_package.add_member("color", color)
        return self
    
    def add_emoji(self, emoji: str):
        self.command_package.add_member("emoji", emoji)
        return self

    def add_punishment(self, punishment: float):
        self.command_package.add_member("punishment", punishment)
        return self
    
    def add_deadline(self, deadline: dict):
        self.command_package.add_member("deadline", deadline)
        return self
    
    def add_validator(self, validator: Callable[[str], str]):
        self.command_package.add_member("validator", validator)
        return self
    

current_week_filter = """
    WITH week_dates AS (
    SELECT
        date('now', '-' || ((strftime('%w', 'now', 'localtime') + 6) % 7) || ' days') AS week_start,
        date('now', '+' || (6 - (strftime('%w', 'now', 'localtime') + 6) % 7) || ' days') AS week_end
    )
"""

bot_commands = {
    "gym":
        CommandPackageBuilder("gym")
        .add_description("Upload gym proof image/selfie")
        .add_color(discord.Color.green())
        .add_emoji("\U0001F4AA")
        .add_punishment(-10.0)
        .add_deadline({"hour": 23, "minute": 59})
        .add_validator(lambda user: f"""
            {current_week_filter}
            SELECT CASE
                WHEN (COUNT(DISTINCT DATE(date_time)) + 7 - strftime('%w', 'now', 'localtime')) >= 5 THEN 1
                ELSE 0
            END
            FROM streaks
            WHERE date_time BETWEEN (SELECT week_start FROM week_dates) AND (SELECT week_end FROM week_dates)
            AND routine_type = 'gym'
            AND user_id = '{user}';
        """)
        .command_package
    ,
    "socials":
        CommandPackageBuilder("socials")
        .add_description("Upload socials image/screenshot")
        .add_color(discord.Color.purple())
        .add_emoji("\U0001F465")
        .add_punishment(-15.0)
        .add_deadline({"day_of_week": "sun", "hour": 23, "minute": 59})
        .add_validator(lambda user: f"""
            {current_week_filter}
            SELECT CASE 
                WHEN COUNT(*) > 0 THEN 1 
                ELSE 0 
            END
            FROM streaks
            WHERE date_time BETWEEN (SELECT week_start FROM week_dates) AND (SELECT week_end FROM week_dates)
            AND routine_type = 'socials'
            AND user_id = '{user}';
        """)
        .command_package
    ,
    "food":
        CommandPackageBuilder("food")
        .add_description("Upload food image/selfie")
        .add_color(discord.Color.red())
        .add_emoji("\U0001F357")
        .add_punishment(-5.0)
        .add_deadline({"hour": 23, "minute": 59})
        .add_validator(lambda user: f"""
            SELECT CASE 
                WHEN COUNT(*) > 0 THEN 1 
                ELSE 0 
            END
            FROM streaks
            WHERE DATE(date_time) = DATE('now', 'localtime') 
            AND routine_type = 'food'
            AND user_id = '{user}';
        """)
        .command_package
    ,
    "outside":
        CommandPackageBuilder("outside")
        .add_description("Upload image/selfie of you dressed outside")
        .add_color(discord.Color.blue())
        .add_emoji("\U00002600")
        .add_punishment(-5.0)
        .add_deadline({"hour": 7, "minute": 0})
        .add_validator(lambda user: f"""
            SELECT CASE 
                WHEN COUNT(*) > 0 THEN 1 
                ELSE 0 
            END
            FROM streaks
            WHERE DATE(date_time) = DATE('now', 'localtime') 
            AND routine_type = 'outside'
            AND user_id = '{user}';
        """)
        .command_package
    ,
    "screentime":
        CommandPackageBuilder("screentime")
        .add_description("Upload image/screenshot of your <=3 hours screentime")
        .add_color(discord.Color.orange())
        .add_emoji("\U0000260E")
        .add_punishment(-10.0)
        .add_deadline({"hour": 23, "minute": 59})
        .add_validator(lambda user: f"""
            SELECT CASE 
                WHEN COUNT(*) > 0 THEN 1 
                ELSE 0 
            END
            FROM streaks
            WHERE DATE(date_time) = DATE('now', 'localtime') 
            AND routine_type = 'screentime'
            AND user_id = '{user}';
        """)
        .command_package
    ,
}

emoji_command_lookup = {command_package.get_member("emoji"): command_package for command_package in bot_commands.values()}