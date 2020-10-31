import random
import traceback
import asyncio
import colorama
import discord
import ctf
import db

from discord.ext import commands
from config import config
from eptbot import bot, logging


@bot.event
async def on_ready():
    print(("<" + bot.user.name) + " Online>")
    print(f"discord.py {discord.__version__}\n")
    await bot.change_presence(activity=discord.Game(name=f'{config["prefix"]}help / {config["prefix"]}report "issue"'))


@bot.event
async def on_message(message):
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
    logging.error("".join(traceback.format_exception(type(err), err, err.__traceback__)))
    print(colorama.Style.BRIGHT + colorama.Fore.RED + f"Error occured with: {ctx.command}\n{err}\n")
    print(colorama.Style.RESET_ALL)
    if isinstance(err, commands.MissingPermissions):
        await ctx.send("You do not have permission to do that! ¯\\_(ツ)_/¯")  # pylint: disable=anomalous-backslash-in-string
    elif isinstance(err, commands.BotMissingPermissions):
        await ctx.send(f""":cry: I can\'t do that. Please ask server ops
        to add all the permission for me!

        ```{str(err)}```""")
    elif isinstance(err, commands.DisabledCommand):
        await ctx.send(":skull: Command has been disabled!")
    elif isinstance(err, commands.CommandNotFound):
        await ctx.send("Invalid command passed. Use !help.")
    elif isinstance(err, ctf.TaskFailed):
        await ctx.send(f":bangbang: {str(err)}")
    elif isinstance(err, commands.NoPrivateMessage):
        await ctx.send(":bangbang: This command cannot be used in PMs.")
    else:
        msg = await ctx.send(f"An error has occurred... :disappointed: \n`{err}`\n")
        await asyncio.sleep(15)
        await msg.delete()


@bot.event
async def on_raw_reaction_add(payload):
    # check if the user is not the bot
    guild = bot.get_guild(payload.guild_id)
    chan = bot.get_channel(payload.channel_id)
    team = db.teamdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    member = guild.get_member(payload.user_id)
    if guild and member and chan:
        if team:
            role = guild.get_role(team["role_id"])
            await member.add_roles(role, reason="User wanted to join team")


@bot.event
async def on_raw_reaction_remove(payload):
    # check if the user is not the bot
    guild = bot.get_guild(payload.guild_id)
    team = db.teamdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    member = guild.get_member(payload.user_id)
    if guild and member:
        if team:
            role = guild.get_role(team["role_id"])
            await member.remove_roles(role, reason="User wanted to leave team")


@bot.command()
async def source(ctx):
    await ctx.send(f"Source: https://github.com/ept-team/eptbot\nForked from: {src_fork2}\nWho again forked from: {src_fork1}")


@bot.command()
async def help(ctx, page=None):
    info = help_page if not page or page == "1" else help_page_2
    await embed_help(ctx, '!request "x" - request a feature', info)

# Bot sends a dm to creator with the name of the user and their request.


@bot.command()
async def request(ctx, feature):
    for cid in config["maintainers"]:
        creator = bot.get_user(cid)
        authors_name = str(ctx.author)
        await creator.send(f""":pencil: {authors_name}: {feature}""")
    await ctx.send(f""":pencil: Thanks, "{feature}" has been requested!""")

# Bot sends a dm to creator with the name of the user and their report.


@bot.command()
async def report(ctx, error_report):
    for cid in config["maintainers"]:
        creator = bot.get_user(cid)
        authors_name = str(ctx.author)
        await creator.send(f""":triangular_flag_on_post: {authors_name}: {error_report}""")
    await ctx.send(f""":triangular_flag_on_post: Thanks for the help, "{error_report}" has been reported!""")


@bot.command()
async def amicool(ctx):
    authors_name = str(ctx.author)

    if any((name in authors_name for name in config["coold_names"])):
        await ctx.send("You are very cool")
    else:
        await ctx.send("lolno")


@commands.command(aliases=["5050", "flip"])
async def cointoss(ctx):
    choice = random.randint(1, 2)

    if choice == 1:
        await ctx.send("heads")

    if choice == 2:
        await ctx.send("tails")


@bot.command()
async def setup(ctx):
    guild = ctx.guild

    overwrites = {guild.default_role: ctf.basic_disallow, guild.me: ctf.basic_allow}
    existing_categories = [category.name for category in ctx.guild.categories]
    for category in [config["categories"]["working"], config["categories"]["done"]]:
        if category not in existing_categories:
            await ctx.guild.create_category(category, overwrites=overwrites)

    await ctx.send("Setup successfull! :tada:")
