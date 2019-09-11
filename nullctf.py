import asyncio
import random
from colorama import Back, Fore, Style
import sys
import os
import discord
from discord.ext.commands import MissingPermissions, BotMissingPermissions, DisabledCommand, CommandNotFound, NoPrivateMessage, Bot
from discord.ext import commands
from vars.help_info import help_page, help_page_2, embed_help, src
from util import getVal, trim_nl
from pymongo import MongoClient

import traceback
import logging as log

from models.ctf import *

creator_id = [412077060207542284, 491610275993223170]

client = discord.Client()
PREFIX = "!"
# TODO: easter egg if typing != :)
bot = commands.Bot(command_prefix=PREFIX)
extensions = ['encoding_decoding', 'cipher', 'ctfs', 'utility']
bot.remove_command('help')
blacklisted = []
cool_names = ['KFBI']
CREATOR_ID = 87606885405982720
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


@bot.event
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
    log.error(f'Ignoring exception at {evt_type}')
    log.error(traceback.format_exc())


@bot.event
async def on_command_error(ctx, err):
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
    else:
        await ctx.send('An error has occurred... :disappointed:')
        log.error(f'Ignoring exception in command {ctx.command}')
        log.error(''.join(traceback.format_exception(type(err), err,
                                                     err.__traceback__)))

# Sends the github link.
@bot.command()
async def source(ctx):
    await ctx.send(GIT_URL)
    await ctx.send(f'Forked from: {src}')


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


if __name__ == '__main__':
    #sys.path.insert(1, os.getcwd() + '/cogs/')
    for extension in extensions:
        # bot.load_extension(extension)
        bot.load_extension('cogs.' + extension)

    bot.run(getVal("TOKEN"))
