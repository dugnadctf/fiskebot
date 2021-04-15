import io
import re
import urllib.request
from datetime import datetime, timezone

import ctf_model
import dateutil.parser
import db
import discord
import requests
from colorthief import ColorThief
from lxml import html

from bot import embed_help
from config import config

from discord.ext import commands
from lxml import html

class Ctftime(commands.Cog):
    def __init__(self, bot):
        self.upcoming_l = []
        self.bot = bot

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0"
    }
    upcoming_url = "https://ctftime.org/api/v1/events/"
    default_image = "https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png"

    @staticmethod
    def rgb2hex(red, green, blue):
        tohex = "#{:02x}{:02x}{:02x}".format(red, green, blue)
        return tohex

    @staticmethod
    def updatedb():
        unix_now = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())
        limit = "5"  # Max amount I can grab the json data for
        response = requests.get(Ctftime.upcoming_url, headers=Ctftime.headers, params=limit)

        ctfs = []
        for data in response.json():  # Generate list of dicts of upcoming ctfs
            ctf_start = dateutil.parser.parse(data["start"].replace("T", " ").split("+", 1)[0])
            ctf_end = dateutil.parser.parse(data["finish"].replace("T", " ").split("+", 1)[0])

            unix_start = int(ctf_start.replace(tzinfo=timezone.utc).timestamp())
            unix_end = int(ctf_end.replace(tzinfo=timezone.utc).timestamp())

            dur_dict = data["duration"]
            ctf_hours = str(dur_dict["hours"])
            ctf_days = str(dur_dict["days"])

            ctf_place = data["onsite"]
            if not ctf_place:
                ctf_place = "Online"
            else:
                ctf_place = "Onsite"

            ctf = {
                "name": data["title"],
                "start": unix_start,
                "end": unix_end,
                "dur": ctf_days + " days, " + ctf_hours + " hours",
                "url": data["url"],
                "img": data["logo"],
                "format": ctf_place + " " + data["format"],
            }
            ctfs.append(ctf)

        for ctf in ctfs:  # If the document doesn't exist: add it, if it does: update it.
            print(f"Got {ctf['name']} from ctftime")
            query = ctf["name"]
            db.ctfs.update({"name": query}, {"$set": ctf}, upsert=True)

        for ctf in db.ctfs.find():  # Delete ctfs that are over from the db
            if ctf["end"] < unix_now:
                db.ctfs.remove({"name": ctf["name"]})

    @commands.group()
    async def ctftime(self, ctx):
        if ctx.invoked_subcommand is None:
            help_text = """
`!ctftime <current/upcoming <number>>`
Returns info on ongoing CTFs from ctftime.org, or displays the `number` of upcoming events.

`!ctftime <countdown/timeleft>`
Returns remaining time until an upcoming CTF begins, or ongoing event ends.

`!ctftime top <year/country>`
Display top teams for a specified year `YYYY` or country `XX`.

`!ctftime team <team name>`
Display the top 10 events this year for a team, sorted by rating points.
"""
            await embed_help(ctx, "Help for CTFtime commands.", help_text)

    @ctftime.command()
    async def upcoming(self, ctx, params=None):
        if params is None:
            params = "3"
        else:
            pass

        response = requests.get(Ctftime.upcoming_url, headers=Ctftime.headers, params=params)
        data = response.json()

        for num in range(0, int(params)):
            ctf_title = data[num]["title"]
            ctf_start = data[num]["start"].replace("T", " ").split("+", 1)[0] + " UTC"
            ctf_end = data[num]["finish"].replace("T", " ").split("+", 1)[0] + " UTC"

            ctf_start = re.sub(":00 ", " ", ctf_start)
            ctf_end = re.sub(":00 ", " ", ctf_end)

            dur_dict = data[num]["duration"]
            ctf_hours = str(dur_dict["hours"])
            ctf_days = str(dur_dict["days"])
            ctf_link = data[num]["url"]
            ctf_image = data[num]["logo"]
            ctf_format = data[num]["format"]
            ctf_place = data[num]["onsite"]

            if not ctf_place:
                ctf_place = "Online"
            else:
                ctf_place = "Onsite"

            image = urllib.request.urlopen(Ctftime.default_image)
            image = io.BytesIO(image.read())
            color_thief = ColorThief(image)
            rgb_color = color_thief.get_color(quality=49)
            hexed = str(Ctftime.rgb2hex(*rgb_color[:3])).replace("#", "")
            f_color = int(hexed, 16)
            embed = discord.Embed(title=ctf_title, description=ctf_link, color=f_color)

            if ctf_image != "":
                embed.set_thumbnail(url=ctf_image)
            else:
                embed.set_thumbnail(url=Ctftime.default_image)

            embed.add_field(name="Duration", value=((ctf_days + " days, ") + ctf_hours) + " hours", inline=True)
            embed.add_field(name="Format", value=ctf_place + " " + ctf_format, inline=True)
            embed.add_field(name=ctf_start, value=ctf_end, inline=True)
            await ctx.channel.send(embed=embed)

    @ctftime.command()
    async def top(self, ctx, year=None):
        if not year:
            year = str(datetime.now().year)

        if not year.isnumeric():
            await self.country(ctx, year)
            return

        year = str(year)
        top_url = f"https://ctftime.org/api/v1/top/{year}/"
        response = requests.get(top_url, headers=Ctftime.headers)
        data = response.json()
        leaderboards = ""

        for team in range(10):
            rank = team + 1
            teamname = data[year][team]["team_name"]
            score = data[year][team]["points"]

            leaderboards += f"{f'[{str(rank).zfill(2)}]':4}  {f'{teamname}:':20} {score:.3f}\n"
        await ctx.send(f":triangular_flag_on_post:  **{year} CTFtime Leaderboards**```ini\n{leaderboards}```")

    @ctftime.command()
    async def team(self, ctx, team=None, year=None):
        team_id = config["team"]["id"]
        msg = None
        if team:
            msg = await ctx.send(f"Looking id for team {team}...")
            team_id = get_team_id(team)
        else:
            team = config["team"]["name"]
        if not team_id or team_id <= 0:
            ctx.send(f":warning: Unknown team `{team}`.")
            return
        if msg:
            await msg.edit(content=f"Looking up scores for {team} with id {team_id}...")
        else:
            msg = await ctx.send(f"Looking up scores for {team} with id {team_id}...")
        table = get_scores(team_id, year)
        table = [line[:2] + line[3:4] for line in table]  # remove CTF points column, not interesting

        unscored = [l for l in table if l[2] == '0.000*']  # add unscored events to the bottom

        table = [l for l in table if l[2] != '0.000*'][:11]  # get top 10 (+1 header)
        score = round(sum([float(l[2]) for l in table[1:]]), 3)

        if len(unscored) > 0:
            table.append(['', '', ''])
            table += unscored

        table.append(['', '', '', ''])
        table.append(['TOTAL', '', '', str(score)])  # add final line with total score

        table[0].insert(0, 'Nr.')
        count = 1
        for line in table[1:-2]:  # add number column for easy counting
            line.insert(0, f'[{str(count).zfill(2)}]' if line[0] else '')
            if line[0]:
                count += 1

        out = f':triangular_flag_on_post:  **Top 10 events for {team}**'
        out += '```glsl\n'
        out += format_table(table)
        out += '\n```'
        await msg.edit(content=out)

    async def country(self, ctx, country):
        table, country_name = country_scores(country.upper())
        if not table:
            raise ctf_model.TaskFailed('Invalid year or country code. Should be `YYYY` or `XX`.')
        out = f':flag_{country.lower()}:  **Top teams for {country_name}**'
        out += '```glsl\n'
        out += format_table(table)

        cut = 0
        suffix = '\n```'
        while len(out) > 2000 - len(suffix):
            out = '\n'.join(out.split('\n')[:-1])
            cut += 1
            suffix = f'\n\n+{cut} more teams\n```'

        out += suffix

        await ctx.send(out)

    @ctftime.command()
    async def current(self, ctx):
        Ctftime.updatedb()
        now = datetime.utcnow()
        unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
        running = False

        for ctf in db.ctfs.find():
            if (ctf["start"] < unix_now and unix_now < ctf["end"]):  # Check if the ctf is running
                running = True
                embed = discord.Embed(title=":red_circle: " + ctf["name"] + " IS LIVE", description=ctf["url"], color=15874645)
                start = datetime.utcfromtimestamp(ctf["start"]).strftime("%Y-%m-%d %H:%M:%S") + " UTC"
                end = datetime.utcfromtimestamp(ctf["end"]).strftime("%Y-%m-%d %H:%M:%S") + " UTC"
                if ctf["img"] != "":
                    embed.set_thumbnail(url=ctf["img"])
                else:
                    embed.set_thumbnail(url=Ctftime.default_image)

                embed.add_field(name="Duration", value=ctf["dur"], inline=True)
                embed.add_field(name="Format", value=ctf["format"], inline=True)
                embed.add_field(name=start, value=end, inline=True)
                await ctx.channel.send(embed=embed)

        if not running:  # No ctfs were found to be running
            await ctx.send("No CTFs currently running! Check out !ctftime countdown, and !ctftime upcoming to see when ctfs will start!")

    # Return the timeleft in the ctf in days, hours, minutes, seconds

    @ctftime.command()
    async def timeleft(self, ctx):
        Ctftime.updatedb()
        now = datetime.utcnow()
        unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
        running = False
        for ctf in db.ctfs.find():
            if ctf["start"] < unix_now and unix_now < ctf["end"]:  # Check if the ctf is running
                running = True
                time = ctf["end"] - unix_now
                days = time // (24 * 3600)
                time = time % (24 * 3600)
                hours = time // 3600
                time %= 3600
                minutes = time // 60
                time %= 60
                seconds = time
                await ctx.send(f"```ini\n{ctf['name']} ends in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```{ctf['url']}")

        if not running:
            await ctx.send("No ctfs are running! Use !ctftime upcoming or !ctftime countdown to see upcoming ctfs")

    @ctftime.command()
    async def countdown(self, ctx, params=None):
        Ctftime.updatedb()
        unix_now = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())

        if params is None:
            self.upcoming_l = []
            index = ""
            for ctf in db.ctfs.find():
                if ctf["start"] > unix_now:
                    self.upcoming_l.append(ctf)
            for i, ctf in enumerate(self.upcoming_l):
                index += f"[{i + 1}] {ctf['name']}\n"

            await ctx.send(f"Type !ctftime countdown <number> to select.\n```ini\n{index}```")

        else:
            if self.upcoming_l != []:
                index = int(params) - 1
                target = self.upcoming_l[index]
                seconds = target["start"] - unix_now
                await ctx.send(f"```ini\n{target['name']} starts in: {format_seconds(seconds)}```\n{target['url']}")

            else:
                for ctf in db.ctfs.find():
                    if ctf["start"] > unix_now:
                        self.upcoming_l.append(ctf)
                index = int(params) - 1
                target = self.upcoming_l[index]
                seconds = target["start"] - unix_now

                await ctx.send(f"```ini\n{target['name']} starts in: {format_seconds(seconds)}```{target['url']}")


def format_seconds(seconds):
    days = seconds // (24 * 3600)
    seconds = seconds % (24 * 3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return f'[{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]'


def country_scores(country):
    url = f"https://ctftime.org/stats/{country}"

    response = requests.get(url, headers=Ctftime.headers)
    if response.status_code != 200:
        return None, None
    doc = html.fromstring(response.content)

    country_name = doc.xpath('//ul[@class="breadcrumb"]//li[@class="active"]')[0].text_content()

    lines = doc.xpath('//div[@class="container"]//table[@class="table table-striped"]//tr')
    column_names = ['Worldwide', 'Country', 'Name', 'Points', 'Events']
    lines = lines[1:]
    table = []
    for line in lines:
        columns = line.xpath('.//td')
        columns = [c.text_content().replace('\t', ' ') for c in columns]
        columns = columns[0:1] + columns[2:3] + columns[4:]
        table.append(columns)

    table = [column_names] + table
    return table, country_name


def get_scores(team_id, year=None):
    url = f"https://ctftime.org/team/{team_id}"

    data = requests.get(url, headers=Ctftime.headers).content
    doc = html.fromstring(data)
    if not year:
        now = datetime.now()
        year = now.year
    lines = doc.xpath(f'//div[@id="rating_{str(year)}"]//table//tr')
    column_names = lines[0].xpath(".//th/text()")
    column_names = ['Place', 'Event', 'CTF Points', 'Rating Points']
    lines = lines[1:]
    table = []
    for line in lines:
        columns = line.xpath('.//td')
        columns = [c.text_content().replace('\t', ' ') for c in columns[1:]]
        table.append(columns)

    table.sort(key=lambda l: float(l[3].replace("*", "")), reverse=True)
    table = [column_names] + table
    return table


def get_team_id(team_name):
    ses = requests.Session()
    url = 'https://ctftime.org/stats/'
    response = ses.get(url, headers=Ctftime.headers)
    doc = html.fromstring(response.content)
    token = doc.xpath('//input[@name="csrfmiddlewaretoken"]')[0]

    url = "https://ctftime.org/team/list/"
    headers = {'Referer': 'https://ctftime.org/stats/'}
    headers.update(Ctftime.headers)
    response = ses.post(url, data={'team_name': team_name, 'csrfmiddlewaretoken': token.value}, headers=headers)
    team_id = response.url.split("/")[-1]
    if team_id.isnumeric():
        return int(team_id)
    return -1


def format_table(table, seperator='      '):
    widths = [max(len(line[i]) for line in table) for i in range(len(table[0]))]
    return '\n'.join([seperator.join([c.ljust(w) for w, c in zip(widths, line)]) for line in table])


def setup(bot):
    bot.add_cog(Ctftime(bot))
