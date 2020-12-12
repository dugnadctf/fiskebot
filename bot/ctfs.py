import re

from discord.ext import commands

from config import config
import db
import ctf_model
import eptbot


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

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.guild_only()
    @commands.command()
    async def create(self, ctx, *name):
        name = ' '.join(name)
        emoji = '🏃'
        messages = await respond_with_reaction(ctx, emoji, ctf_model.CtfTeam.create, ctx.channel.guild, name)
        db.teamdb[str(ctx.channel.guild.id)].update_one({"name": name}, {"$set": {"msg_id": messages[0].id}})

    @commands.guild_only()
    @commands.group()
    async def ctf(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.ctf_help(ctx)

    @ctf.command("help")
    async def ctf_help(self, ctx):
        help = """
These commands are callable from a main CTF channel.

`!ctf add "<challenge>"`
Add a `challenge` and a respective channel. Challenge names may be altered to meet Discord restrictions.
(i.e. no special characters, less than 32 characters long, etc...)

`!ctf invite <user>`
Invites a user to CTF team - `user` is granted the CTF role.

`!ctf delete "<challenge>"`
Remove a challenge (this requires the bot has manage channels permissions).
This will **not** automatically delete the respective private channel. Server staff can remove manually if required.

`!ctf archive`
Archives this ctf and all the respective challenges (this requires the bot has manage channels permissions).

`!ctf unarchive`
Unarchives this ctf and all the respective challenges (this requires the bot has manage channels permissions).

""".replace("!", config["prefix"])
        await eptbot.embed_help(ctx, "Help for CTF commands", help)

    @commands.bot_has_permissions(manage_channels=True)
    @commands.command("add")
    async def add_alias(self, ctx, *name):
        await self.add(ctx, *name)

    @commands.bot_has_permissions(manage_channels=True)
    @ctf.command()
    async def add(self, ctx, *name):
        name = '_'.join(name)
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
        user = await parse_user(ctx.channel.guild, user)
        await respond(ctx, chk_fetch_team(ctx).invite, ctx.author, user)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.command()
    async def join(self, ctx, name=None):
        if name is None:
            await ctx.send(f'Please specify a CTF to join:\n```{config["prefix"]}join <ctf name>```')
        await respond(ctx, chk_fetch_team_by_name(ctx, name).join, ctx.author)

    @ctf.command()
    async def working(self, ctx, chalname):
        chk_fetch_team(ctx)
        chal = ctf_model.Challenge.find(ctx.channel.guild, ctx.channel.id, chalname)
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
        await respond(ctx, ctf_model.export, ctx, ctx.author)

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def deletectf(self, ctx):
        await respond(ctx, ctf_model.delete, ctx, ctx.author)

    @ctf.command()
    async def list(self, ctx):
        chals = chk_fetch_team(ctx).challenges
        if len(chals) == 0:
            await ctx.send("No challenges added...")
            return

        msg_len = 50
        lines = []
        for chal in chals:
            l = f"[{chal.team.name}] [{chal.name}] - {await chal.status()}"
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
            await self.chal_help(ctx)

    @commands.bot_has_permissions(manage_channels=True)
    @chal.command("invite")
    async def invite_chal(self, ctx, user):
        user = await parse_user(ctx.channel.guild, user)
        await respond(ctx, chk_fetch_chal(ctx).invite, ctx.author, user)

    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @commands.command("done")
    async def done_alias(self, ctx, *withlist):
        await self.done(ctx, *withlist)

    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @chal.command()
    async def done(self, ctx, *withlist):
        guild = ctx.channel.guild
        users = [await parse_user(guild, u) for u in withlist]
        users = list(set(users))  # remove dups
        await respond(ctx, chk_fetch_chal(ctx).done, ctx.author, users)

    @chal.command("help")
    async def chal_help(self, ctx):
        help = """
These commands are callable from a CTF **challenge** environment.

`!chal done [<users>]`
Marks this challenge as completed, and moves channel to "done" category. You may optionally include @'s of `users` that worked with you.
Once a challenge is completed, **no one** except you (and admins) can alter the done list or change reset the status to "undone".

`!chal invite <user>`
Invites a `user` to a challenge channel.

`!chal undone`
Marks this challenge as **not** completed. This will move the channel back to the "working" category.
""".replace("!", config["prefix"])
        await eptbot.embed_help(ctx, "Challenge help topic", help)

    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @chal.command()
    async def undone(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).undone)

    @commands.bot_has_permissions(manage_channels=True)
    @chal.command("leave")
    async def leave_chal(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).leave, ctx.author)


async def respond(ctx, callback, *args):
    messages = []
    guild = ctx.channel.guild
    async with ctx.channel.typing():
        for chan_id, msg in await callback(*args):
            chan = guild.get_channel(chan_id) if chan_id else ctx.channel
            msg = await chan.send(msg)
            messages.append(msg)
    return messages


async def respond_with_reaction(ctx, emoji, callback, *args):
    messages = []
    guild = ctx.channel.guild
    async with ctx.channel.typing():
        for chan_id, msg in await callback(*args):
            chan = guild.get_channel(chan_id) if chan_id else ctx.channel
            msg = await chan.send(msg)
            await msg.add_reaction(emoji)
            messages.append(msg)
    return messages


def check_name(name):
    if len(name) > 32:
        raise ctf_model.TaskFailed("Challenge name is too long!")

    if not re.match(r"[-._!0-9A-Za-z æøåÆØÅ]+$", name):
        raise ctf_model.TaskFailed("Challenge contains invalid characters!")

    # Replace spaces with a dash, because discord does it :/
    return re.sub(r" +", "-", name).lower()


def chk_fetch_team_by_name(ctx, name):
    channels = ctx.guild.channels
    if len([channel.id for channel in channels if name == channel.name]) > 1:
        raise ctf_model.TaskFailed("Multiple channels with same name exists")

    found_channel_id = ""
    for channel in channels:
        if channel.name == name:
            found_channel_id = channel.id
    team = ctf_model.CtfTeam.fetch(ctx.channel.guild, found_channel_id)
    if not team:
        raise ctf_model.TaskFailed("Failed to join CTF")
    return team


def chk_fetch_team(ctx):
    team = ctf_model.CtfTeam.fetch(ctx.channel.guild, ctx.channel.id)
    if not team:
        raise ctf_model.TaskFailed("Please type this command in a ctf channel.")
    return team


def chk_fetch_chal(ctx):
    chal = ctf_model.Challenge.fetch(ctx.channel.guild, ctx.channel.id)
    if not chal:
        raise ctf_model.TaskFailed("Please type this command in a challenge channel. You may need to join a challenge first.")
    return chal


async def parse_user(guild, user):
    print('parsinig user:', repr(user))  # XXX: Debug
    mat = re.match(r"<@!{0,1}([0-9]+)>$", user)
    ret = None
    if mat:
        ret = await guild.fetch_member(int(mat[1]))

    if not ret:
        raise ctf_model.TaskFailed(f'Invalid username: `{user}`, use @username')
    return ret


def setup(bot):
    bot.add_cog(Ctfs(bot))
