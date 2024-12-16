from typing import Callable, Any

from discord import Color
from supabase.client import Client


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

    def add_color(self, color: Color):
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
    
    def add_query(self, query: Callable[[Client, str], Any]):
        self.command_package.add_member("query", query)
        return self
    

bot_commands = {
    "gym":
        CommandPackageBuilder("gym")
        .add_description("Upload gym proof image/selfie")
        .add_color(Color.green())
        .add_emoji("\U0001F4AA")
        .add_punishment(-10.0)
        .add_deadline({"hour": 23, "minute": 59})
        .add_query(lambda client, user_id:
            client.table("streak_view").select("gym_complete")
            .filter("user_id", "eq", user_id)
            .limit(1)
        )
        .command_package
    ,
    "socials":
        CommandPackageBuilder("socials")
        .add_description("Upload socials image/screenshot")
        .add_color(Color.purple())
        .add_emoji("\U0001F465")
        .add_punishment(-15.0)
        .add_deadline({"day_of_week": "sun", "hour": 23, "minute": 59})
        .add_query(lambda client, user_id: 
            client.table("streak_view").select("socials_complete")
            .filter("user_id", "eq", user_id)
            .limit(1)
        )
        .command_package
    ,
    "food":
        CommandPackageBuilder("food")
        .add_description("Upload food image/selfie")
        .add_color(Color.red())
        .add_emoji("\U0001F357")
        .add_punishment(-5.0)
        .add_deadline({"hour": 23, "minute": 59})
        .add_query(lambda client, user_id: 
            client.table("streak_view").select("food_complete")
            .filter("user_id", "eq", user_id)
            .limit(1)
        )
        .command_package
    ,
    "outside":
        CommandPackageBuilder("outside")
        .add_description("Upload image/selfie of you dressed outside")
        .add_color(Color.blue())
        .add_emoji("\U00002600")
        .add_punishment(-5.0)
        .add_deadline({"hour": 7, "minute": 0})
        .add_query(lambda client, user_id: 
            client.table("streak_view").select("outside_complete")
            .filter("user_id", "eq", user_id)
            .limit(1)
        )
        .command_package
    ,
    "screentime":
        CommandPackageBuilder("screentime")
        .add_description("Upload image/screenshot of your <=3 hours screentime")
        .add_color(Color.orange())
        .add_emoji("\U0000260E")
        .add_punishment(-10.0)
        .add_deadline({"hour": 23, "minute": 59})
        .add_query(lambda client, user_id: 
            client.table("streak_view").select("screentime_complete")
            .filter("user_id", "eq", user_id)
            .limit(1)
        )
        .command_package
    ,
}

emoji_command_lookup = {command_package.get_member("emoji"): command_package for command_package in bot_commands.values()}