import asyncio
import urllib
import requests
import re
import random
import json
import base64
import binascii
import collections
import string
import sys
import os
import urllib.parse
from urllib.request import urlopen
import io
from dateutil.parser import parse
import time
import datetime
from datetime import timezone
from datetime import datetime
import discord
from discord.ext.commands import *
from discord.ext import commands
from colorthief import ColorThief
from help_info import *
from auth import *

import traceback
import logging as log

from trim import trim_nl
from cogs.ctfmodel import TaskFailed

creator_id = [412077060207542284, 491610275993223170]

client = discord.Client()
bot = commands.Bot(command_prefix='!')
extensions = ['encoding_decoding', 'cipher', 'ctfs', 'utility', 'settings']
bot.remove_command('help')
blacklisted = []
cool_names = ['nullpxl', 'Test_Monkey', 'Yiggles', 'JohnHammond', 'voidUpdate',
        'Michel Ney', 'theKidOfArcrania', 'knapstack'] # This is intended to be able to be circumvented.
# If you do something like report a bug with the report command (OR GITHUB), e.g, >report "a bug", you might be added to the list!

@bot.event
async def on_ready():
    print(('<' + bot.user.name) + ' Online>')
    print(discord.__version__)
    await bot.change_presence(activity=discord.Game(name='!help / !report "issue"'))

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
    if isinstance(err, MissingPermissions):
        await ctx.send('You do not have permission to do that! ¯\_(ツ)_/¯')
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
    await ctx.send(src_fork)
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
        bot.load_extension('cogs.' + extension)
    bot.run(auth_token)
