import logging

import discord
from discord.ext import commands

from config import config

LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"

logging.basicConfig(format=LOG_FORMAT, level=logging.WARN)

client = discord.Client()
bot = commands.Bot(command_prefix=config["prefix"])
bot.remove_command("help")

if __name__ == "__main__":
    bot.load_extension("core")
    bot.load_extension("ctftime")
    bot.load_extension("ctfs")
    bot.run(config["token"])
