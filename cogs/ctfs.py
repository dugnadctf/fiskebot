import urllib
import requests
import re
import json
import base64
import binascii
import collections
import string
import urllib.parse
from urllib.request import urlopen
import io
import time
import datetime
from pymongo import MongoClient
from pprint import pprint
from random import randint
from datetime import *
from dateutil.parser import parse

from colorthief import ColorThief
import discord
from discord.ext import commands

from trim import trim_nl
from help_info import ctf_help_text, chal_help_text

from . import ctfmodel
from .mongo import *


class Ctftime(commands.Cog):

    def __init__(self, bot):
        self.upcoming_l = []
        self.bot = bot

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
        }
    upcoming_url = 'https://ctftime.org/api/v1/events/'
    default_image = 'https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png'
    @staticmethod
    def rgb2hex(r, g, b):
        tohex = '#{:02x}{:02x}{:02x}'.format(r, g, b)
        return tohex

    @staticmethod
    def updatedb():
        now = datetime.utcnow()
        unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
        limit = '5' # Max amount I can grab the json data for
        response = requests.get(Ctftime.upcoming_url, headers=Ctftime.headers, params=limit)
        jdata = response.json()
        
        info = []
        for num, i in enumerate(jdata): # Generate list of dicts of upcoming ctfs
            ctf_title = jdata[num]['title']
            (ctf_start, ctf_end) = (parse(jdata[num]['start'].replace('T', ' ').split('+', 1)[0]), parse(jdata[num]['finish'].replace('T', ' ').split('+', 1)[0]))
            (unix_start, unix_end) = (int(ctf_start.replace(tzinfo=timezone.utc).timestamp()), int(ctf_end.replace(tzinfo=timezone.utc).timestamp()))
            dur_dict = jdata[num]['duration']
            (ctf_hours, ctf_days) = (str(dur_dict['hours']), str(dur_dict['days']))
            ctf_link = jdata[num]['url']
            ctf_image = jdata[num]['logo']
            ctf_format = jdata[num]['format']
            ctf_place = jdata[num]['onsite']
            if ctf_place == False:
              ctf_place = 'Online'
            else:
              ctf_place = 'Onsite'
            
            ctf = {
                'name': ctf_title,
                'start': unix_start,
                'end': unix_end,
                'dur': ctf_days+' days, '+ctf_hours+' hours',
                'url': ctf_link,
                'img': ctf_image,
                'format': ctf_place+' '+ctf_format
                 }
            info.append(ctf)
        
        for ctf in info: # If the document doesn't exist: add it, if it does: update it.
            print(f"Got {ctf['name']} from ctftime")
            query = ctf['name']
            ctfs.update({'name': query}, {"$set":ctf}, upsert=True)
        
        for ctf in ctfs.find(): # Delete ctfs that are over from the db
            if ctf['end'] < unix_now:
                ctfs.remove({'name': ctf['name']})

    @commands.group()
    async def ctftime(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed.  Use !help.')

    @ctftime.command()
    async def upcoming(self, ctx, params=None):
        if params == None:
            params = '3'
        else:
            pass
        
        response = requests.get(Ctftime.upcoming_url, headers=Ctftime.headers, params=params)
        data = response.json()
        
        for num in range(0, int(params)):
            ctf_title = data[num]['title']
            (ctf_start, ctf_end) = (data[num]['start'].replace('T', ' ').split('+', 1)[0] + ' UTC', data[num]['finish'].replace('T', ' ').split('+', 1)[0] + ' UTC')
            (ctf_start, ctf_end) = (re.sub(':00 ', ' ', ctf_start), re.sub(':00 ', ' ', ctf_end))
            dur_dict = data[num]['duration']
            (ctf_hours, ctf_days) = (str(dur_dict['hours']), str(dur_dict['days']))
            ctf_link = data[num]['url']
            ctf_image = data[num]['logo']
            ctf_format = data[num]['format']
            ctf_place = data[num]['onsite']
            
            if ctf_place == False:
                ctf_place = 'Online'
            else:
                ctf_place = 'Onsite'
            
            # if ctf_image != '':
            #     fd = urlopen(ctf_image) # 403 is on this line, no longer able to access this?
            # else:
            #     fd = urlopen(Ctftime.default_image)
            fd = urlopen(Ctftime.default_image)
            f = io.BytesIO(fd.read())
            color_thief = ColorThief(f)
            rgb_color = color_thief.get_color(quality=49)
            hexed = str(Ctftime.rgb2hex(*rgb_color[:3])).replace('#', '')
            f_color = int(hexed, 16)
            embed = discord.Embed(title=ctf_title, description=ctf_link, color=f_color)
            
            if ctf_image != '':
                embed.set_thumbnail(url=ctf_image)
            else:
                embed.set_thumbnail(url=Ctftime.default_image)
            
            embed.add_field(name='Duration', value=((ctf_days + ' days, ') + ctf_hours) + ' hours', inline=True)
            embed.add_field(name='Format', value=(ctf_place + ' ') + ctf_format, inline=True)
            embed.add_field(name='─' * 23, value=(ctf_start + ' -> ') + ctf_end, inline=True)
            await ctx.channel.send(embed=embed)

    @ctftime.command()
    async def top(self, ctx, params = None):
        if not params:
            params = '2018'
        
        params = str(params)
        top_url = 'https://ctftime.org/api/v1/top/' + params + '/'
        response = requests.get(top_url, headers=Ctftime.headers)
        data = response.json()
        leaderboards = ''
        
        for team in range(10):
            rank = team + 1
            teamname = data[params][team]['team_name']
            score = data[params][team]['points']
            
            if team != 9:
                leaderboards += f'''
[{rank}]    {teamname}: {score}
'''
            else:
                leaderboards += f'''
[{rank}]   {teamname}: {score}
'''
        await ctx.send(f''':triangular_flag_on_post:  **{params} CTFtime Leaderboards**```ini
{leaderboards}```''')

    @ctftime.command()
    async def current(self, ctx, params=None):
        Ctftime.updatedb()
        now = datetime.utcnow()
        unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
        running = False
        
        for ctf in ctfs.find():
            if ctf['start'] < unix_now and ctf['end'] > unix_now: # Check if the ctf is running
                running = True
                embed = discord.Embed(title=':red_circle: ' + ctf['name']+' IS LIVE', description=ctf['url'], color=15874645)
                start = datetime.utcfromtimestamp(ctf['start']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
                end = datetime.utcfromtimestamp(ctf['end']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
                if ctf['img'] != '':
                    embed.set_thumbnail(url=ctf['img'])
                else:
                    embed.set_thumbnail(url=Ctftime.default_image)
                 
                embed.add_field(name='Duration', value=ctf['dur'], inline=True)
                embed.add_field(name='Format', value=ctf['format'], inline=True)
                embed.add_field(name='─' * 23, value=start+' -> '+end, inline=True)
                await ctx.channel.send(embed=embed)
        
        if running == False: # No ctfs were found to be running
            await ctx.send("No CTFs currently running! Check out !ctftime countdown, and !ctftime upcoming to see when ctfs will start!")

    # Return the timeleft in the ctf in days, hours, minutes, seconds
    @ctftime.command()
    async def timeleft(self, ctx, params=None):
        Ctftime.updatedb()
        now = datetime.utcnow()
        unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
        running = False
        for ctf in ctfs.find():
           if ctf['start'] < unix_now and ctf['end'] > unix_now: # Check if the ctf is running
              running = True
              time = ctf['end'] - unix_now 
              days = time // (24 * 3600)
              time = time % (24 * 3600)
              hours = time // 3600
              time %= 3600
              minutes = time // 60
              time %= 60
              seconds = time
              await ctx.send(f"```ini\n{ctf['name']} ends in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```\n{ctf['url']}")
        
        if running == False:
            await ctx.send('No ctfs are running! Use !ctftime upcoming or !ctftime countdown to see upcoming ctfs')

    @ctftime.command()
    async def countdown(self, ctx, params=None):
        Ctftime.updatedb()
        now = datetime.utcnow()
        unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
        
        if params == None:
            self.upcoming_l = []
            index = ""
            for ctf in ctfs.find():
                if ctf['start'] > unix_now:
                  self.upcoming_l.append(ctf)
            for i, c in enumerate(self.upcoming_l):
               index += f"\n[{i + 1}] {c['name']}\n"
            
            await ctx.send(f"Type !ctftime countdown <number> to select.\n```ini\n{index}```")
        
        else:
            if self.upcoming_l != []:
                x = int(params) - 1     
                start = datetime.utcfromtimestamp(self.upcoming_l[x]['start']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
                end = datetime.utcfromtimestamp(self.upcoming_l[x]['end']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
                  
                time = self.upcoming_l[x]['start'] - unix_now 
                days = time // (24 * 3600)
                time = time % (24 * 3600)
                hours = time // 3600
                time %= 3600
                minutes = time // 60
                time %= 60
                seconds = time
                
                await ctx.send(f"```ini\n{self.upcoming_l[x]['name']} starts in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```\n{self.upcoming_l[x]['url']}")
            else: # TODO: make this a function, too much repeated code here.
                for ctf in ctfs.find():
                    if ctf['start'] > unix_now:
                      self.upcoming_l.append(ctf)
                x = int(params) - 1     
                start = datetime.utcfromtimestamp(self.upcoming_l[x]['start']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
                end = datetime.utcfromtimestamp(self.upcoming_l[x]['end']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
                  
                time = self.upcoming_l[x]['start'] - unix_now 
                days = time // (24 * 3600)
                time = time % (24 * 3600)
                hours = time // 3600
                time %= 3600
                minutes = time // 60
                time %= 60
                seconds = time
                
                await ctx.send(f"```ini\n{self.upcoming_l[x]['name']} starts in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```\n{self.upcoming_l[x]['url']}")


async def respond(ctx, fn, *args):
    guild = ctx.channel.guild
    async with ctx.channel.typing():
        for chan_id, msg in await fn(*args):
            chan = guild.get_channel(chan_id) if chan_id else ctx.channel
            await chan.send(msg)

def check_name(name):
    if len(name) > 32:
        raise ctfmodel.TaskFailed('Challenge name is too long!')
    # TODO sanitize

def chk_fetch_team(ctx):
    team = ctfmodel.CtfTeam.fetch(ctx.channel.guild, ctx.channel.id)
    if not team:
        raise ctfmodel.TaskFailed('Please type this command in a ctf channel.')
    return team

def chk_fetch_chal(ctx):
    chal = ctfmodel.Challenge.fetch(ctx.channel.guild, ctx.channel.id)
    if not chal:
        raise ctfmodel.TaskFailed('Please type this command in a challenge ' + \
                'channel. You may need to join a challenge first.')
    return chal

def parse_user(guild, user):
    mat = re.match(r'<@([0-9]+)>$', user)
    if mat:
        ret = guild.get_member(int(mat[1]))
    else:
        ret = guild.get_member_named(user)

    if not ret:
        raise ctfmodel.TaskFailed(f'Invalid username: "{user}"')
    return ret
    
def verify_owner():
    def predicate(ctx):
        chk_fetch_chal(ctx).check_done(ctx.author)
        return True

    return commands.check(predicate)

class Ctfs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.challenges = {}
        self.ctfname = ""

    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.command()
    async def create_ctf(self, ctx, name):
        guild = ctx.channel.guild

        # Create channel
        chan = await guild.create_text_channel(name=name, 
                topic=f'General talk for {name} CTF event.')
        msg = await chan.send(trim_nl(f'''Welcome to {name}. Here you can do
        general discussion about this event. Also use this this place to type
        `ctf` related commands. Here is a list of commands just for
        reference:\n\n'''))
        await msg.pin()
        msg = await chan.send(ctf_help_text + chal_help_text)
        await msg.pin()

        # Create role
        role = await guild.create_role(name=f'{name}_team', mentionable=True)

        await respond(ctx, ctfmodel.CtfTeam.create, guild, name, chan.id, role.id)

    @commands.guild_only()
    @commands.group()
    async def ctf(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed. Use !ctf help.')

    @ctf.command('help')
    async def ctf_help(self, ctx):
        emb = discord.Embed(description=ctf_help_text, colour=4387968)
        emb.set_author(name='CTF team help topic')
        await ctx.send(embed=emb)


    @commands.bot_has_permissions(manage_channels=True)
    @ctf.command()
    async def add(self, ctx, name):
        check_name(name)
        await respond(ctx, chk_fetch_team(ctx).add_chal, name)

    @commands.bot_has_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def delete(self, ctx, name):
        check_name(name)
        await respond(ctx, chk_fetch_team(ctx).del_chal, name)

    @commands.bot_has_permissions(manage_roles=True)
    @ctf.command('leave')
    async def leave_ctf(self, ctx):
        await respond(ctx, chk_fetch_team(ctx).leave, ctx.author)

    @commands.bot_has_permissions(manage_roles=True)
    @ctf.command()
    async def join(self, ctx):
        await respond(ctx, chk_fetch_team(ctx).join, ctx.author)

    @ctf.command()
    async def working(self, ctx, chalname):
        chk_fetch_team(ctx)
        chal = ctfmodel.Challenge.find(ctx.channel.guild, ctx.channel.id, chalname)
        await respond(ctx, chal.working, ctx.author)

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def archive(self, ctx):
        # TODO: drop all roles
        await respond(ctx, chk_fetch_team(ctx).archive)

    @ctf.command()
    async def list(self, ctx):
        chals = chk_fetch_team(ctx).challenges
        if len(chals) == 0:
            await ctx.send('No challenges added...')
            return

        msg_len = 50
        lines = []
        for chal in chals:
            l = f'[{chal.team.name}] [{chal.name}] - {chal.status}'
            msg_len += len(l) + 1
            if msg_len > 1000: # Over limit
                lines = '\n'.join(lines)
                await ctx.send(f'```ini\n{lines}```')
                lines = []
                msg_len = len(l) + 51
            lines.append(l)

        lines = '\n'.join(lines)
        await ctx.send(f'```ini\n{lines}```')
    
    @commands.guild_only()
    @commands.group()
    async def chal(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed.  Use !help.')

    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @chal.command()
    async def done(self, ctx, *withlist):
        guild = ctx.channel.guild
        users = [parse_user(guild, u) for u in withlist]
        await respond(ctx, chk_fetch_chal(ctx).done, ctx.author, users)

    @chal.command('help')
    async def chal_help(self, ctx):
        emb = discord.Embed(description=chal_help_text, colour=4387968)
        emb.set_author(name='Challenge help topic')
        await ctx.send(embed=emb)

    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @chal.command()
    async def undone(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).undone)

    @commands.bot_has_permissions(manage_channels=True)
    @chal.command('leave')
    async def leave_chal(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).leave, ctx.author)

    @commands.command()
    async def htb(self, ctx):
        twitter_page = requests.get('https://twitter.com/hackthebox_eu')
        all_content = str(twitter_page.text.encode('utf-8'))
        tweet = re.search('\\w+ will go live \\d{2}/\\d{2}/\\d{4} at \\d{2}:\\d{2}:\\d{2} UTC', all_content)
        match = tweet.group(0)
        await ctx.send(match + '\nhttps://hackthebox.eu')

def setup(bot):
    bot.add_cog(Ctfs(bot))
    bot.add_cog(Ctftime(bot))
