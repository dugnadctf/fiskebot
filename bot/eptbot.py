import logging

import discord
from discord.ext import commands

from config import config

FORMAT = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"

logging.basicConfig(format=FORMAT, level=logging.WARN)

default_categories = ["working", "done"]

client = discord.Client()
bot = commands.Bot(command_prefix=config["prefix"])
bot.remove_command("help")

if __name__ == "__main__":
    bot.load_extension("core")
    bot.load_extension("ctftime")
    bot.load_extension("ctfs")
    bot.run(config["token"])
