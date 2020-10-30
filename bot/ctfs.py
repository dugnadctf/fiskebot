import re
import requests

from discord.ext import commands

import db
import ctf as ctfmodel


class Ctfs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.challenges = {}
        self.ctfname = ""

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.guild_only()
    @commands.command()
    async def create(self, ctx, name):
        emoji = '🏃'
        messages = await respond_with_reaction(ctx, emoji, ctfmodel.CtfTeam.create, ctx.channel.guild, name)
        db.teamdb[str(ctx.channel.guild.id)].update_one(
            {"name": name}, {"$set": {"msg_id": messages[0].id}}
        )

    @commands.guild_only()
    @commands.group()
    async def ctf(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed. Use !ctf help.")

    @ctf.command("help")
    async def ctf_help(self, ctx):
        await embed_help(ctx, "CTF team help topic", ctf_help_text)

    @commands.bot_has_permissions(manage_channels=True)
    @ctf.command()
    async def add(self, ctx, name):
        name = check_name(name)
        emoji = '🔨'
        await respond_with_reaction(ctx, emoji,  chk_fetch_team(ctx).add_chal, name)

    @commands.bot_has_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def delete(self, ctx, name):
        name = check_name(name)
        await respond(ctx, chk_fetch_team(ctx).del_chal, name)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.command("leave")
    async def leave_ctf(self, ctx):
        await respond(ctx, chk_fetch_team(ctx).leave, ctx.author)

    @commands.bot_has_permissions(manage_roles=True)
    @ctf.command("invite")
    async def invite_ctf(self, ctx, user):
        user = parse_user(ctx.channel.guild, user)
        await respond(ctx, chk_fetch_team(ctx).invite, ctx.author, user)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.command()
    async def join(self, ctx, name):
        await respond(ctx, chk_fetch_team_by_name(ctx, name).join, ctx.author)

    @ctf.command()
    async def working(self, ctx, chalname):
        chk_fetch_team(ctx)
        chal = ctfmodel.Challenge.find(ctx.channel.guild, ctx.channel.id, chalname)
        await respond(ctx, chal.working, ctx.author)

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def archive(self, ctx):
        await respond(ctx, chk_fetch_team(ctx).archive)

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def unarchive(self, ctx):
        await respond(ctx, chk_fetch_team(ctx).unarchive)

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def export(self, ctx):
        await respond(ctx, ctfmodel.export, ctx, ctx.author)

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def deletectf(self, ctx):
        await respond(ctx, ctfmodel.delete, ctx, ctx.author)

    @ctf.command()
    async def list(self, ctx):
        chals = chk_fetch_team(ctx).challenges
        if len(chals) == 0:
            await ctx.send("No challenges added...")
            return

        msg_len = 50
        lines = []
        for chal in chals:
            l = f"[{chal.team.name}] [{chal.name}] - {chal.status}"
            msg_len += len(l) + 1
            if msg_len > 1000:  # Over limit
                lines = "\n".join(lines)
                await ctx.send(f"```ini\n{lines}```")
                lines = []
                msg_len = len(l) + 51
            lines.append(l)

        lines = "\n".join(lines)
        await ctx.send(f"```ini\n{lines}```")

    @commands.guild_only()
    @commands.group()
    async def chal(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use !help.")

    @commands.bot_has_permissions(manage_channels=True)
    @chal.command("invite")
    async def invite_chal(self, ctx, user):
        user = parse_user(ctx.channel.guild, user)
        await respond(ctx, chk_fetch_chal(ctx).invite, ctx.author, user)

    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @chal.command()
    async def done(self, ctx, *withlist):
        guild = ctx.channel.guild
        users = [parse_user(guild, u) for u in withlist]
        await respond(ctx, chk_fetch_chal(ctx).done, ctx.author, users)

    @chal.command("help")
    async def chal_help(self, ctx):
        await embed_help(ctx, "Challenge help topic", chal_help_text)

    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @chal.command()
    async def undone(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).undone)

    @commands.bot_has_permissions(manage_channels=True)
    @chal.command("leave")
    async def leave_chal(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).leave, ctx.author)

    @commands.command()
    async def htb(self, ctx):
        twitter_page = requests.get("https://twitter.com/hackthebox_eu")
        all_content = str(twitter_page.text.encode("utf-8"))
        tweet = re.search(
            "\\w+ will go live \\d{2}/\\d{2}/\\d{4} at \\d{2}:\\d{2}:\\d{2} UTC",
            all_content,
        )
        match = tweet.group(0)
        await ctx.send(match + "\nhttps://hackthebox.eu")


async def respond(ctx, fn, *args):
    messages = []
    guild = ctx.channel.guild
    async with ctx.channel.typing():
        for chan_id, msg in await fn(*args):
            chan = guild.get_channel(chan_id) if chan_id else ctx.channel
            msg = await chan.send(msg)
            messages.append(msg)
    return messages


async def respond_with_reaction(ctx, emoji, fn, *args):
    messages = []
    guild = ctx.channel.guild
    async with ctx.channel.typing():
        for chan_id, msg in await fn(*args):
            chan = guild.get_channel(chan_id) if chan_id else ctx.channel
            msg = await chan.send(msg)
            await msg.add_reaction(emoji)
            messages.append(msg)
    return messages


def check_name(name):
    if len(name) > 32:
        raise ctfmodel.TaskFailed("Challenge name is too long!")

    if not re.match(r"[-.!0-9A-Za-z ]+$", name):
        raise ctfmodel.TaskFailed("Challenge contains invalid characters!")

    # Replace spaces with a dash, because discord does it :/
    return re.sub(r" +", "-", name).lower()


def chk_fetch_team_by_name(ctx, name):
    channels = ctx.guild.channels
    if len([channel.id for channel in channels if name == channel.name]) > 1:
        raise ctfmodel.TaskFailed("Multiple channels with same name exists")

    found_channel_id = ""
    for channel in channels:
        if channel.name == name:
            found_channel_id = channel.id
    team = ctfmodel.CtfTeam.fetch(ctx.channel.guild, found_channel_id)
    if not team:
        raise ctfmodel.TaskFailed("Failed to join CTF")
    return team


def chk_fetch_team(ctx):
    team = ctfmodel.CtfTeam.fetch(ctx.channel.guild, ctx.channel.id)
    if not team:
        raise ctfmodel.TaskFailed("Please type this command in a ctf channel.")
    return team


def chk_fetch_chal(ctx):
    chal = ctfmodel.Challenge.fetch(ctx.channel.guild, ctx.channel.id)
    if not chal:
        raise ctfmodel.TaskFailed(
            "Please type this command in a challenge "
            + "channel. You may need to join a challenge first."
        )
    return chal


def parse_user(guild, user):
    mat = re.match(r"<@([0-9]+)>$", user)
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


def setup(bot):
    bot.add_goc(Ctfs(bot))
