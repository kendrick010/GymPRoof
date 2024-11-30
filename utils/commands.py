import discord
from datetime import datetime


class CommandPackage:
    def __init__(self, command_name):
        self.command_name = command_name
        self.meta = {}

    def add_criteria(self, criteria, criteria_value):
        self.meta[criteria] = criteria_value

    def get_criteria(self, criteria):
        return self.meta[criteria]


class CommandPackageBuilder:
    def __init__(self, command_name):
        self.command_package = CommandPackage(command_name)

    def add_description(self, description):
        self.command_package.add_criteria("description", description)
        return self

    def add_color(self, color):
        self.command_package.add_criteria("color", color)
        return self

    def add_punishment(self, punishment):
        self.command_package.add_criteria("punishment", punishment)
        return self
    
    def add_deadline(self, deadline):
        self.command_package.add_criteria("deadline", deadline)
        return self
    
    def add_validator(self, validator):
        self.command_package.add_criteria("validator", validator)
        return self
    

bot_commands = {
    "gym":
        CommandPackageBuilder("gym")
        .add_description("Upload gym proof image/selfie")
        .add_color(discord.Color.green())
        .add_punishment(-10.0)
        .add_deadline(None)
        .add_validator(None).command_package
    ,
    "socials":
        CommandPackageBuilder("socials")
        .add_description("Upload socials image/screenshot")
        .add_color(discord.Color.purple())
        .add_punishment(-15.0)
        .add_deadline(None)
        .add_validator(None).command_package
    ,
    "food":
        CommandPackageBuilder("food")
        .add_description("Upload food image/selfie")
        .add_color(discord.Color.red())
        .add_punishment(-5.0)
        .add_deadline(None)
        .add_validator(None).command_package
    ,
    "outside":
        CommandPackageBuilder("outside")
        .add_description("Upload image/selfie of you dressed outside")
        .add_color(discord.Color.blue())
        .add_punishment(-5.0)
        .add_deadline(None)
        .add_validator(None).command_package
    ,
}